"""Synthetic-only contract tests. These are NOT browser/model-inference tests."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from validate_manifest import ManifestError, load_manifest, validate_manifest, verify_local_assets


def fixture(root: Path, clearance="pending"):
    files = {
        "vendor/wllama.js": b"fake-js",
        "vendor/wllama.wasm": b"fake-wasm",
        "vendor/compat/wllama.wasm": b"compat-wasm",
        "vendor/compat/wllama.js": b"compat-js",
        "assets/demo.gguf": b"synthetic-gguf-not-a-model",
    }
    roles = ["runtime-js", "runtime-wasm", "compat-wasm", "compat-worker", "model-part"]
    for rel, data in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return {
        "schema_version": 1,
        "model": {
            "id": "synthetic/demo",
            "source_revision": "9" * 40,
            "source_url": "https://huggingface.co/example/synthetic/blob/" + "9" * 40 + "/README.md",
            "license_spdx": "Apache-2.0",
            "license_evidence_url": "https://huggingface.co/example/synthetic",
            "rights_clearance": clearance,
        },
        "runtime": {"package": "@wllama/wllama", "version": "3.8.1", "mode": "self-hosted"},
        "policy": {"offline_after_install": True, "automatic_download": False,
                   "external_runtime_fetch": False, "explicit_download_consent": True,
                   "conversation_storage_default": "none", "contains_private_data": False},
        "assets": [
            {"role": role, "path": rel, "size_bytes": len(data),
             "sha256": hashlib.sha256(data).hexdigest()}
            for (rel, data), role in zip(files.items(), roles)
        ],
    }


class AssetCustodyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.manifest = fixture(self.root)

    def test_pinned_self_hosted_structure_passes_but_pending_not_ready(self):
        out = validate_manifest(self.manifest)
        self.assertEqual(5, out["assets"])
        self.assertEqual(1, out["model_parts"])
        with self.assertRaisesRegex(ManifestError, "rights review"):
            validate_manifest(self.manifest, require_cleared=True)

    def test_bytes_verified_only_when_all_pins_match_and_review_asserted(self):
        self.manifest["model"]["rights_clearance"] = "reviewed"
        self.assertTrue(verify_local_assets(self.manifest, self.root))
        (self.root / "assets/demo.gguf").write_bytes(b"modified")
        with self.assertRaisesRegex(ManifestError, "asset mismatch"):
            verify_local_assets(self.manifest, self.root)

    def test_rejects_missing_and_malformed_hash(self):
        for mutation in ("", "0" * 63, "A" * 64, "latest"):
            doc = deepcopy(self.manifest)
            doc["assets"][0]["sha256"] = mutation
            with self.subTest(mutation=mutation), self.assertRaises(ManifestError):
                validate_manifest(doc)
        doc = deepcopy(self.manifest)
        del doc["assets"][0]["sha256"]
        with self.assertRaises(ManifestError):
            validate_manifest(doc)

    def test_rejects_remote_or_escaping_paths(self):
        for path in ("https://cdn.example.org/model.gguf", "/assets/model.gguf",
                     "assets/../secret.gguf", "assets/%2e%2e/model.gguf",
                     "assets\\model.gguf", "C:/private.gguf", "assets/./model.gguf",
                     "assets/model.gguf?token=abc", "file:///tmp/model.gguf"):
            doc = deepcopy(self.manifest)
            doc["assets"][-1]["path"] = path
            with self.subTest(path=path), self.assertRaises(ManifestError):
                validate_manifest(doc)

    def test_rejects_mutable_runtime_and_source_revision(self):
        for version in ("latest", "^3.8.1", "3.8.x", "v3.8.1", "3.8", "3.7.9", "3.8.2"):
            doc = deepcopy(self.manifest)
            doc["runtime"]["version"] = version
            with self.subTest(version=version), self.assertRaises(ManifestError):
                validate_manifest(doc)
        doc = deepcopy(self.manifest)
        doc["model"]["source_revision"] = "main"
        with self.assertRaises(ManifestError):
            validate_manifest(doc)
        doc = deepcopy(self.manifest)
        doc["model"]["source_revision"] = "1" * 40
        with self.assertRaisesRegex(ManifestError, "bind exact declared commit"):
            validate_manifest(doc)

    def test_rejects_runtime_external_fetch_default_download_and_storage(self):
        changes = [
            ("automatic_download", True),
            ("external_runtime_fetch", True),
            ("explicit_download_consent", False),
            ("offline_after_install", False),
            ("contains_private_data", True),
            ("conversation_storage_default", "localStorage"),
        ]
        for key, value in changes:
            doc = deepcopy(self.manifest)
            doc["policy"][key] = value
            with self.subTest(key=key), self.assertRaises(ManifestError):
                validate_manifest(doc)

    def test_rejects_unverifiable_and_credential_urls(self):
        for url in ("http://huggingface.co/x", "https://user:pass@huggingface.co/x",
                    "https://evil.example.org/model", "https://huggingface.co/x#fragment",
                    "https://[", "https://[broken]/x"):
            doc = deepcopy(self.manifest)
            doc["model"]["source_url"] = url
            with self.subTest(url=url), self.assertRaises(ManifestError):
                validate_manifest(doc)

    def test_rejects_unknown_fields_duplicates_and_oversized(self):
        doc = deepcopy(self.manifest)
        doc["model"]["override"] = "yes"
        with self.assertRaises(ManifestError):
            validate_manifest(doc)
        doc = deepcopy(self.manifest)
        doc["assets"][1]["path"] = doc["assets"][0]["path"]
        with self.assertRaises(ManifestError):
            validate_manifest(doc)
        doc = deepcopy(self.manifest)
        doc["assets"][-1]["size_bytes"] = 513 * 1024 * 1024
        with self.assertRaises(ManifestError):
            validate_manifest(doc)
        # Official source *rounded* Qwen Q4_0 file is about 563 decimal MB,
        # above the current conservative 512 MiB per-file policy. No bytes loaded.
        doc = deepcopy(self.manifest)
        doc["assets"][-1]["size_bytes"] = 563_000_000
        with self.assertRaises(ManifestError):
            validate_manifest(doc)
        doc = deepcopy(self.manifest)
        doc["schema_version"] = True
        with self.assertRaises(ManifestError):
            validate_manifest(doc)

    def test_rejects_duplicate_json_keys(self):
        p = self.root / "manifest.json"
        p.write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
        with self.assertRaisesRegex(ManifestError, "duplicate JSON key"):
            load_manifest(p)

    def test_rejects_symlink_asset(self):
        self.manifest["model"]["rights_clearance"] = "reviewed"
        target = self.root / "assets/demo.gguf"
        target.unlink()
        target.symlink_to(self.root / "vendor/wllama.js")
        with self.assertRaises(ManifestError):
            verify_local_assets(self.manifest, self.root)

    def test_rejects_intermediate_directory_symlink_within_root(self):
        self.manifest["model"]["rights_clearance"] = "reviewed"
        original = self.root / "vendor/compat"
        renamed = self.root / "vendor/compat_real"
        original.rename(renamed)
        original.symlink_to(renamed, target_is_directory=True)
        with self.assertRaisesRegex(ManifestError, "includes symlink"):
            verify_local_assets(self.manifest, self.root)

    def test_untrusted_structured_types_are_validation_errors_not_exceptions(self):
        for field, value in (("role", []), ("role", {})):
            doc = deepcopy(self.manifest)
            doc["assets"][-1][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ManifestError):
                validate_manifest(doc)
        for value in ({}, [], None, 1):
            doc = deepcopy(self.manifest)
            doc["model"]["rights_clearance"] = value
            with self.subTest(rights=value), self.assertRaises(ManifestError):
                validate_manifest(doc)


if __name__ == "__main__":
    unittest.main()
