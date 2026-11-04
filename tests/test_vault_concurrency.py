"""Threaded localhost characterization of vault authorization transactions.

Synthetic records only.  These tests exercise the actual ThreadingHTTPServer,
not a mocked single-threaded handler or a browser-only session model.
"""

import concurrent.futures
import http.client
import json
import socket
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

from therapybot.app import Handler, create_server


class VaultConcurrencyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.server = create_server(0, str(Path(self.temp.name) / "synthetic-vault.sqlite3"))
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)
        self.addCleanup(self.close)
        code, body = self.request("POST", "/api/unlock", {"passphrase": "synthetic-passphrase-0001"})
        self.assertEqual(200, code)
        self.session_a = body["session"]

    def close(self):
        self.pool.shutdown(wait=True)
        self.server.shutdown()
        self.server.server_close()
        self.server.vault.close()
        self.thread.join(timeout=2)

    def request(self, method, path, body=None, session=None, confirm=False, binary=False, marker=None):
        payload = json.dumps(body).encode() if body is not None else None
        headers = {"Host": f"127.0.0.1:{self.server.server_port}", "X-TherapyBot-Token": self.server.csrf}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        if session:
            headers["X-TherapyBot-Session"] = session
        if confirm:
            headers["X-TherapyBot-Confirm"] = "DELETE"
        if marker:
            headers["X-TherapyBot-Test-Marker"] = marker
        req = urllib.request.Request(self.base + path, data=payload, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                raw = response.read()
                return response.status, raw if binary else json.loads(raw)
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            return exc.code, raw if binary else json.loads(raw)

    def test_overlapping_lock_unlock_never_orphans_decrypted_key(self):
        original_lock = self.server.vault.lock
        key_removed = threading.Event()
        resume_lock = threading.Event()

        def pause_after_key_removed():
            original_lock()
            key_removed.set()
            self.assertTrue(resume_lock.wait(4), "timed out waiting for test to release lock")

        self.server.vault.lock = pause_after_key_removed
        lock = self.pool.submit(self.request, "POST", "/api/lock", {}, self.session_a)
        self.assertTrue(key_removed.wait(3))
        started_unlock = threading.Event()

        def concurrent_unlock():
            started_unlock.set()
            return self.request("POST", "/api/unlock", {"passphrase": "synthetic-passphrase-0001"})

        unlock = self.pool.submit(concurrent_unlock)
        self.assertTrue(started_unlock.wait(1))
        # The unsafe implementation can issue B while A is paused.  A fixed
        # server must hold the state mutex and make B wait for A to finish.
        threading.Event().wait(0.3)
        resume_lock.set()
        lock_code, _ = lock.result(timeout=4)
        unlock_code, unlock_data = unlock.result(timeout=4)
        self.assertEqual((200, 200), (lock_code, unlock_code))
        self.assertTrue(self.server.vault.unlocked)
        self.assertEqual(unlock_data["session"], self.server.session)
        self.assertEqual(403, self.request("GET", "/api/history", session=self.session_a)[0])
        self.assertEqual(200, self.request("GET", "/api/history", session=unlock_data["session"])[0])

    def test_backup_snapshot_auth_finishes_before_lock_confirmation(self):
        code, _ = self.request("POST", "/api/journal", {"text": "SYNTHETIC_RECORD_ONLY"}, self.session_a)
        self.assertEqual(201, code)
        original_backup = self.server.vault.backup
        backup_ready = threading.Event()
        resume_backup = threading.Event()

        def pause_after_backup_bytes():
            result = original_backup()
            backup_ready.set()
            self.assertTrue(resume_backup.wait(4))
            return result

        self.server.vault.backup = pause_after_backup_bytes
        backup = self.pool.submit(self.request, "GET", "/api/backup", None, self.session_a, False, True)
        self.assertTrue(backup_ready.wait(3))
        lock_started = threading.Event()

        def do_lock():
            lock_started.set()
            return self.request("POST", "/api/lock", {}, self.session_a)

        lock = self.pool.submit(do_lock)
        self.assertTrue(lock_started.wait(1))
        threading.Event().wait(0.2)
        try:
            self.assertFalse(lock.done(), "Lock confirmation raced ahead of an authorized backup")
        finally:
            resume_backup.set()
        backup_code, backup_bytes = backup.result(timeout=4)
        lock_code, _ = lock.result(timeout=4)
        self.assertEqual((200, 200), (backup_code, lock_code))
        self.assertTrue(backup_bytes.startswith(b"SQLite format 3"))
        self.assertFalse(self.server.vault.unlocked)
        self.assertIsNone(self.server.session)

    def test_stalled_backup_socket_does_not_block_vault_lock(self):
        original_bytes = Handler._bytes
        sending_backup = threading.Event()
        resume_send = threading.Event()

        def paused_backup_send(handler, data, *args, **kwargs):
            if handler.path == "/api/backup":
                sending_backup.set()
                self.assertTrue(resume_send.wait(4))
            return original_bytes(handler, data, *args, **kwargs)

        with patch.object(Handler, "_bytes", paused_backup_send):
            backup = self.pool.submit(self.request, "GET", "/api/backup", None, self.session_a, False, True)
            self.assertTrue(sending_backup.wait(3))
            lock = self.pool.submit(self.request, "POST", "/api/lock", {}, self.session_a)
            try:
                # The encrypted snapshot exists, but the client isn't reading
                # the response. Locking must not wait on socket I/O.
                lock_code, _ = lock.result(timeout=1.5)
                self.assertEqual(200, lock_code)
                self.assertFalse(self.server.vault.unlocked)
                self.assertIsNone(self.server.session)
            finally:
                resume_send.set()
            backup_code, backup_bytes = backup.result(timeout=4)
            self.assertEqual(200, backup_code)
            self.assertTrue(backup_bytes.startswith(b"SQLite format 3"))

    def test_real_nonreading_tcp_journal_cannot_hold_vault_lock_indefinitely(self):
        # Large private plaintext responses used to hold auth_lock throughout
        # a blocking socket sendall. An authenticated local client can request
        # data and stop reading without an application-layer timeout.
        for number in range(500):
            self.server.vault.add("journal", "SYNTHETIC_JOURNAL_%03d_" % number + "X" * 11000)
        entered_response = threading.Event()
        spurious_error_response = threading.Event()
        original_bytes = Handler._bytes
        original_error = Handler._error

        def observe_response(handler, data, *args, **kwargs):
            if handler.path == "/api/journal":
                entered_response.set()
            return original_bytes(handler, data, *args, **kwargs)

        def track_error(handler, code, message):
            if handler.path == "/api/journal":
                spurious_error_response.set()
            return original_error(handler, code, message)

        with patch.object(Handler, "_bytes", observe_response), patch.object(Handler, "_error", track_error):
            slow = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            slow.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4096)
            try:
                slow.connect(("127.0.0.1", self.server.server_port))
                slow.sendall((
                    "GET /api/journal HTTP/1.1\r\n"
                    f"Host: 127.0.0.1:{self.server.server_port}\r\n"
                    f"X-TherapyBot-Session: {self.session_a}\r\n"
                    "Connection: close\r\n\r\n"
                ).encode("ascii"))
                self.assertTrue(entered_response.wait(3), "journal response never started")
                lock = self.pool.submit(self.request, "POST", "/api/lock", {}, self.session_a)
                code, _ = lock.result(timeout=3.5)
                self.assertEqual(200, code)
            finally:
                slow.close()
        self.assertFalse(self.server.vault.unlocked)
        self.assertIsNone(self.server.session)
        self.assertFalse(spurious_error_response.is_set(), "Do not attempt a second HTTP response after partial delivery")

    def test_three_stalled_private_responses_do_not_serialize_the_auth_lock(self):
        # A single slow client is insufficient: three clients could each hold
        # the mutex until their independent socket timeout (3 * 2 seconds).
        # Exercise the real threaded server and pause all sends at the I/O
        # boundary, after the private snapshots have been authorized.
        for number in range(650):
            self.server.vault.add("journal", "SYNTHETIC_JOURNAL_%03d_" % number + "X" * 11000)
        seen = set()
        seen_lock = threading.Lock()
        all_sending = threading.Event()
        release_sends = threading.Event()
        original_bytes = Handler._bytes

        def hold_private_socket_send(handler, data, *args, **kwargs):
            if handler.path == "/api/journal":
                with seen_lock:
                    seen.add(id(handler))
                    if len(seen) == 3:
                        all_sending.set()
                self.assertTrue(release_sends.wait(4), "synthetic stalled response was not released")
            return original_bytes(handler, data, *args, **kwargs)

        sockets = []
        try:
            with patch.object(Handler, "_bytes", hold_private_socket_send):
                for _ in range(3):
                    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4096)
                    sockets.append(client)
                    client.connect(("127.0.0.1", self.server.server_port))
                    client.sendall((
                        "GET /api/journal HTTP/1.1\r\n"
                        f"Host: 127.0.0.1:{self.server.server_port}\r\n"
                        f"X-TherapyBot-Session: {self.session_a}\r\n"
                        "Connection: close\r\n\r\n"
                    ).encode("ascii"))
                self.assertTrue(all_sending.wait(3), "private sends appear serialized under auth_lock")
                code, _ = self.request("POST", "/api/lock", {}, self.session_a)
                self.assertEqual(200, code)
                self.assertFalse(self.server.vault.unlocked)
                self.assertIsNone(self.server.session)
        finally:
            release_sends.set()
            for client in sockets:
                client.close()

    def test_interrupted_unlock_reply_clears_unreceived_session(self):
        original_json = Handler._json

        def interrupted_unlock(handler, data, *args, **kwargs):
            if handler.path == "/api/unlock" and isinstance(data, dict) and "session" in data:
                raise OSError("synthetic interrupted unlock response")
            return original_json(handler, data, *args, **kwargs)

        with patch.object(Handler, "_json", interrupted_unlock):
            try:
                code, _ = self.request("POST", "/api/unlock", {"passphrase": "synthetic-passphrase-0001"})
                self.assertGreaterEqual(code, 400)
            except (ConnectionError, http.client.RemoteDisconnected, urllib.error.URLError, OSError):
                pass  # Also an acceptable outcome for a failed response.
        self.assertFalse(self.server.vault.unlocked, "Failed unlock left decrypted key resident")
        self.assertIsNone(self.server.session, "Failed unlock left issued session resident")
        self.assertEqual(403, self.request("GET", "/api/history", session=self.session_a)[0])

    def test_failed_old_unlock_cannot_erase_newer_successful_session(self):
        original_json = Handler._json
        first_reply_started = threading.Event()
        resume_first_reply = threading.Event()

        def fail_first_reply(handler, data, *args, **kwargs):
            if (handler.path == "/api/unlock" and handler.headers.get("X-TherapyBot-Test-Marker") == "A"
                    and isinstance(data, dict) and "session" in data):
                first_reply_started.set()
                self.assertTrue(resume_first_reply.wait(4))
                raise OSError("synthetic first-tab response failure")
            return original_json(handler, data, *args, **kwargs)

        with patch.object(Handler, "_json", fail_first_reply):
            first = self.pool.submit(self.request, "POST", "/api/unlock",
                                     {"passphrase": "synthetic-passphrase-0001"}, marker="A")
            self.assertTrue(first_reply_started.wait(3))
            try:
                code, second = self.request("POST", "/api/unlock", {"passphrase": "synthetic-passphrase-0001"})
                self.assertEqual(200, code)
            finally:
                resume_first_reply.set()
            self.assertGreaterEqual(first.result(timeout=4)[0], 400)
        self.assertTrue(self.server.vault.unlocked)
        self.assertEqual(second["session"], self.server.session)
        self.assertEqual(200, self.request("GET", "/api/history", session=second["session"])[0])

    def test_stale_saved_chat_cannot_cross_session_rotation(self):
        # Explicit developer reviewer activates generation for this race probe.
        self.server.output_reviewer = lambda **_kwargs: "allow"
        generation_started = threading.Event()
        resume_generation = threading.Event()

        def slow_generate(*_args, **_kwargs):
            generation_started.set()
            self.assertTrue(resume_generation.wait(4))
            return "SYNTHETIC_MODEL_REPLY_ONLY"

        self.server.model.generate = slow_generate
        chat = self.pool.submit(self.request, "POST", "/api/chat", {"message": "Synthetic saved chat", "save": True}, self.session_a)
        self.assertTrue(generation_started.wait(3))
        self.assertEqual(200, self.request("POST", "/api/lock", {}, self.session_a)[0])
        code, unlocked = self.request("POST", "/api/unlock", {"passphrase": "synthetic-passphrase-0001"})
        self.assertEqual(200, code)
        resume_generation.set()
        code, _ = chat.result(timeout=4)
        self.assertEqual(403, code, "An old session must not save after a lock/reunlock epoch")
        code, history = self.request("GET", "/api/history", session=unlocked["session"])
        self.assertEqual(200, code)
        self.assertEqual([], history["messages"])

    def test_authorized_delete_finishes_before_lock_transition(self):
        code, _ = self.request("POST", "/api/journal", {"text": "SYNTHETIC_DELETE_RECORD"}, self.session_a)
        self.assertEqual(201, code)
        original_delete = self.server.vault.delete_all
        deleting = threading.Event()
        resume_delete = threading.Event()

        def pause_before_delete():
            deleting.set()
            self.assertTrue(resume_delete.wait(4))
            return original_delete()

        self.server.vault.delete_all = pause_before_delete
        deletion = self.pool.submit(self.request, "DELETE", "/api/records", None, self.session_a, True)
        self.assertTrue(deleting.wait(3))
        started_lock = threading.Event()

        def lock_during_delete():
            started_lock.set()
            return self.request("POST", "/api/lock", {}, self.session_a)

        lock = self.pool.submit(lock_during_delete)
        self.assertTrue(started_lock.wait(1))
        threading.Event().wait(0.2)
        try:
            self.assertFalse(lock.done(), "Lock must not overtake authorized private deletion")
        finally:
            resume_delete.set()
        del_code, del_result = deletion.result(timeout=4)
        lock_code, _ = lock.result(timeout=4)
        self.assertEqual((200, 200), (del_code, lock_code))
        self.assertEqual(1, del_result["deleted"])
        self.assertFalse(self.server.vault.unlocked)
        self.assertIsNone(self.server.session)


if __name__ == "__main__":
    unittest.main()
