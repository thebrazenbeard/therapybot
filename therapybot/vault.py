"""Encrypted records. SQLite indexes only opaque IDs, kind and timestamps.

The passphrase stays in process memory while unlocked. This is not whole-disk
encryption or protection against a compromised operating system.
"""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import sqlite3
import threading
import time
import uuid
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class LockedError(RuntimeError):
    pass


class WrongPassphrase(ValueError):
    pass


class Vault:
    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser().resolve()
        self._key: bytes | None = None
        self._mutex = threading.RLock()
        was_present = self.path.parent.exists()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if os.name != "nt" and not was_present:
            os.chmod(self.path.parent, 0o700)
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS meta (name TEXT PRIMARY KEY, value BLOB NOT NULL)")
            db.execute("""CREATE TABLE IF NOT EXISTS records (
                id TEXT PRIMARY KEY, kind TEXT NOT NULL, created REAL NOT NULL,
                nonce BLOB NOT NULL, ciphertext BLOB NOT NULL)""")
        if os.name != "nt":
            os.chmod(self.path, 0o600)

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.execute("PRAGMA secure_delete = ON")
        db.execute("PRAGMA journal_mode = DELETE")
        return db

    @property
    def unlocked(self) -> bool:
        return self._key is not None

    def unlock(self, passphrase: str) -> None:
        if not isinstance(passphrase, str) or len(passphrase) < 12:
            raise ValueError("Use a passphrase of at least 12 characters.")
        with self._mutex, self._connect() as db:
            existing = dict(db.execute("SELECT name, value FROM meta"))
            salt = existing.get("salt", os.urandom(16))
            key = hashlib.scrypt(passphrase.encode("utf-8"), salt=salt, n=2**14, r=8, p=1, dklen=32)
            if "check" in existing:
                try:
                    payload = existing["check"]
                    plaintext = AESGCM(key).decrypt(payload[:12], payload[12:], b"vault-check")
                    if plaintext != b"therapybot-vault-v1":
                        raise WrongPassphrase("Incorrect vault passphrase.")
                except (InvalidTag, ValueError) as exc:
                    raise WrongPassphrase("Incorrect vault passphrase.") from exc
            else:
                nonce = secrets.token_bytes(12)
                check = nonce + AESGCM(key).encrypt(nonce, b"therapybot-vault-v1", b"vault-check")
                db.execute("INSERT INTO meta(name,value) VALUES('salt',?)", (salt,))
                db.execute("INSERT INTO meta(name,value) VALUES('check',?)", (check,))
            self._key = key

    def lock(self) -> None:
        with self._mutex:
            self._key = None

    def _require_key(self) -> bytes:
        if self._key is None:
            raise LockedError("Unlock the local vault first.")
        return self._key

    def add(self, kind: str, data: dict) -> str:
        if kind not in {"chat", "journal"} or not isinstance(data, dict):
            raise ValueError("Invalid record type or data.")
        with self._mutex:
            key = self._require_key()
            record_id = uuid.uuid4().hex
            nonce = secrets.token_bytes(12)
            payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
            cipher = AESGCM(key).encrypt(nonce, payload, (record_id + ":" + kind).encode())
            with self._connect() as db:
                db.execute("INSERT INTO records VALUES(?,?,?,?,?)", (record_id, kind, time.time(), nonce, cipher))
            return record_id

    def list(self, kind: str | None = None, query: str | None = None) -> list[dict]:
        if kind is not None and kind not in {"chat", "journal"}:
            raise ValueError("Invalid record type.")
        with self._mutex:
            key = self._require_key()
            with self._connect() as db:
                if kind:
                    rows = db.execute("SELECT id,kind,created,nonce,ciphertext FROM records WHERE kind=? ORDER BY created,id", (kind,)).fetchall()
                else:
                    rows = db.execute("SELECT id,kind,created,nonce,ciphertext FROM records ORDER BY created,id").fetchall()
            results = []
            for record_id, record_kind, created, nonce, cipher in rows:
                data = json.loads(AESGCM(key).decrypt(nonce, cipher, (record_id + ":" + record_kind).encode()))
                if query and query.casefold() not in json.dumps(data, ensure_ascii=False).casefold():
                    continue
                results.append({"id": record_id, "kind": record_kind, "created": created, "data": data})
            return results

    def delete(self, record_id: str) -> bool:
        with self._mutex:
            self._require_key()
            with self._connect() as db:
                result = db.execute("DELETE FROM records WHERE id=?", (record_id,))
                return result.rowcount == 1

    def export(self) -> list[dict]:
        return self.list()
