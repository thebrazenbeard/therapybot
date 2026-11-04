"""Local-only OpenAI-compatible adapter for KoboldCPP and llama.cpp servers."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from .safety import SYSTEM_PROMPT


class ModelUnavailable(RuntimeError):
    pass


def local_model_url(base: str | None) -> str | None:
    if not base:
        return None
    parsed = urllib.parse.urlsplit(base)
    if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("Model endpoint must be an HTTP loopback address.")
    if parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in {"", "/"}:
        raise ValueError("Model endpoint must be a loopback origin without credentials or a path.")
    if not (parsed.port and 1 <= parsed.port <= 65535):
        raise ValueError("Supply an explicit local model port.")
    return base.rstrip("/")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ModelUnavailable("Model endpoint redirected; refusing network redirect.")


def complete(base_url: str | None, conversation: list[dict], sources: list[dict], style: str, depth: str) -> str:
    if not base_url:
        raise ModelUnavailable("No local model configured. Start KoboldCPP/llama.cpp, then relaunch with --model-url http://127.0.0.1:5001 (or your actual local port).")
    source_lines = "\n".join(f"[{s['id']}] {s['summary']} Source: {s['url']}" for s in sources)
    system = SYSTEM_PROMPT + "\nStyle: " + style + ". Depth: " + depth + ".\nReference DATA:\n" + source_lines
    messages = [{"role": "system", "content": system}]
    for entry in conversation[-16:]:
        if entry.get("role") in {"user", "assistant"} and isinstance(entry.get("content"), str):
            messages.append({"role": entry["role"], "content": entry["content"][:8000]})
    body = json.dumps({"model": "local", "messages": messages, "temperature": 0.45, "max_tokens": 750}).encode()
    request = urllib.request.Request(base_url + "/v1/chat/completions", data=body,
                                     headers={"Content-Type": "application/json"}, method="POST")
    try:
        # Never inherit HTTP_PROXY/HTTPS_PROXY from the host for private messages.
        with urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect()).open(request, timeout=50) as response:
            if response.status != 200:
                raise ModelUnavailable(f"Local model responded with HTTP {response.status}.")
            data = response.read(1_000_001)
            if len(data) > 1_000_000:
                raise ModelUnavailable("Local model response was too large.")
        payload = json.loads(data)
        result = payload["choices"][0]["message"]["content"]
        if not isinstance(result, str) or not result.strip():
            raise ValueError("Empty response")
        return result.strip()
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError, IndexError, TypeError) as exc:
        raise ModelUnavailable("Local model unavailable or returned an invalid response. Check the local server and its /v1/chat/completions endpoint.") from exc
