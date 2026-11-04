"""Synthetic local output-quarantine tests, not clinical qualification."""

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
from therapybot.safety import CONCERN_PREFIX


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

    def test_default_output_review_holds_without_invoking_model(self):
        self.model.reply = "SYNTHETIC_UNREVIEWED_BAD_CANARY"
        status, result = self.chat("Tell me about ferns")
        self.assertEqual(200, status)
        self.assertEqual("review_hold", result["mode"])
        self.assertEqual("quarantined", result["output_review"])
        self.assertNotIn("SYNTHETIC_UNREVIEWED_BAD_CANARY", result["reply"])
        self.assertEqual(0, self.model.calls)
        self.assertEqual(False, result["saved"])

    def test_observes_unscreened_concern_reply(self):
        self.model.reply = "SYNTHETIC_FALSE_REASSURANCE_CANARY"
        status, result = self.chat("I sometimes wish I would never wake up.")
        self.assertEqual(200, status)
        self.assertEqual("concern", result["safety"])
        self.assertEqual("review_hold", result["mode"])
        self.assertTrue(result["reply"].startswith(CONCERN_PREFIX), "concern review hold lost safety preface")
        self.assertNotIn("SYNTHETIC_FALSE_REASSURANCE_CANARY", result["reply"])
        self.assertEqual(0, self.model.calls)

    def test_coercion_concern_does_not_cast_threatened_person_as_actor(self):
        status, result = self.chat("My husband blocked the exit and I am frightened.")
        self.assertEqual(200, status)
        self.assertEqual("concern", result["safety"])
        self.assertEqual("review_hold", result["mode"])
        self.assertIn("Are you safe right now", result["reply"])
        self.assertNotIn("thinking of acting on it", result["reply"])
        self.assertEqual(0, self.model.calls)

    def test_rejected_or_unknown_review_of_concern_keeps_safety_preface(self):
        self.model.reply = "SYNTHETIC_FALSE_REASSURANCE_CANARY"
        for verdict in ("block", "unknown", {"allow": True}):
            with self.subTest(verdict=repr(verdict)):
                self.server.output_reviewer = lambda **_kwargs: verdict
                status, result = self.chat("I sometimes wish I would never wake up.")
                self.assertEqual(200, status)
                self.assertEqual("concern", result["safety"])
                self.assertEqual("review_hold", result["mode"])
                self.assertTrue(result["reply"].startswith(CONCERN_PREFIX), "concern review hold lost safety preface")
                self.assertNotIn("SYNTHETIC_FALSE_REASSURANCE_CANARY", result["reply"])

    def test_observes_unscreened_diagnosis_and_spiritual_causality(self):
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
                self.assertEqual(0, self.model.calls)

    def test_observes_unscreened_unsupported_reference(self):
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

    def test_opt_in_storage_remains_off_and_unreviewed_model_status_is_not_ready(self):
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

    def test_model_failure_returns_local_503_without_cloud_fallback(self):
        self.server.output_reviewer = lambda **_kwargs: "allow"
        self.model.fail = True
        status, result = self.chat("Explain behavioral activation")
        self.assertEqual(503, status)
        self.assertIn("no cloud fallback", result["error"].lower())
        self.assertEqual(0, self.server.vault.db.execute("SELECT COUNT(*) FROM records").fetchone()[0])

        self.model.fail = False
        status, result = self.chat("Synthetic model recovered question")
        self.assertEqual(200, status)
        self.assertEqual("model", result["mode"])

    def test_review_admission_releases_capacity_on_worker_start_failure(self):
        admission = ReviewAdmission(capacity=1, timeout=0.1)
        reviewer_input = {"message": "synthetic", "context": [], "input_route": "normal",
                          "reviewer": lambda **_kwargs: "allow"}
        with mock.patch("therapybot.output_review.threading.Thread",
                        side_effect=RuntimeError("synthetic worker-start error")):
            candidate, verdict = admission.generate_reviewed(
                lambda: "SYNTHETIC_UNREVIEWED_CANDIDATE", **reviewer_input)
        self.assertIsNone(candidate)
        self.assertEqual("unknown", verdict)
        candidate, verdict = admission.generate_reviewed(
            lambda: "SYNTHETIC_RECOVERED_CANDIDATE", **reviewer_input)
        self.assertEqual("allow", verdict)
        self.assertEqual("SYNTHETIC_RECOVERED_CANDIDATE", candidate)

    def test_review_admission_releases_capacity_on_generator_error(self):
        admission = ReviewAdmission(capacity=1, timeout=0.1)
        reviewer_input = {"message": "synthetic", "context": [], "input_route": "normal",
                          "reviewer": lambda **_kwargs: "allow"}

        def broken_generator():
            raise RuntimeError("synthetic generator error")

        with self.assertRaisesRegex(RuntimeError, "synthetic generator error"):
            admission.generate_reviewed(broken_generator, **reviewer_input)
        candidate, verdict = admission.generate_reviewed(
            lambda: "SYNTHETIC_RECOVERED_CANDIDATE", **reviewer_input)
        self.assertEqual("allow", verdict)
        self.assertEqual("SYNTHETIC_RECOVERED_CANDIDATE", candidate)

    def test_review_admission_holds_system_exit_from_callback(self):
        admission = ReviewAdmission(capacity=1, timeout=0.2)

        def reviewer_exits(**_kwargs):
            raise SystemExit("synthetic callback exit")

        candidate, verdict = admission.generate_reviewed(
            lambda: "SYNTHETIC_MUST_NOT_ESCAPE", message="synthetic",
            context=[], input_route="normal", reviewer=reviewer_exits)
        self.assertIsNone(candidate)
        self.assertEqual("unknown", verdict)

    def test_injected_reviewer_cannot_expose_rejected_or_malformed_candidate(self):
        self.server.output_reviewer = lambda **_kwargs: "block"
        self.model.reply = "SYNTHETIC_REJECTED_CANARY"
        status, result = self.chat("Growing ferns")
        self.assertEqual(200, status)
        self.assertEqual("review_hold", result["mode"])
        self.assertEqual("quarantined", result["output_review"])
        self.assertNotIn("SYNTHETIC_REJECTED_CANARY", result["reply"])
        self.assertEqual(1, self.model.calls)
        self.server.output_reviewer = lambda **_kwargs: {"allow": True}
        self.model.reply = "SYNTHETIC_UNVERIFIED_CANARY"
        status, result = self.chat("I need a houseplant")
        self.assertEqual(200, status)
        self.assertEqual("review_hold", result["mode"])
        self.assertNotIn("SYNTHETIC_UNVERIFIED_CANARY", result["reply"])

    def test_opt_in_developer_reviewer_marks_observed_model_not_clinically_qualified(self):
        self.server.output_reviewer = lambda **_kwargs: "allow"
        self.model.reply = "SYNTHETIC_EXPLICIT_DEVELOPER_ALLOW"
        status, result = self.chat("Growing ferns")
        self.assertEqual(200, status)
        self.assertEqual("model", result["mode"])
        self.assertEqual("allowed", result["output_review"])
        self.assertEqual("SYNTHETIC_EXPLICIT_DEVELOPER_ALLOW", result["reply"])
        _, system_status = self.request("/api/status")
        self.assertTrue(system_status["ready"])
        self.assertFalse(system_status["output_review_qualified"])
        self.assertFalse(system_status["clinical_qualified"])

    def test_save_opt_in_cannot_persist_a_default_quarantine_reply(self):
        code, unlocked = self.request("/api/unlock", "POST", {"passphrase": "SYNTHETIC-ONLY-TEST-PASS"}, self.csrf)
        self.assertEqual(200, code)
        auth = {**self.csrf, "X-TherapyBot-Session": unlocked["session"]}
        code, result = self.request("/api/chat", "POST", {"message": "Explain ferns", "save": True}, auth)
        self.assertEqual(200, code)
        self.assertEqual("review_hold", result["mode"])
        self.assertFalse(result["saved"])
        self.assertEqual(0, self.model.calls)
        code, history = self.request("/api/history", headers=auth)
        self.assertEqual(200, code)
        self.assertEqual([], history["messages"])

    def test_two_stuck_reviewers_do_not_hold_http_or_vault_unboundedly(self):
        """Real loopback regression; no unreviewed/late allow enters response or vault."""
        code, unlocked = self.request(
            "/api/unlock", "POST", {"passphrase": "SYNTHETIC-HANGING-REVIEWER-PASS"}, self.csrf)
        self.assertEqual(200, code)
        auth = {**self.csrf, "X-TherapyBot-Session": unlocked["session"]}
        self.model.reply = "SYNTHETIC_HUNG_REVIEWER_CANDIDATE_CANARY"
        release = threading.Event()
        two_started = threading.Event()
        started = []
        started_lock = threading.Lock()
        responses = {}
        errors = {}

        def stuck_reviewer(**_kwargs):
            with started_lock:
                started.append(1)
                if len(started) == 2:
                    two_started.set()
            release.wait(20)
            return "allow"

        self.server.output_reviewer = stuck_reviewer

        def chat_request(label, headers, save):
            try:
                responses[label] = self.request("/api/chat", "POST", {
                    "message": f"Synthetic plant question {label}", "save": save}, headers)
            except Exception as exc:
                errors[label] = repr(exc)

        a = threading.Thread(target=chat_request, args=("a", auth, True), daemon=True)
        b = threading.Thread(target=chat_request, args=("b", self.csrf, False), daemon=True)
        c = threading.Thread(target=chat_request, args=("c", self.csrf, False), daemon=True)
        d = threading.Thread(target=chat_request, args=("d", self.csrf, False), daemon=True)
        started_at = time.monotonic()
        third_fast = fourth_fast = first_two_bounded = False
        locked_during_review = False
        try:
            a.start()
            b.start()
            self.assertTrue(two_started.wait(3), "two reviewer callbacks never entered")
            c.start()
            c.join(timeout=1)
            third_fast = not c.is_alive()
            self.assertEqual(2, self.model.calls, "saturated requests must skip model inference")

            status, _ = self.request("/api/lock", "POST", {}, auth)
            locked_during_review = status == 200
            a.join(timeout=3.5)
            b.join(timeout=3.5)
            first_two_bounded = not a.is_alive() and not b.is_alive()
            d.start()
            d.join(timeout=1)
            fourth_fast = not d.is_alive()
            self.assertEqual(2, self.model.calls, "timed-out reviewers must retain capacity")
        finally:
            release.set()
            for thread in (a, b, c, d):
                if thread.ident is not None:
                    thread.join(timeout=5)

        self.assertTrue(third_fast, "third request waited for occupied callback slots")
        self.assertTrue(fourth_fast, "after deadline, active callbacks lost their held slots")
        self.assertTrue(first_two_bounded, "reviewer wait occupied HTTP handler indefinitely")
        self.assertTrue(locked_during_review, "unrelated vault lock was blocked")
        self.assertLess(time.monotonic() - started_at, 12)
        self.assertEqual({}, errors)
        self.assertEqual(2, len(started))
        self.assertEqual({"a", "b", "c", "d"}, set(responses))
        for status, result in responses.values():
            self.assertEqual(200, status)
            self.assertEqual("review_hold", result["mode"])
            self.assertEqual("quarantined", result["output_review"])
            self.assertFalse(result["saved"])
            self.assertNotIn(self.model.reply, json.dumps(result))
        self.assertEqual(0, self.server.vault.db.execute("SELECT COUNT(*) FROM records").fetchone()[0])

        # Once the developer releases the callbacks, capacity can recover.
        self.server.output_reviewer = lambda **_kwargs: "allow"
        for _ in range(20):
            recovered_status, recovered = self.chat("Synthetic recovered plant question")
            if recovered["mode"] == "model":
                break
            time.sleep(0.05)
        self.assertEqual(200, recovered_status)
        self.assertEqual("model", recovered["mode"])


if __name__ == "__main__":
    unittest.main()
