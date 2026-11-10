"""Real-loopback request-body availability tests with synthetic content only.

These bound one class of stalled local handler; they are not a global DoS test.
"""

import json
import select
import socket
import tempfile
import threading
import time
import unittest
import urllib.request
from pathlib import Path
from unittest.mock import patch

from therapybot import app


class SyntheticModel:
    url = "http://127.0.0.1:1/v1/chat/completions"
    model_name = "synthetic-only"

    def generate(self, *args, **kwargs):
        return "SYNTHETIC_ONLY_RESPONSE"


class HttpBodyDeadlineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="therapybot-body-deadline-")
        self.addCleanup(self.temp.cleanup)
        self.server = app.create_server(0, str(Path(self.temp.name) / "synthetic.sqlite3"))
        self.server.model = SyntheticModel()
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close)

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.server.vault.close()
        self.thread.join(timeout=2)

    def partial_client(self, initial=b"{"):
        sock = socket.create_connection(("127.0.0.1", self.server.server_port), timeout=2)
        sock.settimeout(2)
        request = (
            "POST /api/journal HTTP/1.1\r\n"
            f"Host: 127.0.0.1:{self.server.server_port}\r\n"
            "Content-Type: application/json\r\n"
            f"X-TherapyBot-Token: {self.server.csrf}\r\n"
            "Content-Length: 48000\r\n"
            "Connection: close\r\n\r\n"
        ).encode("ascii")
        sock.sendall(request + initial)
        self.addCleanup(sock.close)
        return sock

    def assert_deadline_response(self, sock, max_seconds=1.1):
        start = time.monotonic()
        ready, _, _ = select.select([sock], [], [], max_seconds)
        self.assertTrue(ready, "partial request left handler reading beyond its total deadline")
        response = sock.recv(4096)
        self.assertIn(b"HTTP/1.0 408", response, "stalled body should receive 408 Request Timeout")
        self.assertLess(time.monotonic() - start, max_seconds)

    def test_partial_body_timeout_releases_handler(self):
        # `create=True` lets the test fail against the unfixed implementation,
        # whose `_body` ignores the future deadline setting entirely.
        with patch.object(app, "HTTP_BODY_READ_TIMEOUT_SECONDS", 0.3, create=True):
            self.assert_deadline_response(self.partial_client(), max_seconds=1.1)

    def test_slow_trickle_cannot_extend_absolute_deadline(self):
        with patch.object(app, "HTTP_BODY_READ_TIMEOUT_SECONDS", 0.3, create=True):
            sock = self.partial_client(initial=b"{")
            stop = threading.Event()

            def keep_trickling():
                while not stop.wait(0.08):
                    try:
                        sock.sendall(b" ")
                    except OSError:
                        return

            producer = threading.Thread(target=keep_trickling, daemon=True)
            producer.start()
            try:
                self.assert_deadline_response(sock, max_seconds=1.1)
            finally:
                stop.set()
                producer.join(timeout=1)

    def test_multiple_partial_clients_expire_independently(self):
        with patch.object(app, "HTTP_BODY_READ_TIMEOUT_SECONDS", 0.3, create=True):
            clients = [self.partial_client() for _ in range(5)]
            pending = set(clients)
            cutoff = time.monotonic() + 1.3
            while pending and time.monotonic() < cutoff:
                ready, _, _ = select.select(list(pending), [], [], max(0, cutoff - time.monotonic()))
                for sock in ready:
                    self.assertIn(b"HTTP/1.0 408", sock.recv(4096))
                    pending.remove(sock)
            self.assertFalse(pending, "stalled requests retained handler threads")

    def test_vault_lock_stays_live_during_partial_body_reads(self):
        def post(path, payload, session=None):
            raw = json.dumps(payload).encode("utf-8")
            headers = {"Content-Type": "application/json", "X-TherapyBot-Token": self.server.csrf}
            if session:
                headers["X-TherapyBot-Session"] = session
            req = urllib.request.Request(
                f"http://127.0.0.1:{self.server.server_port}{path}",
                data=raw, method="POST", headers=headers,
            )
            with urllib.request.urlopen(req, timeout=2) as response:
                return response.status, json.load(response)

        status, unlocked = post("/api/unlock", {"passphrase": "synthetic-passphrase-0001"})
        self.assertEqual(200, status)
        with patch.object(app, "HTTP_BODY_READ_TIMEOUT_SECONDS", 0.75, create=True):
            clients = [self.partial_client() for _ in range(8)]
            start = time.monotonic()
            status, locked = post("/api/lock", {}, session=unlocked["session"])
            self.assertEqual((200, "locked"), (status, locked["storage"]))
            self.assertLess(time.monotonic() - start, 0.55, "stalled bodies delayed vault lock")
            # The deliberate incomplete uploads must still expire after lock.
            cutoff = time.monotonic() + 1.3
            pending = set(clients)
            while pending and time.monotonic() < cutoff:
                ready, _, _ = select.select(list(pending), [], [], max(0, cutoff - time.monotonic()))
                for sock in ready:
                    self.assertIn(b"HTTP/1.0 408", sock.recv(4096))
                    pending.remove(sock)
            self.assertFalse(pending, "partial handlers outlived body deadline after vault lock")

    def test_valid_near_limit_body_still_succeeds(self):
        # This test isolates HTTP framing/size, not generated-output review.
        # Explicit developer reviewer activates the synthetic model path;
        # production default remains a no-generation quarantine.
        self.server.output_reviewer = lambda **_kwargs: "allow"
        payload = {"message": "synthetic question", "save": False, "context": ["S" * 47000]}
        raw = json.dumps(payload).encode("utf-8")
        self.assertGreater(len(raw), 47000)
        self.assertLessEqual(len(raw), app.MAX_BODY)
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.server.server_port}/api/chat",
            data=raw,
            method="POST",
            headers={"Content-Type": "application/json", "X-TherapyBot-Token": self.server.csrf},
        )
        with urllib.request.urlopen(req, timeout=4) as response:
            self.assertEqual(200, response.status)
            self.assertEqual("SYNTHETIC_ONLY_RESPONSE", json.load(response)["reply"])


if __name__ == "__main__":
    unittest.main()
