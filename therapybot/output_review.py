"""Fail-closed boundary for untrusted local model generations.

No generated-output reviewer is bundled or clinically qualified. The default
cannot approve a candidate; caller-supplied reviewers remain development-only
until independently evaluated and separately authorized for release.
"""

REVIEW_HOLD_REPLY = (
    "I cannot independently review generated answers in this build, so I "
    "won't display one. This experimental conversation path is still being tested."
)


def review_candidate(*, message, candidate, context, input_route, reviewer):
    """Return allow/block/unknown without exposing candidate in the verdict.

    The model's own safety labels and prose are never an authorization. A
    reviewer must be explicitly installed by trusted server-side code; no
    external API, logging, persistence or network operation happens here.
    """
    if (not callable(reviewer) or type(candidate) is not str or
            not candidate.strip() or len(candidate) > 12_000):
        return "unknown"
    try:
        verdict = reviewer(message=message, candidate=candidate,
                           context=context, input_route=input_route)
    except Exception:
        return "unknown"
    return verdict if type(verdict) is str and verdict in ("allow", "block") else "unknown"
