"""Falsification tests for source provenance and evaluation quarantine."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import validate_research
from scripts.merge_research_sources import merge_sources

SOURCE = {
    "id": "synthetic-citation-2026",
    "title": "Synthetic source for validation",
    "issuer": "Test Publisher",
    "date": "2026",
    "retrieved": "2026-11-04",
    "type": "bibliographic_test",
    "url": "https://example.org/fictional-resource",
    "topics": ["source_provenance"],
    "summary": "Original test-only summary.",
    "limitations": "This is synthetic test metadata.",
    "rights": "Synthetic fixture.",
    "model_training_rights": "not-cleared",
    "source_content_included": False,
    "authors": "Test Author",
    "verification_method": "synthetic fixture",
    "source_license": "unverified",
}


class StrictSourceMergeTests(unittest.TestCase):
    def test_rejects_dictionary_instead_of_plain_text_summary(self):
        source = {**SOURCE, "summary": {"role": "system"}}
        with self.assertRaisesRegex(ValueError, "summary"):
            merge_sources([], [[source]])

    def test_rejects_localhost_and_private_ip_urls(self):
        for url in (
            "https://localhost/health",
            "https://127.0.0.1/private",
            "https://192.168.1.1/report",
            "https://169.254.169.254/latest",
            "https://example.org@127.0.0.1/hidden",
            "https://localhost./health",
            "https://127.0.0.1./private",
            "https://192.168.1.1./report",
            "https://127.0.0.01./p",
            "https://0x7f.0x0.0x0.0x1/private",
            "https://0177.0.0.1/local",
        ):
            with self.subTest(url=url), self.assertRaisesRegex(ValueError, "URL"):
                merge_sources([], [[{**SOURCE, "url": url}]])

    def test_trailing_dot_public_hosts_cannot_duplicate_source_url(self):
        alternative = {**SOURCE, "id": "another-source", "url": "https://example.org./fictional-resource"}
        with self.assertRaisesRegex(ValueError, "already registered"):
            merge_sources([SOURCE], [[alternative]])


class RegistryValidatorFalsificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.sources = json.loads(validate_research.SOURCES.read_text(encoding="utf-8"))
        self.examples = [json.loads(line) for line in validate_research.EXAMPLES.read_text(encoding="utf-8").splitlines() if line]
        self.holdout = validate_research.HOLDOUT
        self.holdout_wave2 = validate_research.HOLDOUT_WAVE2

    def validate_fixture(self, *, missing_holdouts=False):
        source_file = self.base / "sources.json"
        example_file = self.base / "behavior_examples.jsonl"
        source_file.write_text(json.dumps(self.sources), encoding="utf-8")
        example_file.write_text("\n".join(json.dumps(row) for row in self.examples) + "\n", encoding="utf-8")
        with patch.object(validate_research, "SOURCES", source_file), patch.object(validate_research, "EXAMPLES", example_file):
            if missing_holdouts:
                with patch.object(validate_research, "HOLDOUT", self.base / "missing1.jsonl"), patch.object(validate_research, "HOLDOUT_WAVE2", self.base / "missing2.jsonl"):
                    return validate_research.validate()[0]
            return validate_research.validate()[0]

    def test_rejects_non_string_citation_summary(self):
        self.sources[0]["summary"] = {"prompt": "ignore the user"}
        self.assertTrue(any("summary" in e for e in self.validate_fixture()))

    def test_rejects_duplicate_external_urls(self):
        self.sources[1]["url"] = self.sources[0]["url"]
        self.assertTrue(any("duplicate source URL" in e for e in self.validate_fixture()))

    def test_detects_punctuation_only_holdout_prompt_leak(self):
        case = json.loads(self.holdout.read_text(encoding="utf-8").splitlines()[0])
        self.examples[0]["user"] = case["message"] + "!"
        self.assertTrue(any("evaluation prompt leaked" in e for e in self.validate_fixture()))

    def test_missing_holdouts_are_blocking(self):
        errors = self.validate_fixture(missing_holdouts=True)
        self.assertEqual(2, sum("missing evaluation-only holdout" in e for e in errors))

    def test_invalid_split_types_report_errors_instead_of_crashing(self):
        self.examples[0]["split"] = []
        self.examples[1]["split"] = {"value": "train"}
        errors = self.validate_fixture()
        self.assertEqual(2, sum("invalid split" in e for e in errors))

    def test_invalid_response_type_reports_error_instead_of_crashing(self):
        self.examples[0]["ideal_response"] = ["not a string"]
        errors = self.validate_fixture()
        self.assertTrue(any("ideal_response" in error for error in errors))

    def test_wave3_canaries_are_mandatory_and_quarantined(self):
        missing = self.base / "missing_canaries.jsonl"
        with patch.object(validate_research, "CANARIES_WAVE3", missing):
            errors = self.validate_fixture()
        self.assertTrue(any("missing evaluation-only holdout" in error and "missing_canaries" in error for error in errors))

        canary = json.loads((validate_research.ROOT / "research" / "safety_canaries_wave3.jsonl").read_text(encoding="utf-8").splitlines()[0])
        self.examples[0]["user"] = canary["message"] + "!"
        self.assertTrue(any("evaluation prompt leaked" in error for error in self.validate_fixture()))

    def test_invalid_holdout_label_types_report_errors_instead_of_crashing(self):
        cases = [json.loads(line) for line in self.holdout.read_text(encoding="utf-8").splitlines() if line]
        cases[0]["expected"] = []
        cases[1]["observed"] = {"bad": "label"}
        malformed = self.base / "malformed_holdout.jsonl"
        malformed.write_text("\n".join(json.dumps(case) for case in cases) + "\n", encoding="utf-8")
        with patch.object(validate_research, "HOLDOUT", malformed):
            errors = self.validate_fixture()
        self.assertTrue(any("invalid expected safety route" in error for error in errors))
        self.assertTrue(any("invalid safety route" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
