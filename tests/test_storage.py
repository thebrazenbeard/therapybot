"""Synthetic encrypted-vault integration tests; no personal content."""

import os
import stat
import tempfile
import unittest
from pathlib import Path

from therapybot.storage import Vault, VaultError


class VaultTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.path = self.folder / "vault.sqlite3"
        self.vault = Vault(self.path)
        self.addCleanup(self.vault.close)

    def test_opt_in_encryption_and_restart(self):
        self.assertFalse(self.vault.initialized)
        self.assertEqual([], self.vault.search("CANARY") if self.vault.unlocked else [])
        with self.assertRaises(VaultError):
            self.vault.add("chat", "SYNTHETIC_CANARY_0042")
        self.vault.unlock("synthetic-passphrase-0001")
        self.vault.add("chat", {"user": "SYNTHETIC_CANARY_0042", "assistant": "example reply"})
        self.assertEqual(1, len(self.vault.search("SYNTHETIC_CANARY_0042")))
        data = self.path.read_bytes()
        self.assertNotIn(b"SYNTHETIC_CANARY_0042", data)
        self.assertNotIn(b"SYNTHETIC_CANARY_0042", self.vault.backup())
        self.vault.lock()
        with self.assertRaises(VaultError):
            self.vault.list("chat")
        with self.assertRaises(VaultError):
            self.vault.unlock("wrong-passphrase-0002")
        self.vault.unlock("synthetic-passphrase-0001")
        self.assertEqual(1, len(self.vault.list("chat")))
        # Closing and reopening a new connection must recover only with the key.
        self.vault.close()
        restored = Vault(self.path)
        try:
            with self.assertRaises(VaultError):
                restored.list("chat")
            restored.unlock("synthetic-passphrase-0001")
            self.assertEqual(1, len(restored.search("SYNTHETIC_CANARY_0042")))
        finally:
            restored.close()

    def test_delete_records_not_encryption_settings(self):
        self.vault.unlock("synthetic-passphrase-0001")
        self.vault.add("journal", "SYNTHETIC_ENTRY_91", mood=7)
        self.vault.add("chat", {"user": "hello", "assistant": "reply"})
        self.assertEqual(2, self.vault.delete_all())
        self.assertEqual([], self.vault.list())
        self.assertTrue(self.vault.initialized)

    def test_existing_parent_directory_not_changed(self):
        if os.name == "nt":
            self.skipTest("Unix mode test")
        # Existing parent mode deliberately differs from Vault's 0700 creation mode.
        self.folder.chmod(0o751)
        original_mode = stat.S_IMODE(self.folder.stat().st_mode)
        self.assertEqual(0o600, stat.S_IMODE(self.path.stat().st_mode))
        self.vault.close()
        self.path.chmod(0o644)
        replacement = Vault(self.path)
        try:
            self.assertEqual(0o600, stat.S_IMODE(self.path.stat().st_mode))
            self.assertEqual(original_mode, stat.S_IMODE(self.folder.stat().st_mode))
        finally:
            replacement.close()

    def test_preexisting_directory_permissions_preserved_on_first_open(self):
        if os.name == "nt":
            self.skipTest("Unix mode test")
        parent = self.folder / "already-existing"
        parent.mkdir(mode=0o751)
        parent.chmod(0o751)
        before = stat.S_IMODE(parent.stat().st_mode)
        self.assertEqual(0o751, before)
        opened = Vault(parent / "new-vault.sqlite3")
        try:
            self.assertEqual(before, stat.S_IMODE(parent.stat().st_mode))
            self.assertEqual(0o600, stat.S_IMODE(opened.path.stat().st_mode))
        finally:
            opened.close()

    def test_refuses_short_passphrase_and_invalid_type(self):
        with self.assertRaises(VaultError):
            self.vault.unlock("short")
        self.vault.unlock("synthetic-passphrase-0001")
        with self.assertRaises(VaultError):
            self.vault.add("unknown", "text")
