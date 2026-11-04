"""Synthetic claim/reference attribution tests (no patient data or copied articles)."""

import copy
import unittest

from therapybot.claim_evidence import audit_claim_references


SOURCES = [
    {"id": "source-a", "url": "https://example.org/guideline", "title": "Example guideline",
     "section_anchor": "Section A", "model_training_rights": "not-cleared"},
    {"id": "source-b", "url": "https://example.org/study", "title": "Example study"},
]


def synthetic_claim():
    return {"id": "claim-1", "text": "A fictional breathing exercise uses a slower exhale.",
            "references": [{"source_id": "source-a", "url": "https://example.org/guideline",
                            "section": "Section A",
                            "excerpt": "Invented example evidence passage used only in a synthetic test."}]}


class ClaimEvidenceTests(unittest.TestCase):
    def test_known_source_metadata_never_becomes_claim_support_verification(self):
        result = audit_claim_references([synthetic_claim()], SOURCES)
        self.assertEqual("metadata-only", result["assurance_level"])
        self.assertEqual("caller-supplied-unverified", result["catalog_authority"])
        self.assertFalse(result["catalog_authenticated"])
        self.assertFalse(result["claim_support_verified"])
        entry = result["claims"][0]
        self.assertTrue(entry["all_references_metadata_matched"])
        self.assertFalse(entry["claim_support_verified"])
        self.assertTrue(entry["independent_review_required"])
        self.assertEqual("source-a", entry["references"][0]["source_id"])
        self.assertTrue(entry["references"][0]["metadata_match"])
        self.assertTrue(entry["references"][0]["section_supplied"])
        self.assertTrue(entry["references"][0]["excerpt_supplied"])
        self.assertFalse(entry["references"][0]["claim_support_verified"])

    def test_mismatched_url_and_hallucinated_source_are_visible(self):
        claim = synthetic_claim()
        claim["references"] = [
            {"source_id": "source-a", "url": "https://example.org/something-else"},
            {"source_id": "made-up", "url": "https://example.org/imagined"},
        ]
        result = audit_claim_references([claim], SOURCES)
        self.assertFalse(result["all_claims_metadata_matched"])
        self.assertFalse(result["claims"][0]["all_references_metadata_matched"])
        self.assertEqual([False, False], [r["metadata_match"] for r in result["claims"][0]["references"]])
        self.assertFalse(result["claim_support_verified"])

    def test_no_references_never_vacuously_passes_and_inputs_are_not_mutated(self):
        claims = [{"id": "claim-2", "text": "A harmless fictional statement.", "references": []}]
        before = copy.deepcopy((claims, SOURCES))
        result = audit_claim_references(claims, SOURCES)
        self.assertFalse(result["claims"][0]["all_references_metadata_matched"])
        self.assertEqual((claims, SOURCES), before)

    def test_refuses_user_supplied_verification_and_duplicate_identity(self):
        claim = synthetic_claim()
        claim["references"][0]["claim_support_verified"] = True
        with self.assertRaises(ValueError):
            audit_claim_references([claim], SOURCES)
        with self.assertRaises(ValueError):
            audit_claim_references([synthetic_claim(), synthetic_claim()], SOURCES)
        with self.assertRaises(ValueError):
            audit_claim_references([synthetic_claim()], SOURCES + [{"id": "source-a", "url": "https://example.org/other"}])

    def test_rejects_oversized_untrusted_metadata_and_malformed_source_shapes(self):
        for bad in (None, {}, [{"id": "x", "text": "ok", "references": "not-list"}],
                    [{"id": "x", "text": "x" * 2001, "references": []}]):
            with self.subTest(bad=repr(bad)[:40]), self.assertRaises(ValueError):
                audit_claim_references(bad, SOURCES)
        with self.assertRaises(ValueError):
            audit_claim_references([synthetic_claim()], [{"id": "a", "url": "javascript:alert(1)"}])

    def test_rejects_loopback_private_and_local_intranet_links(self):
        unfit = (
            "https://127.0.0.1/private", "https://10.0.0.8/health",
            "https://169.254.1.2/", "https://[::1]/admin", "https://[fd00::3]/",
            "https://localhost/a", "https://LOCALHOST./a",
            "https://vault.local/private", "https://nas.lan/admin",
            "https://host.internal/", "https://127.0.0.1.nip.io/private",
            "https://no-dot-host/a",
            "https://127.1/private", "https://127.0.1/admin",
            "https://0177.0.0.1/", "https://0x7f.0x0.0x0.0x1/",
            "https://10.1/health", "https://192.168.1/",
        )
        for url in unfit:
            with self.subTest(url=url), self.assertRaises(ValueError):
                audit_claim_references([synthetic_claim()], [{"id": "private", "url": url}])

    def test_caller_controlled_fake_catalog_match_is_never_authenticated(self):
        fictitious = [{"id": "fabricated", "url": "https://plausible-example.org/citation"}]
        claim = {"id": "c-fake", "text": "An invented assertion with no validated publication.",
                 "references": [{"source_id": "fabricated", "url": fictitious[0]["url"]}]}
        result = audit_claim_references([claim], fictitious)
        self.assertTrue(result["all_claims_metadata_matched"])
        self.assertEqual("caller-supplied-unverified", result["catalog_authority"])
        self.assertFalse(result["catalog_authenticated"])
        self.assertFalse(result["claim_support_verified"])


if __name__ == "__main__":
    unittest.main()
