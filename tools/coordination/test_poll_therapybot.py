"""Unit tests for bounded observation semantics; no network or credentials."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))
from poll_therapybot import MAX_COMMENT_BYTES, scan, correlate_review_chain

PR11 = "a" * 40
PR12 = "b" * 40
SUBJECT = f"therapybot#11@{PR11}+therapybot#12@{PR12}"


def packet(*, message_id: str = "msg-001", effect: str = "READ_ONLY", performative: str = "REVIEW", target: str = "therapybot:bt2", origin: str = "therapybot:pr11-review", parent: str | None = None) -> dict:
    return {
        "protocol": "INTRANEL/1",
        "origin": origin,
        "actor": origin,
        "target": target,
        "reply_to": "github:therapybot-issue-4",
        "message_id": message_id,
        "conversation_id": "tb-review-001",
        "performative": performative,
        "effect_class": effect,
        "security_profile": "OPEN",
        "parent_message_id": parent,
        "subject": "therapybot/canonical-engine-selection",
        "exact_subject": SUBJECT,
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
        origin=obj["origin"],
        message_id=obj["message_id"],
        conversation_id=obj["conversation_id"],
        parent_message_id=obj.get("parent_message_id"),
        subject=obj.get("subject"),
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


def run_chain(pages, heads=None):
    all_packets = scan(pages, start_page=1, expected_target=None, parse=fake_parse, digest=fake_digest)
    return correlate_review_chain(all_packets, current_heads=heads)


def ack(*, parent: str | None = "msg-001", origin: str = "therapybot:bt2", target: str = "therapybot:pr11-review", message_id: str = "ack-001") -> dict:
    return packet(message_id=message_id, performative="ACK", target=target, origin=origin, parent=parent)


def review_report(*, parent: str | None = "ack-001") -> dict:
    return packet(message_id="report-001", performative="REPORT", target="therapybot:pr11-review", origin="therapybot:bt2", parent=parent)


def requester_report() -> dict:
    return packet(message_id="requester-report-001", performative="REPORT", target="therapybot:bt2", origin="therapybot:pr11-review", parent="ack-001")


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

    def test_causal_ack_then_report_is_claim_only(self):
        report = run_chain([[comment(10, packet()), comment(11, ack()), comment(12, review_report())]], heads={11: PR11, 12: PR12})
        self.assertEqual(report["chain_state"], "REVIEW_ACK_REPORT_OBSERVED_UNAUTHENTICATED")
        self.assertTrue(report["ack_claim_observed"])
        self.assertTrue(report["report_claim_observed"])
        self.assertFalse(report["delivered"])
        self.assertFalse(report["ack_accepted_as_authority"])

    def test_current_ack_without_report_is_pending(self):
        report = run_chain([[comment(10, packet()), comment(11, ack())]], heads={11: PR11, 12: PR12})
        self.assertEqual(report["chain_state"], "WAIT_REPORT_NOT_OBSERVED")
        self.assertTrue(report["ack_claim_observed"])

    def test_requester_report_is_not_misidentified_as_bt2_report(self):
        report = run_chain([[comment(10, packet()), comment(11, ack()), comment(12, requester_report())]], heads={11: PR11, 12: PR12})
        self.assertEqual(report["chain_state"], "WAIT_RESPONDER_REPORT_NOT_OBSERVED")
        self.assertTrue(report["requester_report_claim_observed"])
        self.assertFalse(report["report_claim_observed"])

    def test_ack_with_missing_parent_is_held(self):
        report = run_chain([[comment(10, packet()), comment(11, ack(parent=None))]], heads={11: PR11, 12: PR12})
        self.assertEqual(report["chain_state"], "HOLD_ACK_CAUSAL_MISMATCH")

    def test_report_with_wrong_parent_is_held(self):
        report = run_chain([[comment(10, packet()), comment(11, ack()), comment(12, review_report(parent="unrelated"))]], heads={11: PR11, 12: PR12})
        self.assertEqual(report["chain_state"], "HOLD_REPORT_CAUSAL_MISMATCH")

    def test_spoof_like_origin_and_target_held(self):
        report = run_chain([[comment(10, packet()), comment(11, ack(origin="therapybot:someone-else"))]], heads={11: PR11, 12: PR12})
        self.assertEqual(report["chain_state"], "HOLD_ACK_ORIGIN_TARGET_MISMATCH")

    def test_stale_heads_hold_even_with_valid_causal_claims(self):
        report = run_chain([[comment(10, packet()), comment(11, ack()), comment(12, review_report())]], heads={11: "c" * 40, 12: PR12})
        self.assertEqual(report["chain_state"], "HOLD_STALE_SUBJECT")
        self.assertEqual(report["subject_currentness"], "STALE")
        self.assertTrue(report["ack_claim_observed"])
        self.assertTrue(report["report_claim_observed"])
        self.assertFalse(report["ack_accepted_as_authority"])

    def test_unknown_heads_hold_without_inventing_currentness(self):
        report = run_chain([[comment(10, packet()), comment(11, ack())]], heads=None)
        self.assertEqual(report["chain_state"], "HOLD_CURRENT_HEADS_UNKNOWN")
        self.assertTrue(report["ack_claim_observed"])

    def test_same_packet_identity_different_target_is_conflict(self):
        conflicting = packet(target="therapybot:pr11-review")
        report = run_chain([[comment(10, packet()), comment(11, conflicting), comment(12, ack())]], heads={11: PR11, 12: PR12})
        self.assertEqual(report["chain_state"], "HOLD_IDENTITY_COLLISION")

    def test_same_packet_identity_different_conversation_is_conflict(self):
        conflicting = packet()
        conflicting["conversation_id"] = "different-conversation"
        report = run_chain([[comment(10, packet()), comment(11, conflicting), comment(12, ack())]], heads={11: PR11, 12: PR12})
        self.assertEqual(report["chain_state"], "HOLD_IDENTITY_COLLISION")

    def test_missing_review_parent_cannot_be_bootstrapped_by_ack(self):
        report = run_chain([[comment(11, ack())]], heads={11: PR11, 12: PR12})
        self.assertEqual(report["chain_state"], "HOLD_PARENT_REVIEW_NOT_OBSERVED")


if __name__ == "__main__":
    unittest.main()
