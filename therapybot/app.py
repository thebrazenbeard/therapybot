"""Loopback-only local web application. No telemetry, accounts, or cloud fallback."""

import json
import os
import secrets
import socket
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import __version__
from .knowledge import search as source_search, sources
from .model import ModelClient, ModelError
from .safety import CONCERN_PREFIX, IMMEDIATE_RESPONSE, classify
from .storage import Vault, VaultError


STATIC = Path(__file__).resolve().parent.parent / "static"
EMBEDDED = Path(__file__).resolve().parent.parent / "embedded"
EMBEDDED_ASSETS = {
    "index.html": "text/html; charset=utf-8",
    "style.css": "text/css; charset=utf-8",
    "catalog.js": "text/javascript; charset=utf-8",
    "engine.js": "text/javascript; charset=utf-8",
    "council.js": "text/javascript; charset=utf-8",
    "conversation_adapter.js": "text/javascript; charset=utf-8",
    "ui.js": "text/javascript; charset=utf-8",
    "manifest.json": "application/json; charset=utf-8",
}
# The bundled Council is a separate volatile client. It does not access the
# encrypted vault or the local GGUF API, and must not submit HTML forms.
EMBEDDED_CSP = (
    "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
    "connect-src 'none'; form-action 'none'; frame-ancestors 'none'; "
    "base-uri 'none'; object-src 'none'"
)
MAX_BODY = 48_000


class AppServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, address, vault, model):
        if address[0] != "127.0.0.1":
            raise ValueError("TherapyBot only binds to 127.0.0.1")
        self.vault = vault
        self.model = model
        self.csrf = secrets.token_urlsafe(32)
        self.session = None  # Issued only after a correct vault passphrase.
        self.model_responded = False  # Only true after this process observed a reply.
        super().__init__(address, Handler)


class Handler(BaseHTTPRequestHandler):
    server_version = "TherapyBot/0.1"
    sys_version = ""

    def log_message(self, *args):
        # URLs and messages might be personal. Intentionally no request logs.
        return

    def _headers(self, code, content_type, length, extra=None, csp=None):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", csp or "default-src 'self'; connect-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        for name, val in (extra or {}).items():
            self.send_header(name, val)
        self.end_headers()

    def _bytes(self, data, content_type="application/octet-stream", code=200, extra=None, csp=None):
        self._headers(code, content_type, len(data), extra, csp)
        self.wfile.write(data)

    def _json(self, data, code=200):
        self._bytes(json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8", code)

    def _error(self, code, message):
        self._json({"error": message}, code)

    def _authorized_origin(self):
        host = self.headers.get("Host", "")
        allowed = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
        if host not in allowed:
            self._error(403, "Invalid local host")
            return False
        origin = self.headers.get("Origin")
        if origin and origin != "http://" + host:
            self._error(403, "Cross-origin requests are not allowed")
            return False
        return True

    def _authorized_mutation(self):
        if self.headers.get("X-TherapyBot-Token") != self.server.csrf:
            self._error(403, "Missing or invalid local request token")
            return False
        return True

    def _authorized_session(self):
        if not self.server.vault.unlocked or not self.server.session or not secrets.compare_digest(self.headers.get("X-TherapyBot-Session", ""), self.server.session):
            self._error(403, "Unlock your local vault in this browser session")
            return False
        return True

    def _body(self):
        if self.headers.get("Content-Type", "").split(";")[0].strip().lower() != "application/json":
            raise ValueError("Expected application/json")
        try:
            n = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("Invalid request size") from exc
        if n < 2 or n > MAX_BODY:
            raise ValueError("Request must be between 2 and 48000 bytes")
        data = json.loads(self.rfile.read(n))
        if not isinstance(data, dict):
            raise ValueError("Expected a JSON object")
        return data

    def _model_ready(self):
        endpoint = urllib.parse.urlsplit(self.server.model.url)
        try:
            with socket.create_connection((endpoint.hostname, endpoint.port), timeout=0.25):
                return True
        except OSError:
            return False

    def do_GET(self):
        if not self._authorized_origin():
            return
        parsed = urllib.parse.urlsplit(self.path)
        path = parsed.path
        try:
            if path in ("/", "/index.html"):
                raw = (STATIC / "index.html").read_text(encoding="utf-8").replace("{{CSRF_TOKEN}}", self.server.csrf)
                self._bytes(raw.encode("utf-8"), "text/html; charset=utf-8")
            elif path in ("/embedded", "/embedded/") or path.startswith("/embedded/"):
                asset = "index.html" if path in ("/embedded", "/embedded/") else path[len("/embedded/"):]
                if parsed.query or asset not in EMBEDDED_ASSETS:
                    self._error(404, "Not found")
                    return
                self._bytes((EMBEDDED / asset).read_bytes(), EMBEDDED_ASSETS[asset], csp=EMBEDDED_CSP)
            elif path == "/api/status":
                endpoint_reachable = self._model_ready()
                self._json({"version": __version__, "storage": "unlocked" if self.server.vault.unlocked else "locked", "initialized": self.server.vault.initialized,
                            "endpoint_reachable": endpoint_reachable, "ready": endpoint_reachable and self.server.model_responded,
                            "model": self.server.model.url, "model_name": self.server.model.model_name, "source_count": len(sources()),
                            "persistence_default": False, "local_only": True})
            elif path == "/api/sources":
                self._json({"sources": sources()})
            elif path == "/api/history":
                if not self._authorized_session():
                    return
                history = self.server.vault.list("chat")
                self._json({"messages": [{"id": r["id"], "created_at": r["created_at"], **r["content"]} for r in reversed(history)]})
            elif path == "/api/journal":
                if not self._authorized_session():
                    return
                self._json({"entries": self.server.vault.list("journal")})
            elif path == "/api/search":
                if not self._authorized_session():
                    return
                q = urllib.parse.parse_qs(parsed.query).get("q", [""])[0][:200]
                self._json({"results": self.server.vault.search(q)})
            elif path == "/api/backup":
                if not self._authorized_mutation() or not self._authorized_session():
                    return
                blob = self.server.vault.backup()
                self._bytes(blob, "application/x-sqlite3", extra={"Content-Disposition": 'attachment; filename="therapybot-encrypted-backup.sqlite3"'})
            elif path == "/api/safety-resources":
                self._json({"us": "In the United States, call or text 988 for crisis support. If danger is immediate, call emergency services.", "url": "https://988lifeline.org/get-help/"})
            elif path == "/favicon.ico":
                self._bytes(b"", "image/x-icon", 204)
            else:
                self._error(404, "Not found")
        except VaultError as exc:
            self._error(423, str(exc))
        except (ValueError, OSError) as exc:
            self._error(500, "Local operation failed")

    def do_POST(self):
        if not self._authorized_origin() or not self._authorized_mutation():
            return
        try:
            data = self._body()
            if self.path == "/api/unlock":
                self.server.vault.unlock(data.get("passphrase"))
                self.server.session = secrets.token_urlsafe(32)
                self._json({"storage": "unlocked", "session": self.server.session})
            elif self.path == "/api/lock":
                if not self._authorized_session():
                    return
                self.server.vault.lock()
                self.server.session = None
                self._json({"storage": "locked"})
            elif self.path == "/api/chat":
                msg = data.get("message")
                if not isinstance(msg, str) or not msg.strip() or len(msg) > 8000:
                    raise ValueError("Message must contain 1 to 8000 characters")
                save = data.get("save", False)
                if not isinstance(save, bool):
                    raise ValueError("Save must be a boolean")
                if save and not self.server.vault.unlocked:
                    raise VaultError("Unlock your vault to save chat records")
                if save and not self._authorized_session():
                    return
                context = data.get("context") if isinstance(data.get("context"), list) else []
                safety = classify(msg, context)
                citations = source_search(msg)
                if safety == "immediate":
                    reply, mode = IMMEDIATE_RESPONSE, "safety"
                else:
                    try:
                        reply = self.server.model.generate(msg, data.get("style", "direct"), data.get("depth", "balanced"), context, citations)
                        self.server.model_responded = True
                        mode = "model"
                    except ModelError:
                        if safety != "concern":
                            self._error(503, "Local model unavailable. Configure and start KoboldCPP or llama.cpp; no cloud fallback was used.")
                            return
                        reply, mode = "I couldn't reach your local model. " + CONCERN_PREFIX.strip(), "safety"
                    if safety == "concern" and mode == "model":
                        reply = CONCERN_PREFIX + reply
                if save:
                    self.server.vault.add("chat", {"user": msg, "assistant": reply})
                self._json({"reply": reply, "mode": mode, "safety": safety, "citations": [{"title": c["title"], "url": c["url"]} for c in citations]})
            elif self.path == "/api/journal":
                if not self._authorized_session():
                    return
                body = data.get("text")
                mood = data.get("mood")
                if not isinstance(body, str) or not body.strip() or len(body) > 12000:
                    raise ValueError("Journal entry must contain 1 to 12000 characters")
                if mood is not None and (type(mood) is not int or not 0 <= mood <= 10):
                    raise ValueError("Mood must be an integer from 0 to 10")
                rid = self.server.vault.add("journal", body, mood)
                self._json({"id": rid}, 201)
            else:
                self._error(404, "Not found")
        except VaultError as exc:
            self._error(423, str(exc))
        except (ValueError, json.JSONDecodeError) as exc:
            self._error(400, str(exc))
        except OSError:
            self._error(500, "Local operation failed")

    def do_DELETE(self):
        if not self._authorized_origin() or not self._authorized_mutation():
            return
        try:
            if self.path != "/api/records":
                return self._error(404, "Not found")
            if not self._authorized_session():
                return
            if self.headers.get("X-TherapyBot-Confirm") != "DELETE":
                return self._error(400, "Deletion requires explicit confirmation")
            self._json({"deleted": self.server.vault.delete_all()})
        except VaultError as exc:
            self._error(423, str(exc))


def create_server(port=8768, database=None, model_url=None, model_name=None):
    database = database or os.environ.get("THERAPYBOT_DB", str(Path.home() / ".therapybot" / "vault.sqlite3"))
    return AppServer(("127.0.0.1", int(port)), Vault(database), ModelClient(model_url, model_name=model_name))


def main():
    import argparse
    import webbrowser
    parser = argparse.ArgumentParser(description="TherapyBot local prototype")
    parser.add_argument("--port", type=int, default=8768)
    parser.add_argument("--database", help="Local SQLite encrypted-vault path")
    parser.add_argument("--model-url", help="Local KoboldCPP or llama.cpp endpoint")
    parser.add_argument("--model-name", help="Model ID for OpenAI-compatible local endpoints")
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    server = create_server(args.port, args.database, args.model_url, args.model_name)
    url = f"http://127.0.0.1:{server.server_port}/"
    print(f"TherapyBot experimental local support UI: {url}", flush=True)
    print("No telemetry, cloud inference, or background data upload. This is not emergency or licensed clinical care.", flush=True)
    if not args.no_browser:
        threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever(poll_interval=0.1)
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.vault.close()
        server.server_close()


if __name__ == "__main__":
    main()
