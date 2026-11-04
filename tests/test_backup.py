"""Encrypted portable backup/restore tests using synthetic records only."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from therapybot.backup import (
    HEADER_LEN, MAGIC, BackupError, create_backup, restore_backup,
)
from therapybot.vault import LockedError, Vault


PASSPHRASE = "synthetic long test passphrase"
CANARY = "SYNTHETIC_PRIVATE_BACKUP_CANARY_7935"


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.original = self.root / "original.sqlite3"
        self.vault = Vault(self.original)
        self.vault.unlock(PASSPHRASE)
        self.record_id = self.vault.add("journal", {"text": CANARY, "mood": 7})
        self.vault.add("chat", {"role": "user", "text": "synthetic dialogue only"})

    def tearDown(self):
        self.vault.lock()
        self.temp.cleanup()

    def test_encrypted_backup_round_trip_new_destination(self):
        backup = create_backup(self.vault)
        self.assertTrue(backup.startswith(MAGIC))
        self.assertNotIn(CANARY.encode(), backup)
        self.assertNotIn(b"SQLite format 3", backup)
        destination = self.root / "recovered.sqlite3"
        self.assertEqual(restore_backup(backup, PASSPHRASE, destination), destination)
        self.assertTrue(self.original.is_file(), "Original vault must remain intact")
        recovered = Vault(destination)
        recovered.unlock(PASSPHRASE)
        records = recovered.list()
        self.assertEqual(len(records), 2)
        record_by_id = {record["id"]: record for record in records}
        self.assertEqual(record_by_id[self.record_id]["data"]["text"], CANARY)
        self.assertNotIn(CANARY.encode(), destination.read_bytes(), "Restored vault contents must remain encrypted")
        recovered.lock()
        if os.name != "nt":
            self.assertEqual(destination.stat().st_mode & 0o777, 0o600)

    def test_backup_requires_unlocked_vault(self):
        self.vault.lock()
        with self.assertRaises(LockedError):
            create_backup(self.vault)

    def test_wrong_passphrase_cannot_create_output(self):
        backup = create_backup(self.vault)
        output = self.root / "wrong-passphrase.sqlite3"
        with self.assertRaises(BackupError):
            restore_backup(backup, "incorrect long passphrase", output)
        self.assertFalse(output.exists())

    def test_authentication_rejects_modified_header_and_ciphertext(self):
        good = create_backup(self.vault)
        for label, index in (("salt", len(MAGIC) + 2), ("nonce", HEADER_LEN - 1),
                             ("ciphertext", HEADER_LEN + 5), ("tag", len(good) - 1)):
            with self.subTest(label=label):
                tampered = bytearray(good)
                tampered[index] ^= 1
                output = self.root / f"bad-{label}.sqlite3"
                with self.assertRaises(BackupError):
                    restore_backup(bytes(tampered), PASSPHRASE, output)
                self.assertFalse(output.exists())

    def test_truncated_unknown_version_and_oversized_rejected(self):
        good = create_backup(self.vault)
        candidates = (good[:8], good[:-20], b"garbage" + good,
                      good[:len(MAGIC)] + b"\x07" + good[len(MAGIC)+1:])
        for index, candidate in enumerate(candidates):
            with self.subTest(index=index):
                output = self.root / f"invalid-{index}.sqlite3"
                with self.assertRaises(BackupError):
                    restore_backup(candidate, PASSPHRASE, output)
                self.assertFalse(output.exists())
        with patch("therapybot.backup.MAX_BACKUP", len(good) - 1):
            with self.assertRaises(BackupError):
                restore_backup(good, PASSPHRASE, self.root / "oversized.sqlite3")

    def test_existing_destination_never_overwritten(self):
        backup = create_backup(self.vault)
        output = self.root / "already-here.sqlite3"
        output.write_bytes(b"DO-NOT-OVERWRITE")
        with self.assertRaises(BackupError):
            restore_backup(backup, PASSPHRASE, output)
        self.assertEqual(output.read_bytes(), b"DO-NOT-OVERWRITE")

    @unittest.skipUnless(hasattr(os, "symlink"), "Symbolic links unavailable")
    def test_symlink_destination_rejected(self):
        backup = create_backup(self.vault)
        target = self.root / "target.sqlite3"
        target.write_bytes(b"UNTOUCHED")
        alias = self.root / "alias.sqlite3"
        try:
            alias.symlink_to(target)
        except OSError as exc:
            self.skipTest(f"OS does not permit creating a test symlink: {exc}")
        with self.assertRaises(BackupError):
            restore_backup(backup, PASSPHRASE, alias)
        self.assertEqual(target.read_bytes(), b"UNTOUCHED")

    def test_unexpected_trigger_is_rejected(self):
        with self.vault._connect() as db:
            db.execute("CREATE TRIGGER synthetic_trigger AFTER INSERT ON records BEGIN SELECT 1; END")
        backup = create_backup(self.vault)
        output = self.root / "trigger.sqlite3"
        with self.assertRaises(BackupError):
            restore_backup(backup, PASSPHRASE, output)
        self.assertFalse(output.exists())

    def test_unexpected_check_constraint_is_rejected(self):
        # The columns and autoindexes still match, but chat inserts fail.
        with self.vault._connect() as db:
            db.execute("ALTER TABLE records RENAME TO original_records")
            db.execute("CREATE TABLE records (id TEXT PRIMARY KEY, kind TEXT NOT NULL "
                       "CHECK(kind='journal'), created REAL NOT NULL, nonce BLOB NOT NULL, "
                       "ciphertext BLOB NOT NULL)")
            db.execute("INSERT INTO records SELECT * FROM original_records WHERE kind='journal'")
            db.execute("DROP TABLE original_records")
        backup = create_backup(self.vault)
        output = self.root / "constraint.sqlite3"
        with self.assertRaises(BackupError):
            restore_backup(backup, PASSPHRASE, output)
        self.assertFalse(output.exists())

    @unittest.skipIf(os.name == "nt", "POSIX mode enforcement")
    def test_shared_writable_restore_directory_rejected(self):
        backup = create_backup(self.vault)
        shared = self.root / "shared"
        shared.mkdir(mode=0o777)
        shared.chmod(0o777)
        with self.assertRaises(BackupError):
            restore_backup(backup, PASSPHRASE, shared / "unsafe.sqlite3")

    def test_corrupt_encrypted_record_is_rejected(self):
        with self.vault._connect() as db:
            db.execute("UPDATE records SET ciphertext=? WHERE id=?", (b"invalid-tag", self.record_id))
        backup = create_backup(self.vault)
        output = self.root / "corrupt.sqlite3"
        with self.assertRaises(BackupError):
            restore_backup(backup, PASSPHRASE, output)
        self.assertFalse(output.exists())

    def test_failed_write_only_removes_newly_created_destination(self):
        backup = create_backup(self.vault)
        output = self.root / "write-failure.sqlite3"
        with patch("therapybot.backup.os.fsync", side_effect=OSError("synthetic disk failure")):
            with self.assertRaises(BackupError):
                restore_backup(backup, PASSPHRASE, output)
        self.assertFalse(output.exists())
        self.assertTrue(self.original.exists())

    def test_interrupted_restore_cleans_partial_destination(self):
        backup = create_backup(self.vault)
        output = self.root / "interrupted.sqlite3"
        with patch("therapybot.backup.os.fsync", side_effect=KeyboardInterrupt()):
            with self.assertRaises(KeyboardInterrupt):
                restore_backup(backup, PASSPHRASE, output)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
