"""Offline source merge invariants; no third-party prose is bundled."""

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.merge_research_sources import merge_files, merge_sources


SOURCE = {
    "id": "synthetic-citation-2026",
    "title": "Synthetic citation for source merge testing",
    "issuer": "Test Publisher",
    "date": "2026",
    "retrieved": "2026-11-04",
    "type": "bibliographic_test",
    "url": "https://example.org/fictional-resource",
    "topics": ["source_provenance"],
    "summary": "Fabricated fixture, not an actual research claim.",
    "limitations": "This source does not exist and is used only as a fixture.",
    "rights": "Test metadata only.",
    "model_training_rights": "not-cleared",
    "source_content_included": False,
    "authors": "Unit Test",
    "verification_method": "synthetic fixture",
    "source_license": "unverified",
}


class ResearchMergeTests(unittest.TestCase):
    def test_merge_metadata_without_mutating_inputs(self):
        baseline = [copy.deepcopy(SOURCE)]
        second = copy.deepcopy(SOURCE)
        second["id"] = "second-citation-2026"
        second["url"] = "https://example.org/second-resource"
        result, count = merge_sources(baseline, [[second]])
        self.assertEqual(1, count)
        self.assertEqual(2, len(result))
        self.assertEqual(1, len(baseline))

    def test_reject_duplicate_urls_even_when_ids_differ(self):
        changed = {**SOURCE, "id": "another-source"}
        with self.assertRaisesRegex(ValueError, "already registered"):
            merge_sources([SOURCE], [[changed]])

    def test_reject_false_training_rights_and_full_text(self):
        for field, value in (("model_training_rights", "permitted"), ("source_content_included", True)):
            changed = {**SOURCE, field: value}
            with self.subTest(field=field), self.assertRaises(ValueError):
                merge_sources([], [[changed]])

    def test_dry_run_keeps_register_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            current = Path(directory) / "current.json"
            batch = Path(directory) / "batch.json"
            current.write_text("[]\n", encoding="utf-8")
            batch.write_text(json.dumps([SOURCE]), encoding="utf-8")
            self.assertEqual((0, 1, 1), merge_files(current, [batch]))
            self.assertEqual("[]\n", current.read_text(encoding="utf-8"))
            self.assertEqual((0, 1, 1), merge_files(current, [batch], apply=True))
            self.assertEqual(SOURCE["id"], json.loads(current.read_text(encoding="utf-8"))[0]["id"])


if __name__ == "__main__":
    unittest.main()
