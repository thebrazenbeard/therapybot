"""Offline claim-to-source metadata audit; never a clinical fact-checker.

Schema:
    claims = [{"id": str, "text": str, "references": [
        {"source_id": str, "url": str, "section": str?, "excerpt": str?}]}]

The caller supplies approved bibliography metadata separately. A matching source
ID and literal URL proves *only* that the source appears in that register. The
checker cannot determine whether an excerpt is genuine, whether a paper supports
a sentence, whether publisher rights permit reuse, or whether a human reviewed
the claim. No network access or model inference occurs here.
"""

import ipaddress
import re
import socket
from urllib.parse import urlsplit


_HOST = re.compile(r"[a-z0-9.-]+\Z")
_LOCAL_SUFFIXES = (".localhost", ".local", ".lan", ".internal", ".home.arpa",
                   ".localdomain", ".nip.io", ".sslip.io", ".xip.io")


def _text(value, max_length):
    return (isinstance(value, str) and 0 < len(value.strip()) <= max_length
            and not any(ord(char) < 32 or ord(char) == 127 for char in value))


def _public_https(url):
    if not _text(url, 2048) or any(char.isspace() for char in url):
        return False
    try:
        parsed = urlsplit(url)
        hostname = (parsed.hostname or "").lower().rstrip(".")
        port = parsed.port
    except ValueError:
        return False
    if (parsed.scheme != "https" or parsed.username or parsed.password
            or port not in (None, 443) or not _HOST.fullmatch(hostname)
            or "." not in hostname or hostname == "localhost"
            or any(hostname.endswith(suffix) for suffix in _LOCAL_SUFFIXES)):
        return False
    # Treat *all* raw IPs as untrusted attribution endpoints, whether publicly
    # routable or RFC1918. No DNS/network resolution occurs in this checker;
    # DNS aliases/rebinding beyond common known suffixes remain unverified.
    try:
        ipaddress.ip_address(hostname)
        return False
    except ValueError:
        pass
    # Legacy URL/network stacks may interpret shortened, octal or hex dotted
    # forms as IPv4 even though ipaddress rejects them as noncanonical. This
    # conversion is local syntax parsing only; it performs no DNS lookup.
    try:
        socket.inet_aton(hostname)
        return False
    except OSError:
        return True


def audit_claim_references(claims, source_records):
    """Check declared reference identity; always withhold semantic support claims.

    Raises ValueError for structurally invalid declarations, never for a merely
    unknown or mismatched reference, which is reported visibly for review.
    Returned section/excerpt flags mean *supplied by caller*, not independently
    located or verified in any publication.
    """
    if not isinstance(claims, list) or not 1 <= len(claims) <= 50:
        raise ValueError("Provide 1 to 50 structured claims")
    if not isinstance(source_records, list) or len(source_records) > 1000:
        raise ValueError("Source register must be a bounded list")

    by_id = {}
    for source in source_records:
        if (not isinstance(source, dict) or not _text(source.get("id"), 100)
                or not _public_https(source.get("url"))):
            raise ValueError("Source register contains invalid attribution metadata")
        if source["id"] in by_id:
            raise ValueError("Duplicate source identity in attribution register")
        by_id[source["id"]] = source["url"]

    assessments = []
    seen_claim_ids = set()
    for claim in claims:
        if (not isinstance(claim, dict) or set(claim) != {"id", "text", "references"}
                or not _text(claim.get("id"), 100) or not _text(claim.get("text"), 2000)
                or not isinstance(claim.get("references"), list)
                or len(claim["references"]) > 8):
            raise ValueError("Invalid claim declaration")
        if claim["id"] in seen_claim_ids:
            raise ValueError("Duplicate claim identity")
        seen_claim_ids.add(claim["id"])
        refs = []
        for ref in claim["references"]:
            if not isinstance(ref, dict) or not {"source_id", "url"} <= set(ref) or not set(ref) <= {
                    "source_id", "url", "section", "excerpt"}:
                raise ValueError("Invalid reference declaration")
            if not _text(ref.get("source_id"), 100) or not _public_https(ref.get("url")):
                raise ValueError("Invalid reference identity or URL")
            for optional, cap in (("section", 200), ("excerpt", 600)):
                if optional in ref and not _text(ref[optional], cap):
                    raise ValueError("Invalid reference detail")
            refs.append({
                "source_id": ref["source_id"],
                "metadata_match": by_id.get(ref["source_id"]) == ref["url"],
                "section_supplied": "section" in ref,
                "excerpt_supplied": "excerpt" in ref,
                "claim_support_verified": False,
            })
        assessments.append({
            "claim_id": claim["id"],
            "references": refs,
            "all_references_metadata_matched": bool(refs) and all(
                ref["metadata_match"] for ref in refs),
            "claim_support_verified": False,
            "independent_review_required": True,
        })

    return {
        "assurance_level": "metadata-only",
        "catalog_authority": "caller-supplied-unverified",
        "catalog_authenticated": False,
        "claims": assessments,
        "all_claims_metadata_matched": all(
            claim["all_references_metadata_matched"] for claim in assessments),
        "claim_support_verified": False,
    }
