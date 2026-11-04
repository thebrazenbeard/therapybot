"""Portable, authenticated backups for the existing encrypted-record vault.

Only the final .tbbak envelope leaves memory during backup. Restore validates
in memory and creates a *new* vault path; it never replaces a live database.
Requires SQLite serialize/deserialize support (usually Python 3.11+).
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import secrets
import sqlite3
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from .vault import Vault

MAGIC = b"THERAPYBOT-VAULT-BACKUP\x00"
VERSION = 1
KDF_ID = 1  # scrypt n=16384, r=8, p=1, dklen=32
SALT_LEN = 16
NONCE_LEN = 12
TAG_LEN = 16
MAX_SNAPSHOT = 64 * 1024 * 1024
HEADER_LEN = len(MAGIC) + 2 + SALT_LEN + NONCE_LEN
MAX_BACKUP = HEADER_LEN + MAX_SNAPSHOT + TAG_LEN
_BACKUP_INFO = b"therapybot/backup/v1"


class BackupError(ValueError):
    """Invalid backup or a safely rejected backup/restore operation."""


def _backup_key(vault_key: bytes, salt: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=salt, info=_BACKUP_INFO).derive(vault_key)


def _serialize_snapshot(vault: Vault) -> tuple[bytes, bytes, bytes]:
    """Return (database bytes, original salt, unlocked key) under vault mutex."""
    if not hasattr(sqlite3.Connection, "serialize"):
        raise BackupError("This Python/SQLite build does not support in-memory SQLite serialization.")
    with vault._mutex:
        key = vault._require_key()
        if vault.path.stat().st_size > MAX_SNAPSHOT:
            raise BackupError("Vault exceeds the 64 MiB backup limit.")
        with vault._connect() as source:
            snapshot_db = sqlite3.connect(":memory:")
            try:
                source.backup(snapshot_db)
                # Read the salt from the same snapshot we are encrypting. An
                # independent process might otherwise change source metadata
                # between separate queries and the online backup operation.
                salt_row = snapshot_db.execute("SELECT value FROM meta WHERE name='salt'").fetchone()
                if not salt_row or not isinstance(salt_row[0], bytes) or len(salt_row[0]) != SALT_LEN:
                    raise BackupError("Vault encryption metadata is invalid.")
                salt = salt_row[0]
                snapshot = snapshot_db.serialize()
            except (sqlite3.Error, AttributeError) as exc:
                raise BackupError("Could not create a consistent vault snapshot.") from exc
            finally:
                snapshot_db.close()
        if not 0 < len(snapshot) <= MAX_SNAPSHOT:
            raise BackupError("Vault snapshot exceeds the 64 MiB backup limit.")
        return snapshot, salt, key


def create_backup(vault: Vault) -> bytes:
    """Produce a versioned, authenticated, encrypted snapshot without disk temp files."""
    if not isinstance(vault, Vault):
        raise TypeError("Expected a TherapyBot Vault.")
    with vault._mutex:
        snapshot, salt, key = _serialize_snapshot(vault)
        nonce = secrets.token_bytes(NONCE_LEN)
        header = MAGIC + bytes((VERSION, KDF_ID)) + salt + nonce
        return header + AESGCM(_backup_key(key, salt)).encrypt(nonce, snapshot, header)


def _decrypt_envelope(data: bytes, passphrase: str) -> tuple[bytes, bytes, bytes]:
    if not isinstance(data, bytes) or not HEADER_LEN + TAG_LEN < len(data) <= MAX_BACKUP:
        raise BackupError("Invalid or oversized TherapyBot backup.")
    if not isinstance(passphrase, str) or len(passphrase) < 12:
        raise BackupError("A vault passphrase of at least 12 characters is required.")
    if data[: len(MAGIC)] != MAGIC or data[len(MAGIC): len(MAGIC) + 2] != bytes((VERSION, KDF_ID)):
        raise BackupError("Unknown or invalid TherapyBot backup format.")
    salt_start = len(MAGIC) + 2
    salt = data[salt_start: salt_start + SALT_LEN]
    nonce = data[salt_start + SALT_LEN: HEADER_LEN]
    header = data[:HEADER_LEN]
    try:
        vault_key = hashlib.scrypt(passphrase.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32)
        snapshot = AESGCM(_backup_key(vault_key, salt)).decrypt(nonce, data[HEADER_LEN:], header)
    except (InvalidTag, ValueError, OverflowError) as exc:
        # Do not distinguish a wrong passphrase from tampering.
        raise BackupError("Backup authentication failed (wrong passphrase or modified file).") from exc
    if not 0 < len(snapshot) <= MAX_SNAPSHOT:
        raise BackupError("Invalid backup snapshot size.")
    return snapshot, vault_key, salt


def _validate_sqlite(snapshot: bytes, vault_key: bytes, envelope_salt: bytes) -> None:
    """Reject invalid schema, malicious triggers, corrupt rows or wrong KDF metadata."""
    if not hasattr(sqlite3.Connection, "deserialize"):
        raise BackupError("This Python/SQLite build does not support in-memory SQLite deserialization.")
    db = sqlite3.connect(":memory:")
    try:
        try:
            db.deserialize(snapshot)
            integrity = db.execute("PRAGMA integrity_check").fetchone()
            if integrity != ("ok",):
                raise BackupError("Backup SQLite integrity check failed.")
            objects = {(row[0], row[1], row[2], row[3]) for row in db.execute(
                "SELECT type,name,tbl_name,sql FROM sqlite_master"
            )}
            expected_indexes = {
                ("index", "sqlite_autoindex_meta_1", "meta", None),
                ("index", "sqlite_autoindex_records_1", "records", None),
            }
            # Table SQL uses harmless formatting differences across creation
            # paths; exact column/schema inspection follows below.
            table_objects = {(typ, name) for typ, name, _, _ in objects if typ == "table"}
            other_objects = {(typ, name, tbl, sql) for typ, name, tbl, sql in objects if typ != "table"}
            if (table_objects != {("table", "meta"), ("table", "records")}
                    or other_objects != expected_indexes):
                raise BackupError("Backup contains an unexpected database object or schema.")
            # PRAGMA table_info does not expose CHECK, UNIQUE or FK clauses.
            # Require the current exact schema (ignoring harmless whitespace)
            # to avoid restoring a subtly incompatible authenticated database.
            expected_ddl = {
                "meta": "CREATE TABLE meta (name TEXT PRIMARY KEY, value BLOB NOT NULL)",
                "records": "CREATE TABLE records (id TEXT PRIMARY KEY, kind TEXT NOT NULL, "
                           "created REAL NOT NULL, nonce BLOB NOT NULL, ciphertext BLOB NOT NULL)",
            }
            for name, expected_sql in expected_ddl.items():
                actual_sql = next((sql for typ, obj, _, sql in objects
                                   if typ == "table" and obj == name), None)
                if (not isinstance(actual_sql, str)
                        or "".join(actual_sql.split()).casefold() != "".join(expected_sql.split()).casefold()):
                    raise BackupError("Backup schema definition is not compatible with this version.")
            expected_columns = {
                "meta": [("name", "TEXT", 0, 1), ("value", "BLOB", 1, 0)],
                "records": [("id", "TEXT", 0, 1), ("kind", "TEXT", 1, 0),
                            ("created", "REAL", 1, 0), ("nonce", "BLOB", 1, 0),
                            ("ciphertext", "BLOB", 1, 0)],
            }
            for table, expected in expected_columns.items():
                actual = [(col[1], col[2].upper(), col[3], col[5])
                          for col in db.execute(f"PRAGMA table_info({table})")]
                if actual != expected:
                    raise BackupError("Backup schema columns do not match TherapyBot.")
            metadata = dict(db.execute("SELECT name,value FROM meta"))
            if (set(metadata) != {"salt", "check"} or not isinstance(metadata["salt"], bytes)
                    or len(metadata["salt"]) != SALT_LEN or metadata["salt"] != envelope_salt):
                raise BackupError("Backup vault metadata is invalid.")
            check = metadata["check"]
            if not isinstance(check, bytes) or len(check) < NONCE_LEN + TAG_LEN:
                raise BackupError("Backup vault metadata is invalid.")
            try:
                sentinel = AESGCM(vault_key).decrypt(check[:NONCE_LEN], check[NONCE_LEN:], b"vault-check")
            except InvalidTag as exc:
                raise BackupError("Backup vault passphrase verification failed.") from exc
            if sentinel != b"therapybot-vault-v1":
                raise BackupError("Backup vault format is not recognized.")
            row_count = db.execute("SELECT COUNT(*) FROM records").fetchone()[0]
            if row_count > 100_000:
                raise BackupError("Backup contains too many records.")
            for record_id, kind, created, nonce, ciphertext in db.execute(
                "SELECT id,kind,created,nonce,ciphertext FROM records"
            ):
                if (not isinstance(record_id, str) or not re.fullmatch(r"[0-9a-f]{32}", record_id)
                        or kind not in {"chat", "journal"}
                        or isinstance(created, bool) or not isinstance(created, (int, float))
                        or not math.isfinite(created)
                        or not isinstance(nonce, bytes) or len(nonce) != NONCE_LEN
                        or not isinstance(ciphertext, bytes) or len(ciphertext) < TAG_LEN):
                    raise BackupError("Backup contains an invalid record.")
                try:
                    record = json.loads(AESGCM(vault_key).decrypt(
                        nonce, ciphertext, (record_id + ":" + kind).encode()
                    ))
                except (InvalidTag, ValueError, UnicodeError) as exc:
                    raise BackupError("Backup contains an unauthenticated or invalid record.") from exc
                if not isinstance(record, dict):
                    raise BackupError("Backup record payload is not an object.")
        except sqlite3.Error as exc:
            raise BackupError("Invalid or corrupted SQLite backup data.") from exc
    finally:
        db.close()


def restore_backup(data: bytes, passphrase: str, output_path: str | Path) -> Path:
    """Restore a backup into a NEW file only; never replace an active vault.

    No private contents are written to intermediate plaintext files. The new
    database itself uses TherapyBot's existing encrypted-record schema.
    """
    snapshot, key, salt = _decrypt_envelope(data, passphrase)
    _validate_sqlite(snapshot, key, salt)
    path = Path(output_path).expanduser()
    if path.exists() or path.is_symlink():
        raise BackupError("Restore destination already exists; it will not be overwritten.")
    if not path.parent.is_dir():
        raise BackupError("Restore destination directory does not exist.")
    # Another principal must not be able to swap the output path during
    # post-write verification. On POSIX reject group/other-writable parents.
    # Windows callers must choose a private folder with restrictive ACLs.
    if os.name != "nt" and path.parent.stat().st_mode & 0o022:
        raise BackupError("Restore destination directory must not be group/other writable.")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    created = False
    try:
        try:
            fd = os.open(path, flags, 0o600)
        except FileExistsError as exc:
            raise BackupError("Restore destination already exists; it will not be overwritten.") from exc
        created = True
        with os.fdopen(fd, "wb") as stream:
            stream.write(snapshot)
            stream.flush()
            os.fsync(stream.fileno())
        # Verify bytes as written, using the ordinary vault loader.
        restored = Vault(path)
        restored.unlock(passphrase)
        restored.list()
        restored.lock()
        return path
    except BaseException as exc:
        if created:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                pass
        if not isinstance(exc, Exception):
            raise  # Propagate interrupt/exit after removing the new partial file.
        if isinstance(exc, BackupError):
            raise
        raise BackupError("Could not safely create or verify restored vault.") from exc
