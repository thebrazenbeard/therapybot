"""Model-output quarantine regressions; not a clinical safety qualification.

Earlier source characterization demonstrated synthetic unsafe canaries passing
through unchanged. That failure is preserved in WAVE2_MODEL_OUTPUT_REVIEW.md;
these tests now require them to remain quarantined by default.
"""

import json
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

from therapybot.app import create_server
from therapybot.output_review import ReviewAdmission


class UntrustedLocalModel(BaseHTTPRequestHandler):
    def do_POST(self):
        self.server.calls += 1
        count = int(self.headers.get("Content-Length", "0"))
        _ = self.rfile.read(count)
        if self.server.fail:
            self.send_error(500, "synthetic model failure")
            return
        body = json.dumps({"results": [{"text": self.server.reply}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        return


class ModelOutputBoundaryCharacterization(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.model = ThreadingHTTPServer(("127.0.0.1", 0), UntrustedLocalModel)
        self.model.calls = 0
        self.model.fail = False
        self.model.reply = "SYNTHETIC_NEUTRAL_MODEL_REPLY"
        self.model_thread = threading.Thread(target=self.model.serve_forever, daemon=True)
        self.model_thread.start()
        self.server = create_server(
            0,
            str(Path(self.temp.name) / "synthetic-vault.sqlite3"),
            f"http://127.0.0.1:{self.model.server_port}/api/v1/generate",
        )
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.csrf = {"X-TherapyBot-Token": self.server.csrf}
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close)

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.server.vault.close()
        self.thread.join(timeout=2)
        self.model.shutdown()
        self.model.server_close()
        self.model_thread.join(timeout=2)

    def request(self, path, method="GET", data=None, headers=None):
        payload = None if data is None else json.dumps(data).encode("utf-8")
        request = urllib.request.Request(
            self.base + path,
            data=payload,
            headers={"Content-Type": "application/json", **(headers or {})},
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read())

    def chat(self, message):
        return self.request("/api/chat", "POST", {"message": message, "save": False}, self.csrf)

    def test_no_qualified_reviewer_does_not_spend_model_compute(self):
        self.model.reply = 'SYNTHETIC_NEVER_REQUESTED_CANARY'
        status, result = self.chat('How do I organize the next task?')
        self.assertEqual(200, status)
        self.assertEqual('review_hold', result['mode'])
        self.assertEqual(0, self.model.calls)
        self.assertNotIn('SYNTHETIC_NEVER_REQUESTED_CANARY', json.dumps(result))
        self.assertNotIn('generated a draft', result['reply'].lower())

    def test_unreviewed_neural_candidate_is_quarantined_by_default(self):
        self.model.reply = 'SYNTHETIC_UNREVIEWED_NEURAL_CANARY'
        status, result = self.chat('How do people build better habits?')
        self.assertEqual(200, status)
        self.assertEqual('review_hold', result['mode'])
        self.assertNotIn('SYNTHETIC_UNREVIEWED_NEURAL_CANARY', result['reply'])
        self.assertIn('cannot independently review', result['reply'].lower())
        self.assertEqual(0, self.server.vault.db.execute('SELECT COUNT(*) FROM records').fetchone()[0])

    def test_quarantines_unreviewed_concern_reply(self):
        self.model.reply = "SYNTHETIC_FALSE_REASSURANCE_CANARY"
        status, result = self.chat("I sometimes wish I would never wake up.")
        self.assertEqual(200, status)
        self.assertEqual("concern", result["safety"])
        self.assertEqual("review_hold", result["mode"])
        self.assertIn("I want to take that seriously", result["reply"])
        self.assertNotIn("SYNTHETIC_FALSE_REASSURANCE_CANARY", result["reply"])
        self.assertEqual(0, self.model.calls)

    def test_quarantines_unreviewed_diagnosis_and_spiritual_causality(self):
        for canary, prompt in (
            ("SYNTHETIC_DIAGNOSTIC_CERTAINTY_CANARY", "What are some possible causes of low motivation?"),
            ("SYNTHETIC_UNVERIFIED_SUPERNATURAL_CAUSE_CANARY", "Could a strange experience have a spiritual interpretation?"),
        ):
            with self.subTest(canary=canary):
                self.model.reply = canary
                status, result = self.chat(prompt)
                self.assertEqual(200, status)
                self.assertEqual("review_hold", result["mode"])
                self.assertNotIn(canary, result["reply"])

    def test_quarantines_unreviewed_unsupported_reference(self):
        self.model.reply = "SYNTHETIC_FAKE_CITATION https://example.invalid/no-source"
        status, result = self.chat("Explain behavior and interpersonal patterns")
        self.assertEqual(200, status)
        self.assertNotIn("https://example.invalid/no-source", result["reply"])
        # The separately retrieved source list is not a verifier of model prose.
        self.assertNotIn("https://example.invalid/no-source", [s["url"] for s in result["citations"]])

    def test_immediate_static_response_does_not_consult_untrusted_model(self):
        self.model.reply = "SHOULD_NOT_BE_RETURNED_CANARY"
        status, result = self.chat("I already swallowed forty tablets to die")
        self.assertEqual(200, status)
        self.assertEqual("safety", result["mode"])
        self.assertEqual("immediate", result["safety"])
        self.assertNotIn("SHOULD_NOT_BE_RETURNED_CANARY", result["reply"])
        self.assertEqual(0, self.model.calls)

    def test_opt_in_storage_remains_off_and_quarantine_is_not_ready(self):
        status, result = self.chat("What is behavioral activation?")
        self.assertEqual(200, status)
        self.assertEqual("review_hold", result["mode"])
        self.assertFalse(self.server.vault.initialized)
        count = self.server.vault.db.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        self.assertEqual(0, count)
        code, system_status = self.request("/api/status")
        self.assertEqual(200, code)
        self.assertTrue(system_status["endpoint_reachable"])
        self.assertFalse(system_status["ready"])
        self.assertFalse(system_status["output_review_qualified"])
        self.assertFalse(system_status["clinical_qualified"])
        self.assertEqual("observed_local_model_output_only_not_safety", system_status["ready_scope"])

    def test_oversize_candidate_quarantined_even_if_reviewer_would_allow(self):
        self.model.reply = 'SYNTHETIC_LONG_CANARY' + 'x' * 15_000
        self.server.output_reviewer = lambda **kwargs: 'allow'
        status, result = self.chat('What would help with organizing tasks?')
        self.assertEqual(200, status)
        self.assertEqual('review_hold', result['mode'])
        self.assertNotIn('SYNTHETIC_LONG_CANARY', json.dumps(result))
        self.assertFalse(result['saved'])

    def test_explicit_server_reviewer_can_allow_benign_development_reply(self):
        self.model.reply = "A bounded experiment can start with one concrete question."
        seen = []
        def reviewer(**kwargs):
            seen.append(kwargs)
            return "allow"
        self.server.output_reviewer = reviewer
        status, result = self.chat("How can I clarify this task?")
        self.assertEqual(200, status)
        self.assertEqual("model", result["mode"])
        self.assertEqual(self.model.reply, result["reply"])
        self.assertEqual("explicit_allow_unqualified", result["output_review"])
        self.assertFalse(result["saved"])
        self.assertEqual(1, len(seen))
        self.assertEqual("normal", seen[0]["input_route"])
        self.assertEqual(self.model.reply, seen[0]["candidate"])
        code, system_status = self.request("/api/status")
        self.assertEqual(200, code)
        self.assertTrue(system_status["ready"])
        self.assertFalse(system_status["output_review_qualified"])
        self.assertFalse(system_status["clinical_qualified"])
        self.assertEqual("observed_local_model_output_only_not_safety", system_status["ready_scope"])

    def test_explicit_reviewer_block_and_unknown_never_leak(self):
        for verdict in ("block", "unknown", True, None, {"route": "allow"}):
            with self.subTest(verdict=verdict):
                self.server.output_reviewer = lambda **kwargs: verdict
                self.model.reply = "SYNTHETIC_BLOCKED_COMPLETION_CANARY"
                status, result = self.chat("Can you help me reflect?")
                self.assertEqual(200, status)
                self.assertEqual("review_hold", result["mode"])
                self.assertEqual("quarantined", result["output_review"])
                self.assertNotIn(self.model.reply, json.dumps(result))
                self.assertFalse(result["saved"])

    def test_reviewer_exception_quarantines_without_error_or_candidate_leak(self):
        def reviewer(**kwargs):
            raise RuntimeError("SYNTHETIC_REVIEWER_EXCEPTION_CANARY")
        self.server.output_reviewer = reviewer
        self.model.reply = "SYNTHETIC_UNSAFE_MODEL_CANARY"
        status, result = self.chat("How can I plan tomorrow?")
        self.assertEqual(200, status)
        self.assertEqual("review_hold", result["mode"])
        self.assertNotIn("SYNTHETIC_UNSAFE_MODEL_CANARY", json.dumps(result))
        self.assertNotIn("SYNTHETIC_REVIEWER_EXCEPTION_CANARY", json.dumps(result))

    def test_urgent_input_skips_model_and_optional_reviewer(self):
        def forbidden_reviewer(**kwargs):
            self.fail("Reviewer should not see immediate input")
        self.server.output_reviewer = forbidden_reviewer
        status, result = self.chat("I already swallowed forty tablets to die")
        self.assertEqual(200, status)
        self.assertEqual("safety", result["mode"])
        self.assertEqual("not_applicable", result["output_review"])
        self.assertEqual(0, self.model.calls)

    def test_opt_in_save_never_persists_quarantined_completion(self):
        status, unlocked = self.request(
            "/api/unlock", "POST", {"passphrase": "a-synthetic-very-long-passphrase"}, self.csrf)
        self.assertEqual(200, status)
        headers = {**self.csrf, "X-TherapyBot-Session": unlocked["session"]}
        self.model.reply = "SYNTHETIC_NOT_PERSISTED_CANARY"
        status, result = self.request("/api/chat", "POST",
            {"message": "Tell me about task focus", "save": True}, headers)
        self.assertEqual(200, status)
        self.assertEqual("review_hold", result["mode"])
        self.assertFalse(result["saved"])
        self.assertNotIn("SYNTHETIC_NOT_PERSISTED_CANARY", json.dumps(result))
        self.assertEqual([], self.server.vault.list("chat"))
        self.assertEqual(0, self.server.vault.db.execute(
            "SELECT COUNT(*) FROM records").fetchone()[0])

    def test_reviewed_block_with_opt_in_save_never_persists_candidate(self):
        status, unlocked = self.request(
            "/api/unlock", "POST", {"passphrase": "another-synthetic-long-passphrase"}, self.csrf)
        self.assertEqual(200, status)
        headers = {**self.csrf, "X-TherapyBot-Session": unlocked["session"]}
        self.server.output_reviewer = lambda **kwargs: "block"
        self.model.reply = "SYNTHETIC_GENERATED_BLOCKED_CANARY"
        status, result = self.request("/api/chat", "POST",
            {"message": "What is behavior change?", "save": True}, headers)
        self.assertEqual(200, status)
        self.assertGreater(self.model.calls, 0)
        self.assertEqual("review_hold", result["mode"])
        self.assertFalse(result["saved"])
        self.assertNotIn(self.model.reply, json.dumps(result))
        self.assertEqual([], self.server.vault.list("chat"))

    def test_hung_reviewer_is_bounded_and_late_allow_cannot_leak(self):
        status, unlocked = self.request(
            "/api/unlock", "POST", {"passphrase": "synthetic-review-admission-passphrase"}, self.csrf)
        self.assertEqual(200, status)
        saved_headers = {**self.csrf, "X-TherapyBot-Session": unlocked["session"]}
        self.model.reply = "SYNTHETIC_LATE_ALLOW_CANDIDATE_CANARY"
        reviewer_entered = threading.Event()
        release_reviewer = threading.Event()
        gate_lock = threading.Lock()
        entered = []
        results, errors = {}, {}

        def nonreturning_reviewer(**kwargs):
            with gate_lock:
                entered.append(1)
                if len(entered) >= 2:
                    reviewer_entered.set()
            release_reviewer.wait()
            return "allow"  # A late allow is never authority after timeout.

        self.server.output_reviewer = nonreturning_reviewer

        def send(name, headers, save):
            try:
                results[name] = self.request("/api/chat", "POST", {
                    "message": f"Synthetic ordinary question {name}", "save": save}, headers)
            except Exception as exc:
                errors[name] = repr(exc)

        workers = [
            threading.Thread(target=send, args=("a", saved_headers, True), daemon=True),
            threading.Thread(target=send, args=("b", self.csrf, False), daemon=True),
        ]
        third = threading.Thread(target=send, args=("c", self.csrf, False), daemon=True)
        fourth = threading.Thread(target=send, args=("d", self.csrf, False), daemon=True)
        quick_third, returned_before_release, quick_after_timeout = False, False, False
        try:
            for worker in workers:
                worker.start()
            self.assertTrue(reviewer_entered.wait(timeout=3), "Two callbacks should enter")
            third.start()
            third.join(timeout=1.25)
            quick_third = not third.is_alive()
            calls_before_release = self.model.calls
            status_during, _ = self.request("/api/status")
            for worker in workers:
                worker.join(timeout=3.5)
            returned_before_release = all(not worker.is_alive() for worker in workers)
            fourth.start()  # Both HTTP waiters timed out, callbacks remain hung.
            fourth.join(timeout=1.25)
            quick_after_timeout = not fourth.is_alive()
            calls_after_timeout = self.model.calls
        finally:
            release_reviewer.set()
            for worker in [*workers, third, fourth]:
                if worker.ident is not None:
                    worker.join(timeout=5)

        self.assertTrue(quick_third, "Saturated admission must not wait on another hung reviewer")
        self.assertTrue(returned_before_release, "Reviewer wait must have a bounded deadline")
        self.assertTrue(quick_after_timeout, "Timed-out callbacks must still hold their slots")
        self.assertEqual(2, calls_after_timeout, "Fourth request must also skip inference")
        self.assertEqual(2, calls_before_release, "Third request must skip model inference")
        self.assertEqual(2, len(entered), "No third callback should start while both slots are held")
        self.assertEqual(200, status_during, "Unrelated status must remain responsive")
        self.assertEqual({}, errors)
        for status, response in results.values():
            self.assertEqual(200, status)
            self.assertEqual("review_hold", response["mode"])
            self.assertEqual("quarantined", response["output_review"])
            self.assertFalse(response["saved"])
            self.assertNotIn("SYNTHETIC_LATE_ALLOW_CANDIDATE_CANARY", json.dumps(response))
        self.assertEqual({"a", "b", "c", "d"}, set(results))
        self.assertEqual([], self.server.vault.list("chat"), "Late allow must never write to vault")

        self.server.output_reviewer = lambda **kwargs: "allow"
        recovered = None
        for _ in range(20):
            recovered = self.chat("Synthetic recovery question")
            if recovered[1]["mode"] == "model":
                break
            time.sleep(0.05)
        self.assertEqual(200, recovered[0])
        self.assertEqual("model", recovered[1]["mode"])

    def test_thread_start_failure_fails_closed_and_releases_slot(self):
        admission = ReviewAdmission(capacity=1, timeout=0.1)
        kwargs = {"message": "synthetic", "context": [], "input_route": "normal",
                  "reviewer": lambda **kwargs: "allow"}
        with mock.patch("therapybot.output_review.threading.Thread",
                        side_effect=RuntimeError("SYNTHETIC_START_FAILURE_CANARY")):
            candidate, verdict = admission.generate_reviewed(
                lambda: "SYNTHETIC_UNREVIEWED_CANARY", **kwargs)
        self.assertIsNone(candidate)
        self.assertEqual("unknown", verdict)
        # A failed start did not strand the only reviewer slot.
        candidate, verdict = admission.generate_reviewed(
            lambda: "SYNTHETIC_BENIGN_AFTER_START_FAILURE", **kwargs)
        self.assertEqual("allow", verdict)
        self.assertEqual("SYNTHETIC_BENIGN_AFTER_START_FAILURE", candidate)

    def test_model_failure_returns_local_503_without_cloud_fallback(self):
        self.server.output_reviewer = lambda **kwargs: 'allow'
        self.model.fail = True
        status, result = self.chat("Explain behavioral activation")
        self.assertEqual(503, status)
        self.assertIn("no cloud fallback", result["error"].lower())
        self.assertEqual(0, self.server.vault.db.execute("SELECT COUNT(*) FROM records").fetchone()[0])
        # A failed generator must return its admission slot; the next
        # synthetic successful request remains possible.
        self.model.fail = False
        status, result = self.chat("Synthetic recovered local-model question")
        self.assertEqual(200, status)
        self.assertEqual("model", result["mode"])


if __name__ == "__main__":
    unittest.main()
