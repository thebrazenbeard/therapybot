"""Loopback-only HTTP app. Browser UI and API run on the same local origin."""

from __future__ import annotations

import json
import re
import secrets
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .backup import BackupError, create_backup
from .knowledge import search_sources
from .model import ModelUnavailable, complete, local_model_url
from .safety import urgent_reply
from .vault import LockedError, Vault, WrongPassphrase

WEB_ROOT = Path(__file__).resolve().parent.parent / "web"
MAX_BODY = 256 * 1024  # 16 prior messages x 8KB plus the current message and JSON overhead


def create_server(db_path: str | Path, model_url: str | None = None, port: int = 0) -> ThreadingHTTPServer:
    """Return an unstarted loopback server. Caller owns shutdown/server_close."""
    model_origin = local_model_url(model_url)
    vault = Vault(db_path)
    server = ThreadingHTTPServer(("127.0.0.1", port), TherapyHandler)
    server.daemon_threads = True
    server.vault = vault
    server.model_url = model_origin
    server.csrf_token = secrets.token_urlsafe(32)
    server.auth_lock = threading.Lock()
    return server


class TherapyHandler(BaseHTTPRequestHandler):
    server_version = "TherapyBotLocal/0.1"
    sys_version = ""

    def log_message(self, format, *args):
        # Never log requests, paths, IPs, bodies, search terms or responses.
        return

    def _send(self, status: int, content: bytes, mime: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
        self.end_headers()
        try:
            self.wfile.write(content)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _json(self, status: int, payload: dict | list) -> None:
        self._send(status, json.dumps(payload, ensure_ascii=False).encode(), "application/json; charset=utf-8")

    def _fail(self, status: int, message: str) -> None:
        self._json(status, {"error": message})

    def _valid_host(self) -> bool:
        expected = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
        return self.headers.get("Host") in expected

    def _valid_origin(self) -> bool:
        origin = self.headers.get("Origin")
        return not origin or origin in {f"http://127.0.0.1:{self.server.server_port}",
                                        f"http://localhost:{self.server.server_port}"}

    def _body(self) -> dict:
        if self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json":
            raise ValueError("Content-Type must be application/json.")
        try:
            size = int(self.headers.get("Content-Length", "-1"))
        except ValueError as exc:
            raise ValueError("Invalid content length.") from exc
        if not 0 <= size <= MAX_BODY:
            raise ValueError("Request is too large or missing content length.")
        body = json.loads(self.rfile.read(size))
        if not isinstance(body, dict):
            raise ValueError("Expected a JSON object.")
        return body

    def do_GET(self):
        if not self._valid_host():
            return self._fail(403, "Invalid host.")
        route = urlsplit(self.path)
        if route.path in {"/", "/index.html", "/app.js", "/style.css"}:
            filename = {"/": "index.html", "/index.html": "index.html", "/app.js": "app.js", "/style.css": "style.css"}[route.path]
            path = WEB_ROOT / filename
            if not path.is_file():
                return self._fail(404, "Interface file missing.")
            raw = path.read_bytes()
            mime = {"index.html": "text/html; charset=utf-8", "app.js": "text/javascript; charset=utf-8", "style.css": "text/css; charset=utf-8"}[filename]
            return self._send(200, raw, mime)
        if route.path == "/api/status":
            return self._json(200, {"unlocked": self.server.vault.unlocked,
                                    "model_configured": bool(self.server.model_url),
                                    "model_url": self.server.model_url or "Not configured",
                                    "storage": "AES-256-GCM encrypted records (metadata not encrypted)",
                                    "notice": "Experimental support, not clinical care. No external data transfer by TherapyBot."})
        if route.path == "/api/session":
            if self.headers.get("X-TherapyBot-Token") != self.server.csrf_token:
                return self._fail(403, "Missing or invalid app token.")
            return self._json(200, {"unlocked": self.server.vault.unlocked})
        if route.path == "/api/sources":
            q = parse_qs(route.query).get("q", [""])[0][:200]
            return self._json(200, {"sources": search_sources(q, limit=8)})
        if route.path == "/api/backup":
            if self.headers.get("X-TherapyBot-Token") != self.server.csrf_token:
                return self._fail(403, "Missing or invalid app token.")
            try:
                encrypted = create_backup(self.server.vault)
                return self._send(200, encrypted, "application/octet-stream")
            except LockedError as exc:
                return self._fail(423, str(exc))
            except BackupError as exc:
                return self._fail(400, str(exc))
        if route.path in {"/api/records", "/api/export"}:
            if self.headers.get("X-TherapyBot-Token") != self.server.csrf_token:
                return self._fail(403, "Missing or invalid app token.")
            try:
                if route.path == "/api/export":
                    return self._json(200, {"format": "therapybot-plaintext-export-v1",
                                            "warning": "This export is plaintext. Secure or delete exported copies yourself.",
                                            "records": self.server.vault.export()})
                qs = parse_qs(route.query)
                kind = qs.get("kind", [None])[0]
                query = qs.get("q", [None])[0]
                if query and len(query) > 200:
                    return self._fail(400, "Search query too long.")
                return self._json(200, {"records": self.server.vault.list(kind=kind, query=query)})
            except LockedError as exc:
                return self._fail(423, str(exc))
            except ValueError as exc:
                return self._fail(400, str(exc))
        return self._fail(404, "Unknown route.")

    def do_POST(self):
        if not self._valid_host() or not self._valid_origin():
            return self._fail(403, "Request must originate from this local app.")
        if self.headers.get("X-TherapyBot-Token") != self.server.csrf_token:
            return self._fail(403, "Missing or invalid app token.")
        route = urlsplit(self.path).path
        try:
            data = self._body()
            if route == "/api/vault":
                self.server.vault.unlock(data.get("passphrase"))
                with self.server.auth_lock:
                    self.server.csrf_token = secrets.token_urlsafe(32)
                    new_token = self.server.csrf_token
                return self._json(200, {"unlocked": True, "token": new_token})
            if route == "/api/lock":
                self.server.vault.lock()
                with self.server.auth_lock:
                    self.server.csrf_token = secrets.token_urlsafe(32)
                    new_token = self.server.csrf_token
                return self._json(200, {"unlocked": False, "token": new_token})
            if route == "/api/journal":
                self.server.vault._require_key()
                body = data.get("text")
                mood = data.get("mood")
                if not isinstance(body, str) or not body.strip() or len(body) > 16000:
                    raise ValueError("Journal entry must be 1–16000 characters.")
                if mood is not None and (isinstance(mood, bool) or not isinstance(mood, (int, float)) or not 0 <= mood <= 10):
                    raise ValueError("Mood must be between 0 and 10.")
                rid = self.server.vault.add("journal", {"text": body.strip(), "mood": mood})
                return self._json(200, {"id": rid})
            if route == "/api/delete":
                record_id = data.get("id")
                if not isinstance(record_id, str) or not re.fullmatch(r"[0-9a-f]{32}", record_id):
                    raise ValueError("Invalid record ID.")
                return self._json(200, {"deleted": self.server.vault.delete(record_id)})
            if route == "/api/chat":
                text = data.get("text")
                style = data.get("style", "direct")
                depth = data.get("depth", "balanced")
                save_history = data.get("save_history", False)
                history = data.get("history", [])
                if not isinstance(text, str) or not text.strip() or len(text) > 8000:
                    raise ValueError("Message must be 1–8000 characters.")
                if style not in {"direct", "warm", "analytical"} or depth not in {"brief", "balanced", "detailed"}:
                    raise ValueError("Unsupported communication preference.")
                if not isinstance(save_history, bool):
                    raise ValueError("save_history must be a boolean.")
                if not isinstance(history, list) or len(history) > 16 or any(
                    not isinstance(item, dict) or item.get("role") not in {"user", "assistant"}
                    or not isinstance(item.get("text"), str) or len(item["text"]) > 8000 for item in history
                ):
                    raise ValueError("Invalid in-memory conversation history.")
                text = text.strip()
                sources = search_sources(text)
                intervention = urgent_reply(text)
                if intervention:
                    reply, mode = intervention, "safety"
                else:
                    self.server.vault._require_key()
                    messages = [{"role": item["role"], "content": item["text"]} for item in history]
                    messages.append({"role": "user", "content": text})
                    reply = complete(self.server.model_url, messages, sources, style, depth)
                    if re.search(r"\bI (?:have )?(?:called|contacted) (?:911|emergency services|your doctor)\b", reply, re.I):
                        raise ModelUnavailable("Model claimed to contact external help; response suppressed.")
                    known_ids = {source["id"] for source in sources}
                    reply = re.sub(
                        r"\[([a-z][a-z0-9_-]{2,60})\]",
                        lambda match: match.group(0) if match.group(1) in known_ids else "[unverified citation omitted]",
                        reply,
                    )
                    mode = "local-model"
                persisted = save_history and self.server.vault.unlocked
                if persisted:
                    self.server.vault.add_many([
                        ("chat", {"role": "user", "text": text}),
                        ("chat", {"role": "assistant", "text": reply,
                                  "sources": [s["id"] for s in sources], "mode": mode}),
                    ])
                return self._json(200, {"reply": reply,
                                        "sources": [{"id": s["id"], "title": s["title"], "url": s["url"]} for s in sources],
                                        "mode": mode, "saved": persisted})
            return self._fail(404, "Unknown route.")
        except LockedError as exc:
            return self._fail(423, str(exc))
        except WrongPassphrase as exc:
            return self._fail(401, str(exc))
        except ModelUnavailable as exc:
            return self._fail(503, str(exc))
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            return self._fail(400, str(exc))
