"""Synthetic authenticated backup/restore tests for the existing Fernet vault."""

import os
import stat
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from therapybot.storage import Vault, VaultError


PASSPHRASE = "synthetic-backup-passphrase-0042"
CANARY = "SYNTHETIC_PRIVATE_BACKUP_CANARY"


class AuthenticatedBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.source = self.folder / "original.sqlite3"
        self.vault = Vault(self.source)
        self.addCleanup(self.vault.close)
        self.vault.unlock(PASSPHRASE)
        self.vault.add("chat", {"user": CANARY, "assistant": "test answer"})
        self.vault.add("journal", {"text": "offline notes"}, mood=4)
        self.vault.add("profile", {"style": "direct"})
        self.vault.add("safety_plan", {"contact": "synthetic"})

    def test_authenticated_round_trip_preserves_all_record_types_and_original(self):
        original = self.vault.list()
        archive = self.vault.export_authenticated_backup(PASSPHRASE)
        self.assertNotIn(CANARY.encode(), archive)
        destination = self.folder / "restored.sqlite3"
        restored_path = Vault.restore_authenticated_backup(archive, destination, PASSPHRASE)
        self.assertEqual(destination.resolve(), restored_path)
        other = Vault(destination)
        try:
            with self.assertRaises(VaultError):
                other.unlock("wrong-passphrase")
            other.unlock(PASSPHRASE)
            self.assertEqual(original, other.list())
            self.assertEqual(4, len(other.list()))
        finally:
            other.close()
        self.assertEqual(original, self.vault.list())

    def test_wrong_passphrases_leave_no_destination(self):
        with self.assertRaises(VaultError):
            self.vault.export_authenticated_backup("wrong-passphrase")
        archive = self.vault.export_authenticated_backup(PASSPHRASE)
        destination = self.folder / "missing-on-wrong-key.sqlite3"
        with self.assertRaises(VaultError):
            Vault.restore_authenticated_backup(archive, destination, "wrong-passphrase")
        self.assertFalse(destination.exists())

    def test_tamper_is_rejected_without_creating_destination(self):
        archive = self.vault.export_authenticated_backup(PASSPHRASE)
        tampered = bytearray(archive)
        tampered[-22] ^= 1
        destination = self.folder / "missing-on-tamper.sqlite3"
        with self.assertRaises(VaultError):
            Vault.restore_authenticated_backup(bytes(tampered), destination, PASSPHRASE)
        self.assertFalse(destination.exists())
        with self.assertRaises(VaultError):
            Vault.restore_authenticated_backup(b"not-a-therapybot-archive", destination, PASSPHRASE)
        self.assertFalse(destination.exists())

    def test_existing_destination_never_overwritten(self):
        archive = self.vault.export_authenticated_backup(PASSPHRASE)
        destination = self.folder / "existing.sqlite3"
        destination.write_bytes(b"DO_NOT_OVERWRITE")
        with self.assertRaises(VaultError):
            Vault.restore_authenticated_backup(archive, destination, PASSPHRASE)
        self.assertEqual(b"DO_NOT_OVERWRITE", destination.read_bytes())

    def test_rejects_ciphertext_corrupted_inside_authenticated_source(self):
        # A correctly encrypted archive may nevertheless contain a broken
        # original vault. Restoration must authenticate every saved row.
        with self.vault.db:
            self.vault.db.execute("UPDATE records SET encrypted=? WHERE id=1", (b"broken-inner-ciphertext",))
        archive = self.vault.export_authenticated_backup(PASSPHRASE)
        destination = self.folder / "would-be-invalid.sqlite3"
        with self.assertRaises(VaultError):
            Vault.restore_authenticated_backup(archive, destination, PASSPHRASE)
        self.assertFalse(destination.exists())

    def test_rejects_unexpected_sqlite_trigger_before_creating_destination(self):
        # Triggers embedded inside an otherwise authenticated SQLite archive
        # must not be installed into the user's live application.
        with self.vault.db:
            self.vault.db.execute(
                "CREATE TRIGGER unexpected AFTER INSERT ON records "
                "BEGIN DELETE FROM records; END"
            )
        archive = self.vault.export_authenticated_backup(PASSPHRASE)
        destination = self.folder / "would-be-trigger.sqlite3"
        with self.assertRaises(VaultError):
            Vault.restore_authenticated_backup(archive, destination, PASSPHRASE)
        self.assertFalse(destination.exists())

    @unittest.skipIf(os.name == "nt", "POSIX permissions check")
    def test_rejects_group_writable_parent(self):
        archive = self.vault.export_authenticated_backup(PASSPHRASE)
        unsafe = self.folder / "group-writable"
        unsafe.mkdir(mode=0o700)
        unsafe.chmod(0o770)
        destination = unsafe / "restored.sqlite3"
        with self.assertRaises(VaultError):
            Vault.restore_authenticated_backup(archive, destination, PASSPHRASE)
        self.assertFalse(destination.exists())

    @unittest.skipIf(os.name == "nt", "POSIX symlink check")
    def test_rejects_symlinked_parent(self):
        archive = self.vault.export_authenticated_backup(PASSPHRASE)
        actual = self.folder / "actual"
        actual.mkdir(mode=0o700)
        alias = self.folder / "parent-link"
        alias.symlink_to(actual, target_is_directory=True)
        destination = alias / "new-vault.sqlite3"
        with self.assertRaises(VaultError):
            Vault.restore_authenticated_backup(archive, destination, PASSPHRASE)
        self.assertFalse((actual / "new-vault.sqlite3").exists())

    def test_partial_destination_cleaned_on_write_failure(self):
        archive = self.vault.export_authenticated_backup(PASSPHRASE)
        destination = self.folder / "write-failure.sqlite3"
        with mock.patch("therapybot.storage.os.fsync", side_effect=OSError("synthetic disk fault")):
            with self.assertRaises(VaultError):
                Vault.restore_authenticated_backup(archive, destination, PASSPHRASE)
        self.assertFalse(destination.exists())

    @unittest.skipIf(os.name == "nt", "Replacing open files differs on Windows")
    def test_cleanup_does_not_unlink_a_swapped_destination(self):
        archive = self.vault.export_authenticated_backup(PASSPHRASE)
        destination = self.folder / "swap-attempt.sqlite3"
        moved = self.folder / "original-inode.sqlite3"

        def simulate_same_user_path_swap(_):
            destination.rename(moved)
            destination.write_bytes(b"SYNTHETIC_FOREIGN_FILE")
            raise OSError("synthetic fault after pathname replacement")

        with mock.patch("therapybot.storage.os.fsync", side_effect=simulate_same_user_path_swap):
            with self.assertRaises(VaultError):
                Vault.restore_authenticated_backup(archive, destination, PASSPHRASE)
        self.assertEqual(b"SYNTHETIC_FOREIGN_FILE", destination.read_bytes())
        self.assertTrue(moved.exists())

    @unittest.skipIf(os.name == "nt", "POSIX mode check")
    def test_restricts_restored_file_mode(self):
        archive = self.vault.export_authenticated_backup(PASSPHRASE)
        destination = self.folder / "mode-checked.sqlite3"
        Vault.restore_authenticated_backup(archive, destination, PASSPHRASE)
        self.assertEqual(0o600, stat.S_IMODE(destination.stat().st_mode))


if __name__ == "__main__":
    unittest.main()
