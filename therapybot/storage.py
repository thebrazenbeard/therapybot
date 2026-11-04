"""Consent-controlled, passphrase-encrypted SQLite records.

Only opaque ciphertext, record type, and a timestamp are stored. The key is
held in process memory while the vault is unlocked, never written to disk.
"""

import base64
import json
import os
import sqlite3
import threading
from pathlib import Path

from cryptography.exceptions import InvalidKey
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


class VaultError(ValueError):
    pass


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
        import tempfile
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

    def close(self):
        with self._lock:
            self._key = None
            self.db.close()
