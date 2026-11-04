"""Curated, link-only evidence metadata, safe for offline keyword retrieval."""

import json
import ipaddress
import re
from pathlib import Path
from urllib.parse import urlsplit


SOURCES_PATH = Path(__file__).parent / "sources.json"
RESEARCH_PATH = Path(__file__).parent.parent / "research" / "sources.json"
_ID = re.compile(r"[a-z0-9][a-z0-9._-]{0,99}\Z")
_URLS_IN_TEXT = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
_REQUIRED_TEXT = ("id", "title", "issuer", "date", "retrieved", "type",
                  "url", "summary", "limitations", "rights")


def _safe_text(value, *, length=4000):
    """Reject source metadata that could break line-based local-model context."""
    return (isinstance(value, str) and 0 < len(value.strip()) <= length
            and not any(ord(char) < 32 or ord(char) == 127 for char in value))


def _safe_public_link(url):
    """A reference is a public HTTPS pointer, never a local or executable URL."""
    if not _safe_text(url, length=2048) or any(char.isspace() for char in url):
        return False
    try:
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or not parsed.hostname or
                parsed.username is not None or parsed.password is not None or
                parsed.fragment or parsed.port not in (None, 443)):
            return False
        host = parsed.hostname.lower().rstrip(".")
        if host == "localhost" or host.endswith(".localhost") or "." not in host:
            return False
        try:
            ipaddress.ip_address(host)
        except ValueError:
            return True
        return False  # Raw IP addresses are not needed in the curated bibliography.
    except ValueError:
        return False


def _validated(item):
    """Fail closed on malformed checked-in bibliography; do not launder it to the model."""
    if not isinstance(item, dict):
        raise ValueError("Source metadata must be an object")
    if not all(_safe_text(item.get(key)) for key in _REQUIRED_TEXT):
        raise ValueError("Source metadata is missing or contains unsafe text")
    if not _ID.fullmatch(item["id"]) or not _safe_public_link(item["url"]):
        raise ValueError("Source must have a stable ID and public HTTPS URL")
    topics = item.get("topics")
    if (not isinstance(topics, list) or len(topics) > 64 or
            not all(_safe_text(topic, length=100) for topic in topics)):
        raise ValueError("Source topics must be a bounded list of strings")
    return item


def _load(path):
    records = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("Source register must be a list")
    return [_validated(record) for record in records]


def sources():
    items = _load(SOURCES_PATH)
    if RESEARCH_PATH.is_file():
        # Only checked-in source metadata/original summaries, never private
        # documents or third-party article bodies, enter this retrieval path.
        ids = {item["id"] for item in items}
        urls = {item["url"].rstrip("/").lower() for item in items}
        for item in _load(RESEARCH_PATH):
            canonical_url = item["url"].rstrip("/").lower()
            if item["id"] in ids and canonical_url not in urls:
                raise ValueError("Conflicting source identifier and URL")
            if item["id"] not in ids and canonical_url not in urls:
                items.append(item)
                ids.add(item["id"])
                urls.add(canonical_url)
    return items


def audit_reference_links(reply, evidence):
    """Allowlist literal URLs against supplied metadata, NOT factual claim support.

    This intentionally cannot verify that a sentence follows from any source.
    A caller must not promote `all_links_from_context` to semantic grounding.
    """
    if not isinstance(reply, str):
        raise ValueError("Reply must be text")
    allowed = {_validated(source)["url"] for source in evidence}
    links = [url.rstrip(".,;:!?)") for url in _URLS_IN_TEXT.findall(reply)]
    provided = sorted({url for url in links if url in allowed})
    unknown = sorted({url for url in links if url not in allowed})
    return {"provided_urls": provided, "unprovided_urls": unknown,
            "all_links_from_context": not unknown,
            "claim_support_verified": False}


def search(query, limit=3):
    words = set(re.findall(r"[a-z]{3,}", str(query).lower()))
    if not words:
        return []
    ranked = []
    for src in sources():
        def terms(value):
            return set(re.findall(r"[a-z]{3,}", value.lower()))

        score = (3 * len(words & terms(src["title"]))
                 + 2 * len(words & terms(" ".join(src["topics"])))
                 + len(words & terms(src["summary"])))
        if score:
            ranked.append((score, src))
    return [item for _, item in sorted(ranked, key=lambda pair: -pair[0])[:limit]]
