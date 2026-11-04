"""Fail-closed runtime asset build checks, independent of host node_modules."""
import json
import tempfile
import unittest
from pathlib import Path

from build_preview import WLLAMA_ASSETS, build, pinned_assets


class PinnedRuntimeTests(unittest.TestCase):
    def fake_modules(self, root: Path, version: str = "3.8.1"):
        for package in ("wllama", "wllama-compat"):
            directory = root / "@wllama" / package
            directory.mkdir(parents=True, exist_ok=True)
            (directory / "package.json").write_text(
                json.dumps({"name": "@wllama/" + package, "version": version}), encoding="utf-8"
            )
        for asset in WLLAMA_ASSETS:
            path = root.joinpath(*asset.split("/"))
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"tampered-by-test")

    def test_version_mismatch_rejected_without_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            modules = root / "node_modules"
            self.fake_modules(modules, version="3.8.2")
            target = root / "output"
            with self.assertRaises(ValueError):
                build(target, modules)
            self.assertFalse(target.exists())

    def test_hash_mismatch_rejected_without_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            modules = root / "node_modules"
            self.fake_modules(modules)
            with self.assertRaises(ValueError):
                pinned_assets(modules)
            target = root / "output"
            with self.assertRaises(ValueError):
                build(target, modules)
            self.assertFalse(target.exists())

    def test_no_weight_asset_in_allowlist(self):
        self.assertEqual(len(WLLAMA_ASSETS), 5)
        self.assertIn('@wllama/wllama/LICENCE', WLLAMA_ASSETS)
        self.assertFalse(any(".gguf" in key or ".gguf" in dest for key, (dest, _) in WLLAMA_ASSETS.items()))


if __name__ == "__main__":
    unittest.main()
