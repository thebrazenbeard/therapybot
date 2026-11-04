"""Observe public TherapyBot Intranel review packets; never act on them.

This is an opt-in, unauthenticated GitHub *observation* tool. It does not
deliver messages to ChatGPT sessions, acknowledge them, authenticate senders,
admit requested effects, or persist/print packet payloads.

Provide the proprietary Intranel package through a permitted local checkout,
e.g. PYTHONPATH=/path/to/intranel/src python poll_therapybot.py --live.
"""

from __future__ import annotations

import argparse
import json
import re
from typing import Any, Callable
from urllib.request import Request, urlopen

REPO = "thebrazenbeard/therapybot"
ISSUE = 4
MAX_PAGE_BYTES = 2 * 1024 * 1024
MAX_COMMENT_BYTES = 256 * 1024
MAX_PACKETS_PER_COMMENT = 4
MAX_PAGES = 3
FENCE = re.compile(r"```json[ \t]*\r?\n(.*?)\r?\n```", re.I | re.S)
READ_ONLY_PERFORMATIVES = {"QUERY", "REQUEST", "REVIEW", "REPORT", "ACK", "REJECT", "WAIT", "CONFLICT"}
PINNED_SUBJECT = re.compile(r"^therapybot#11@([0-9a-f]{40})\+therapybot#12@([0-9a-f]{40})$")


def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def fetch_page(page: int) -> list[dict[str, Any]]:
    if type(page) is not int or not 1 <= page <= 100:
        raise ValueError("page out of bounds")
    url = f"https://api.github.com/repos/{REPO}/issues/{ISSUE}/comments?per_page=100&page={page}"
    req = Request(url, headers={
        "User-Agent": "TherapyBot-Intranel-Public-Observer/0.1",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urlopen(req, timeout=15) as response:
        data = response.read(MAX_PAGE_BYTES + 1)
    if len(data) > MAX_PAGE_BYTES:
        raise ValueError("GitHub page exceeds byte limit")
    comments = json.loads(data.decode("utf-8"), object_pairs_hook=unique_pairs)
    if type(comments) is not list or len(comments) > 100:
        raise ValueError("invalid GitHub comments page")
    return comments


def fetch_pr_head(pr_number: int) -> str:
    """Read a GitHub head. A successful fetch is source currentness, not authority."""
    if pr_number not in (11, 12):
        raise ValueError("only the two pinned prototype PRs are supported")
    url = f"https://api.github.com/repos/{REPO}/pulls/{pr_number}"
    req = Request(url, headers={
        "User-Agent": "TherapyBot-Intranel-Public-Observer/0.1",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urlopen(req, timeout=15) as response:
        data = response.read(MAX_PAGE_BYTES + 1)
    if len(data) > MAX_PAGE_BYTES:
        raise ValueError("GitHub PR metadata exceeds byte limit")
    metadata = json.loads(data.decode("utf-8"), object_pairs_hook=unique_pairs)
    if type(metadata) is not dict or type(metadata.get("head")) is not dict:
        raise ValueError("invalid GitHub PR metadata")
    sha = metadata["head"].get("sha")
    if type(sha) is not str or re.fullmatch(r"[0-9a-f]{40}", sha) is None:
        raise ValueError("invalid GitHub PR SHA")
    return sha


def scan(
    pages: list[list[dict[str, Any]]],
    *,
    start_page: int,
    expected_target: str | None,
    parse: Callable[[dict[str, Any]], Any],
    digest: Callable[[Any], str],
) -> dict[str, Any]:
    """Inspect a bounded window; never interpret payload prose as commands."""
    if not 1 <= len(pages) <= MAX_PAGES or type(start_page) is not int or start_page < 1:
        raise ValueError("bounded page window required")
    # Intranel message_id identifies a packet instance globally. Reusing it in
    # another conversation is a collision, not a fresh independent identity.
    observed: dict[str, str] = {}
    outcomes: list[dict[str, Any]] = []
    counts = {key: 0 for key in (
        "comments_scanned", "valid_packets", "new", "duplicate", "conflict",
        "rejected", "ignored", "oversized", "packet_overflow",
    )}
    for comments in pages:
        if type(comments) is not list or len(comments) > 100:
            raise ValueError("invalid comment page")
        for comment in comments:
            if type(comment) is not dict or type(comment.get("id")) is not int or comment["id"] < 1:
                raise ValueError("comment identity missing")
            body = comment.get("body")
            if type(body) is not str:
                raise ValueError("comment body missing")
            counts["comments_scanned"] += 1
            try:
                byte_size = len(body.encode("utf-8", "strict"))
            except UnicodeError:
                counts["rejected"] += 1
                continue
            if byte_size > MAX_COMMENT_BYTES:
                counts["oversized"] += 1
                continue
            fences = FENCE.findall(body)
            if len(fences) > MAX_PACKETS_PER_COMMENT:
                counts["packet_overflow"] += 1
                continue
            for source in fences:
                try:
                    raw = json.loads(source, object_pairs_hook=unique_pairs)
                    if type(raw) is not dict:
                        raise ValueError("packet must be object")
                    # Exclude any action-bearing or mutating packet even before
                    # validation; this observer is for review metadata only.
                    if raw.get("performative") not in READ_ONLY_PERFORMATIVES or raw.get("effect_class") != "READ_ONLY":
                        counts["ignored"] += 1
                        continue
                    message = parse(raw)
                    if expected_target is not None and str(message.target) != expected_target:
                        counts["ignored"] += 1
                        continue
                    sha = digest(message)
                    if not re.fullmatch(r"[0-9a-f]{64}", sha):
                        raise ValueError("invalid digest")
                    counts["valid_packets"] += 1
                    key = message.message_id
                    old = observed.get(key)
                    status = "NEW" if old is None else ("DUPLICATE" if old == sha else "CONFLICT")
                    observed.setdefault(key, sha)
                    counts[status.lower()] += 1
                    outcomes.append({
                        "comment_id": comment["id"],
                        "message_id": message.message_id,
                        "conversation_id": message.conversation_id,
                        "performative": message.performative.value,
                        "origin": str(message.origin),
                        "target": str(message.target),
                        "parent_message_id": message.parent_message_id,
                        "subject": message.subject,
                        "exact_subject": message.exact_subject,
                        "content_sha256": sha,
                        "observation": status,
                        "origin_authenticated": False,
                        "delivered": False,
                        "ack_accepted": False,
                        "effect_executed": False,
                        "exact_subject_currentness_checked": False,
                    })
                except (TypeError, ValueError, KeyError, OverflowError, RecursionError):
                    counts["rejected"] += 1
    terminal_observed = len(pages[-1]) < 100
    coverage_complete = start_page == 1 and terminal_observed and not (counts["oversized"] or counts["packet_overflow"])
    return {
        "repo": REPO,
        "issue": ISSUE,
        "expected_target": expected_target,
        "start_page": start_page,
        "pages_scanned": len(pages),
        "coverage_complete": coverage_complete,
        "coverage_status": (
            "COMPLETE_SCANNED_WINDOW" if coverage_complete else
            "HOLD_UNREADABLE_COMMENT" if counts["oversized"] or counts["packet_overflow"] else
            "HOLD_PRECEDING_PAGES_UNVERIFIED" if start_page != 1 else
            "HOLD_PAGINATION_LIMIT"
        ),
        "source_identity_authenticated": False,
        "delivered": False,
        "ack_accepted": False,
        "effect_executed": False,
        "counts": counts,
        "packets": outcomes,
    }


def correlate_review_chain(
    report: dict[str, Any],
    *,
    current_heads: dict[int, str] | None,
    request_origin: str = "therapybot:pr11-review",
    responder: str = "therapybot:bt2",
) -> dict[str, Any]:
    """Correlate *observed claims*; never manufacture trusted ACK or delivery.

    The exact local GitHub page scan must contain the causal parent to accept
    correlation. This is intentionally stricter than trusting an ACK's prose.
    """
    packets = report["packets"]
    result: dict[str, Any] = {
        "chain_state": "HOLD_UNKNOWN",
        "subject_currentness": "UNKNOWN",
        "current_heads_checked": current_heads is not None,
        "review_observed": False,
        "ack_claim_observed": False,
        "report_claim_observed": False,
        "requester_report_claim_observed": False,
        "origin_authenticated": False,
        "delivered": False,
        "ack_accepted_as_authority": False,
        "effect_executed": False,
        "review_message_id": None,
        "ack_message_id": None,
        "report_message_id": None,
        "requester_report_message_id": None,
        "pinned_heads": None,
        "observed_current_heads": (
            {"pr11": current_heads.get(11), "pr12": current_heads.get(12)}
            if current_heads is not None else None
        ),
    }
    if not report.get("coverage_complete"):
        result["chain_state"] = "HOLD_INCOMPLETE_PAGE_COVERAGE"
        return result
    if report["counts"]["conflict"]:
        result["chain_state"] = "HOLD_IDENTITY_COLLISION"
        return result
    reviews = [p for p in packets if p["performative"] == "REVIEW"
        and p["origin"] == request_origin and p["target"] == responder
        and p["observation"] == "NEW"]
    if len(reviews) != 1:
        result["chain_state"] = "HOLD_PARENT_REVIEW_NOT_UNIQUE" if reviews else "HOLD_PARENT_REVIEW_NOT_OBSERVED"
        return result
    review = reviews[0]
    result["review_observed"] = True
    result["review_message_id"] = review["message_id"]
    if review["parent_message_id"] is not None:
        result["chain_state"] = "HOLD_REVIEW_PARENT_UNEXPECTED"
        return result
    pin = PINNED_SUBJECT.fullmatch(review["exact_subject"] or "")
    if pin is None:
        result["chain_state"] = "HOLD_UNRECOGNIZED_EXACT_SUBJECT"
        return result
    result["pinned_heads"] = {"pr11": pin.group(1), "pr12": pin.group(2)}
    if current_heads is None or current_heads.get(11) is None or current_heads.get(12) is None:
        result["chain_state"] = "HOLD_CURRENT_HEADS_UNKNOWN"
    elif current_heads[11] != pin.group(1) or current_heads[12] != pin.group(2):
        result["subject_currentness"] = "STALE"
        result["chain_state"] = "HOLD_STALE_SUBJECT"
    else:
        result["subject_currentness"] = "CURRENT"
    all_ack_claims = [p for p in packets if p["performative"] == "ACK"
        and p["conversation_id"] == review["conversation_id"]
        and p["observation"] == "NEW"]
    acks = [p for p in all_ack_claims
        if p["origin"] == responder and p["target"] == request_origin]
    candidates = [p for p in acks if p["parent_message_id"] == review["message_id"]
        and p["exact_subject"] == review["exact_subject"]
        and p["subject"] == review["subject"]]
    if len(candidates) != 1:
        if result["subject_currentness"] != "CURRENT":
            return result
        result["chain_state"] = (
            "HOLD_ACK_CAUSAL_MISMATCH" if acks else
            "HOLD_ACK_ORIGIN_TARGET_MISMATCH" if all_ack_claims else
            "WAIT_ACK_NOT_OBSERVED"
        )
        return result
    ack = candidates[0]
    result["ack_claim_observed"] = True
    result["ack_message_id"] = ack["message_id"]
    reports = [p for p in packets if p["performative"] == "REPORT"
        and p["origin"] == responder and p["target"] == request_origin
        and p["conversation_id"] == review["conversation_id"]
        and p["observation"] == "NEW"]
    requester_reports = [p for p in packets if p["performative"] == "REPORT"
        and p["origin"] == request_origin and p["target"] == responder
        and p["conversation_id"] == review["conversation_id"]
        and p["parent_message_id"] == ack["message_id"]
        and p["exact_subject"] == review["exact_subject"]
        and p["subject"] == review["subject"]
        and p["observation"] == "NEW"]
    if len(requester_reports) == 1:
        result["requester_report_claim_observed"] = True
        result["requester_report_message_id"] = requester_reports[0]["message_id"]
    candidates = [p for p in reports if p["parent_message_id"] == ack["message_id"]
        and p["exact_subject"] == review["exact_subject"]
        and p["subject"] == review["subject"]]
    if len(candidates) != 1:
        if result["subject_currentness"] != "CURRENT":
            return result
        result["chain_state"] = (
            "HOLD_REPORT_CAUSAL_MISMATCH" if reports else
            "WAIT_RESPONDER_REPORT_NOT_OBSERVED" if requester_reports else
            "WAIT_REPORT_NOT_OBSERVED"
        )
        return result
    result["report_claim_observed"] = True
    result["report_message_id"] = candidates[0]["message_id"]
    if result["subject_currentness"] == "CURRENT":
        result["chain_state"] = "REVIEW_ACK_REPORT_OBSERVED_UNAUTHENTICATED"
    return result


def run() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--live", action="store_true", help="GET public issue comments, no credentials")
    mode.add_argument("--fixture", help="JSON list of synthetic GitHub comment pages")
    ap.add_argument("--target", default="therapybot:bt2")
    ap.add_argument("--start-page", type=int, default=1)
    ap.add_argument("--pages", type=int, default=1)
    ap.add_argument("--chain", action="store_true", help="correlate REVIEW->ACK->REPORT claims; requires --check-heads to avoid unresolved currentness")
    ap.add_argument("--check-heads", action="store_true", help="GET PR11/12 heads for exact-subject currentness")
    args = ap.parse_args()
    if not 1 <= args.pages <= MAX_PAGES or not 1 <= args.start_page <= 100 or args.start_page + args.pages > 101:
        ap.error("page window must fit 1..100 and contain 1..3 pages")
    # Fail closed if Intranel source is unavailable. Do not duplicate its
    # admission/parser implementation or silently parse with plain JSON.
    try:
        from intranel import parse_message, content_digest
    except ImportError as exc:
        ap.error("Intranel package unavailable; pass a permitted Intranel src/ via PYTHONPATH")
        raise AssertionError("unreachable") from exc
    if args.live:
        pages: list[list[dict[str, Any]]] = []
        for page_no in range(args.start_page, args.start_page + args.pages):
            page = fetch_page(page_no)
            pages.append(page)
            if len(page) < 100:
                break
    else:
        with open(args.fixture, "r", encoding="utf-8") as handle:
            pages = json.load(handle, object_pairs_hook=unique_pairs)
        if type(pages) is not list or len(pages) > args.pages:
            ap.error("fixture must contain at most --pages pages")
    result = scan(pages, start_page=args.start_page, expected_target=None if args.chain else args.target, parse=parse_message, digest=content_digest)
    if args.chain:
        heads = None
        if args.check_heads:
            try:
                heads = {11: fetch_pr_head(11), 12: fetch_pr_head(12)}
            except (OSError, ValueError, json.JSONDecodeError):
                # A failed currentness probe must never default to CURRENT.
                heads = None
        result["causal_chain"] = correlate_review_chain(result, current_heads=heads)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
