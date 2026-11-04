"""Unit tests for bounded observation semantics; no network or credentials."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
from poll_therapybot import MAX_COMMENT_BYTES, scan


def packet(*, message_id: str = "msg-001", effect: str = "READ_ONLY", performative: str = "REVIEW", target: str = "therapybot:bt2") -> dict:
    return {
        "protocol": "INTRANEL/1",
        "origin": "therapybot:pr11-review",
        "actor": "therapybot:pr11-review",
        "target": target,
        "reply_to": "github:therapybot-issue-4",
        "message_id": message_id,
        "conversation_id": "tb-review-001",
        "performative": performative,
        "effect_class": effect,
        "security_profile": "OPEN",
        "exact_subject": "pr11@111+pr12@222",
        "payload": {"claim_type": "SOURCE"},
    }


def fake_parse(obj: dict) -> SimpleNamespace:
    # Parser dependency injection lets these tests isolate observer behavior.
    # Actual operation requires upstream intranel.parse_message; the fake
    # deliberately does not claim schema or cryptographic qualification.
    if obj.get("protocol") != "INTRANEL/1" or not obj.get("message_id"):
        raise ValueError("invalid synthetic packet")
    return SimpleNamespace(
        target=obj["target"],
        message_id=obj["message_id"],
        conversation_id=obj["conversation_id"],
        exact_subject=obj.get("exact_subject"),
        performative=SimpleNamespace(value=obj["performative"]),
        original=obj,
    )


def fake_digest(obj: SimpleNamespace) -> str:
    wire = json.dumps(obj.original, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(wire).hexdigest()


def comment(comment_id: int, *packets: dict) -> dict:
    return {"id": comment_id, "body": "\n".join("```json\n" + json.dumps(p) + "\n```" for p in packets)}


def run(pages, start_page=1):
    return scan(pages, start_page=start_page, expected_target="therapybot:bt2", parse=fake_parse, digest=fake_digest)


class ObserverTests(unittest.TestCase):
    def test_valid_review_is_only_observed(self):
        report = run([[comment(123, packet())]])
        self.assertEqual(report["counts"]["new"], 1)
        self.assertTrue(report["coverage_complete"])
        rec = report["packets"][0]
        self.assertEqual(rec["observation"], "NEW")
        self.assertFalse(rec["delivered"])
        self.assertFalse(rec["origin_authenticated"])
        self.assertFalse(rec["effect_executed"])
        self.assertNotIn("payload", rec)

    def test_duplicate_and_collision_distinguished(self):
        first = packet()
        different = packet()
        different["payload"]["claim_type"] = "INFERENCE"
        report = run([[comment(11, first), comment(12, first), comment(13, different)]])
        self.assertEqual([x["observation"] for x in report["packets"]], ["NEW", "DUPLICATE", "CONFLICT"])

    def test_mutation_and_wrong_target_ignored(self):
        report = run([[comment(11, packet(effect="REVERSIBLE_MUTATION"), packet(performative="EXECUTE"), packet(target="therapybot:another"))]])
        self.assertEqual(report["counts"]["ignored"], 3)
        self.assertEqual(report["packets"], [])

    def test_duplicate_keys_rejected(self):
        body = '```json\n{"protocol":"INTRANEL/1","protocol":"INTRANEL/1"}\n```'
        report = run([[{"id": 11, "body": body}]])
        self.assertEqual(report["counts"]["rejected"], 1)

    def test_overlong_and_overfenced_comment_held(self):
        report = run([[{"id": 11, "body": "x" * (MAX_COMMENT_BYTES + 1)}, comment(12, *(packet(message_id=f"m-{i}") for i in range(5)))]])
        self.assertEqual(report["counts"]["oversized"], 1)
        self.assertEqual(report["counts"]["packet_overflow"], 1)
        self.assertFalse(report["coverage_complete"])
        self.assertEqual(report["packets"], [])

    def test_page_ceiling_and_resumption_never_claim_complete(self):
        full = [{"id": i + 1, "body": ""} for i in range(100)]
        self.assertEqual(run([full])["coverage_status"], "HOLD_PAGINATION_LIMIT")
        self.assertEqual(run([[comment(101, packet())]], start_page=2)["coverage_status"], "HOLD_PRECEDING_PAGES_UNVERIFIED")

    def test_missing_comment_identity_is_not_silently_discarded(self):
        with self.assertRaises(ValueError):
            run([[{"body": ""}]])


if __name__ == "__main__":
    unittest.main()
