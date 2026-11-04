"""Consent-controlled, passphrase-encrypted SQLite records.

Only opaque ciphertext, record type, and a timestamp are stored. The key is
held in process memory while the vault is unlocked, never written to disk.
"""

import base64
import json
import os
import sqlite3
import stat
import tempfile
import threading
from pathlib import Path

from cryptography.exceptions import InvalidKey
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


class VaultError(ValueError):
    pass


_BACKUP_MAGIC = b"TBBK-FERNET-1\x00"
# Fernet expands payloads by about 4/3; leave room below the 512 MiB cap.
_MAX_SQLITE_IMAGE_BYTES = 380 * 1024 * 1024
_MAX_ARCHIVE_BYTES = 512 * 1024 * 1024
_VALID_KINDS = frozenset(("chat", "journal", "profile", "safety_plan"))


class Vault:
    def __init__(self, path):
        self.path = Path(path).expanduser().resolve()
        new_parent = not self.path.parent.exists()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if os.name != "nt" and new_parent:
            self.path.parent.chmod(0o700)
        self._lock = threading.RLock()
        self._key = None
        self.db = sqlite3.connect(str(self.path), check_same_thread=False, timeout=10)
        self.db.execute("PRAGMA busy_timeout=10000")
        self.db.execute("CREATE TABLE IF NOT EXISTS meta (name TEXT PRIMARY KEY, value BLOB NOT NULL)")
        self.db.execute("CREATE TABLE IF NOT EXISTS records (id INTEGER PRIMARY KEY, kind TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')), encrypted BLOB NOT NULL)")
        self.db.commit()
        if os.name != "nt":
            # The explicitly selected vault file must not be group/world-readable.
            # Never change the permissions of an existing parent directory.
            self.path.chmod(0o600)

    @property
    def initialized(self):
        with self._lock:
            return self.db.execute("SELECT 1 FROM meta WHERE name='check'").fetchone() is not None

    @property
    def unlocked(self):
        return self._key is not None

    @staticmethod
    def _derive(passphrase, salt):
        if not isinstance(passphrase, str):
            raise VaultError("Passphrase required")
        raw = Scrypt(salt=salt, length=32, n=2**15, r=8, p=1).derive(passphrase.encode("utf-8"))
        return Fernet(base64.urlsafe_b64encode(raw))

    def unlock(self, passphrase):
        with self._lock:
            if not isinstance(passphrase, str) or not passphrase:
                raise VaultError("Passphrase required")
            row = self.db.execute("SELECT value FROM meta WHERE name='salt'").fetchone()
            if row is None:
                if len(passphrase) < 12:
                    raise VaultError("Use a passphrase of at least 12 characters")
                salt = os.urandom(16)
                key = self._derive(passphrase, salt)
                with self.db:
                    self.db.execute("INSERT INTO meta (name,value) VALUES ('salt',?)", (salt,))
                    self.db.execute("INSERT INTO meta (name,value) VALUES ('check',?)", (key.encrypt(b'therapybot-v1'),))
                self._key = key
                return
            key = self._derive(passphrase, row[0])
            try:
                check = self.db.execute("SELECT value FROM meta WHERE name='check'").fetchone()
                if check is None or key.decrypt(check[0]) != b"therapybot-v1":
                    raise VaultError("Wrong passphrase or damaged vault")
            except InvalidToken as exc:
                raise VaultError("Wrong passphrase or damaged vault") from exc
            self._key = key

    def lock(self):
        with self._lock:
            self._key = None

    def _require_key(self):
        if self._key is None:
            raise VaultError("Unlock your local vault first")
        return self._key

    def add(self, kind, content, mood=None):
        if kind not in ("chat", "journal", "profile", "safety_plan"):
            raise VaultError("Invalid record type")
        with self._lock:
            key = self._require_key()
            blob = key.encrypt(json.dumps({"content": content, "mood": mood}, ensure_ascii=False).encode("utf-8"))
            with self.db:
                cur = self.db.execute("INSERT INTO records(kind,encrypted) VALUES (?,?)", (kind, blob))
            return cur.lastrowid

    def list(self, kind=None, limit=500):
        with self._lock:
            key = self._require_key()
            if kind is not None and kind not in ("chat", "journal", "profile", "safety_plan"):
                raise VaultError("Invalid record type")
            if kind:
                rows = self.db.execute("SELECT id,kind,created_at,encrypted FROM records WHERE kind=? ORDER BY id DESC LIMIT ?", (kind, min(max(int(limit), 1), 1000))).fetchall()
            else:
                rows = self.db.execute("SELECT id,kind,created_at,encrypted FROM records ORDER BY id DESC LIMIT ?", (min(max(int(limit), 1), 1000),)).fetchall()
            output = []
            for rid, rkind, when, cipher in rows:
                item = json.loads(key.decrypt(cipher))
                output.append({"id": rid, "kind": rkind, "created_at": when, **item})
            return output

    def search(self, query):
        query = str(query).casefold().strip()
        if not query:
            return []
        return [r for r in self.list(limit=1000) if query in json.dumps(r.get("content"), ensure_ascii=False).casefold()][:100]

    def delete_all(self):
        with self._lock:
            self._require_key()
            with self.db:
                count = self.db.execute("SELECT COUNT(*) FROM records").fetchone()[0]
                self.db.execute("DELETE FROM records")
            # SQLite pages may retain recoverable old ciphertext; VACUUM removes it.
            self.db.execute("VACUUM")
            return count

    def backup(self):
        """Return a consistent encrypted SQLite image. No decrypted content exported."""
        with self._lock:
            self._require_key()
            with tempfile.TemporaryDirectory() as tmp:
                target = Path(tmp) / "backup.sqlite3"
                other = sqlite3.connect(str(target))
                try:
                    self.db.backup(other)
                finally:
                    other.close()
                return target.read_bytes()

    def export_authenticated_backup(self, passphrase):
        """Return a versioned, authenticated archive of this existing vault.

        The caller must have unlocked the vault and demonstrate knowledge of
        its *original* passphrase. The old raw-SQLite backup() contract is
        intentionally preserved for existing API consumers.
        """
        with self._lock:
            self._require_key()
            salt_row = self.db.execute("SELECT value FROM meta WHERE name='salt'").fetchone()
            check_row = self.db.execute("SELECT value FROM meta WHERE name='check'").fetchone()
            if salt_row is None or check_row is None:
                raise VaultError("Vault verification data is missing")
            try:
                source_key = self._derive(passphrase, salt_row[0])
                if source_key.decrypt(check_row[0]) != b"therapybot-v1":
                    raise VaultError("Wrong passphrase or damaged vault")
            except InvalidToken as exc:
                raise VaultError("Wrong passphrase or damaged vault") from exc
            snapshot = self.backup()
            if len(snapshot) > _MAX_SQLITE_IMAGE_BYTES:
                raise VaultError("Vault is too large for this backup format")
            archive_salt = os.urandom(16)
            envelope = self._derive(passphrase, archive_salt).encrypt(snapshot)
            return _BACKUP_MAGIC + archive_salt + envelope

    @staticmethod
    def _validate_restored_snapshot(snapshot, passphrase):
        """Reject malformed, foreign-schema, or row-unauthenticated images.

        Validation happens in a private temporary directory *before* opening
        or creating the caller's requested destination. The database contains
        ciphertext records, not decoded private conversation text.
        """
        with tempfile.TemporaryDirectory(prefix="therapybot-verify-") as folder:
            probe = Path(folder) / "candidate.sqlite3"
            probe.write_bytes(snapshot)
            db = sqlite3.connect(str(probe), timeout=5)
            try:
                # Treat even a passphrase-authenticated backup as untrusted
                # SQLite schema/content before issuing introspection queries.
                db.execute("PRAGMA trusted_schema=OFF")
                db.execute("PRAGMA query_only=ON")
                if db.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                    raise VaultError("Backup SQLite integrity check failed")
                objects = db.execute("SELECT type,name FROM sqlite_master").fetchall()
                if set(objects) != {
                    ("table", "meta"), ("table", "records"),
                    ("index", "sqlite_autoindex_meta_1"),
                }:
                    raise VaultError("Backup has an unexpected schema")
                meta = [
                    (row[1], row[2].upper(), row[3], row[4], row[5])
                    for row in db.execute("PRAGMA table_info(meta)")
                ]
                records = [
                    (row[1], row[2].upper(), row[3], row[4], row[5])
                    for row in db.execute("PRAGMA table_info(records)")
                ]
                if meta != [
                    ("name", "TEXT", 0, None, 1),
                    ("value", "BLOB", 1, None, 0),
                ]:
                    raise VaultError("Backup metadata schema is incompatible")
                if records != [
                    ("id", "INTEGER", 0, None, 1),
                    ("kind", "TEXT", 1, None, 0),
                    ("created_at", "TEXT", 1, "strftime('%Y-%m-%dT%H:%M:%fZ','now')", 0),
                    ("encrypted", "BLOB", 1, None, 0),
                ]:
                    raise VaultError("Backup record schema is incompatible")
                salt_row = db.execute("SELECT value FROM meta WHERE name='salt'").fetchone()
                check_row = db.execute("SELECT value FROM meta WHERE name='check'").fetchone()
                if (
                    salt_row is None or check_row is None
                    or not isinstance(salt_row[0], bytes) or len(salt_row[0]) != 16
                ):
                    raise VaultError("Backup is missing original vault verification data")
                key = Vault._derive(passphrase, salt_row[0])
                try:
                    if key.decrypt(check_row[0]) != b"therapybot-v1":
                        raise VaultError("Wrong passphrase or damaged backup")
                    for kind, encrypted in db.execute("SELECT kind,encrypted FROM records"):
                        if kind not in _VALID_KINDS:
                            raise VaultError("Backup contains an unsupported record type")
                        item = json.loads(key.decrypt(encrypted))
                        if not isinstance(item, dict) or set(item) != {"content", "mood"}:
                            raise VaultError("Backup contains an invalid record")
                except (InvalidToken, UnicodeDecodeError, TypeError, ValueError) as exc:
                    raise VaultError("Backup records failed authentication") from exc
            except sqlite3.DatabaseError as exc:
                raise VaultError("Backup is not a valid TherapyBot SQLite vault") from exc
            finally:
                db.close()

    @staticmethod
    def restore_authenticated_backup(archive, destination, passphrase):
        """Restore only into a new path; never replace or mutate a live vault.

        No destination is created until the outer envelope, original vault
        passphrase, every saved record, and the SQLite schema all validate.
        """
        if not isinstance(archive, bytes) or not archive.startswith(_BACKUP_MAGIC):
            raise VaultError("Unrecognized authenticated TherapyBot backup")
        if len(archive) > _MAX_ARCHIVE_BYTES:
            raise VaultError("Backup archive is too large")
        rest = archive[len(_BACKUP_MAGIC):]
        if len(rest) < 17:
            raise VaultError("Incomplete authenticated backup")
        archive_salt, token = rest[:16], rest[16:]
        try:
            snapshot = Vault._derive(passphrase, archive_salt).decrypt(token)
        except InvalidToken as exc:
            raise VaultError("Wrong passphrase or damaged backup") from exc
        if len(snapshot) > _MAX_SQLITE_IMAGE_BYTES:
            raise VaultError("Backup image is too large")
        Vault._validate_restored_snapshot(snapshot, passphrase)

        dest = Path(destination).expanduser().absolute()
        if os.path.lexists(str(dest)):
            raise VaultError("Destination already exists; restore only creates a new vault")
        parent = dest.parent
        if not parent.is_dir():
            raise VaultError("Destination parent directory must already exist")
        if os.name != "nt":
            if any(component.is_symlink() for component in (parent, *parent.parents)):
                raise VaultError("Choose a restore directory without symlinked ancestors")
            # Fail closed on group/world-writable parents; otherwise a local
            # actor could race a newly restored private vault's pathname.
            parent_mode = stat.S_IMODE(parent.stat().st_mode)
            if parent_mode & 0o022:
                raise VaultError("Choose a private, non-group-writable restore directory")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(str(dest), flags, 0o600)
        except FileExistsError as exc:
            raise VaultError("Destination already exists; restore refused") from exc
        except OSError as exc:
            raise VaultError("Unable to create restore destination securely") from exc
        created_identity = os.fstat(fd)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(snapshot)
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException as exc:
            try:
                current = dest.lstat()
                if (
                    created_identity.st_ino
                    and current.st_dev == created_identity.st_dev
                    and current.st_ino == created_identity.st_ino
                    and stat.S_ISREG(current.st_mode)
                ):
                    dest.unlink()
            except OSError:
                pass
            if isinstance(exc, OSError):
                raise VaultError("Restore write failed; inode-checked cleanup attempted") from exc
            raise
        if os.name != "nt" and hasattr(os, "O_DIRECTORY"):
            try:
                parent_fd = os.open(str(parent), os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(parent_fd)
                finally:
                    os.close(parent_fd)
            except OSError as exc:
                raise VaultError(
                    "Restored file exists but parent directory durability could not be verified"
                ) from exc
        return dest.resolve()

    def close(self):
        with self._lock:
            self._key = None
            self.db.close()
