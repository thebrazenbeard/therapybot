"""Fail-closed boundary for untrusted local model generations.

No generated-output reviewer is bundled or clinically qualified. The default
cannot approve a candidate; caller-supplied reviewers remain development-only
until independently evaluated and separately authorized for release.
"""

import threading
from queue import Empty, Queue


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

MAX_REVIEW_CALLBACKS = 2
REVIEW_WAIT_SECONDS = 2.0


class ReviewAdmission:
    """Bound developer reviewer calls; timeout does NOT kill Python threads.

    Each callback keeps one slot until its worker actually exits. If two
    callbacks hang forever, new requests fail closed rather than spawn more.
    This controls this callback path, not arbitrary threads a reviewer creates.
    """

    def __init__(self, capacity=MAX_REVIEW_CALLBACKS, timeout=REVIEW_WAIT_SECONDS):
        if capacity < 1 or timeout <= 0:
            raise ValueError("Invalid reviewer admission limits")
        self._slots = threading.BoundedSemaphore(capacity)
        self.timeout = timeout

    def generate_reviewed(self, generate, *, message, context, input_route, reviewer):
        """Return (approved_text, verdict); never return unapproved candidates."""
        # Capacity is checked BEFORE the potentially expensive local inference.
        if not self._slots.acquire(blocking=False):
            return None, "saturated"
        try:
            candidate = generate()
        except BaseException:
            self._slots.release()
            raise

        verdict_queue = Queue(maxsize=1)
        def review_worker():
            verdict = "unknown"
            try:
                verdict = review_candidate(
                    message=message, candidate=candidate, context=context,
                    input_route=input_route, reviewer=reviewer)
            finally:
                # The slot is NOT returned merely because the HTTP waiter has
                # timed out. A hung callback retains this bounded slot.
                try:
                    verdict_queue.put_nowait(verdict)
                finally:
                    self._slots.release()

        try:
            threading.Thread(
                target=review_worker, daemon=True,
                name="therapybot-output-review").start()
        except Exception:
            self._slots.release()
            return None, "unknown"

        try:
            verdict = verdict_queue.get(timeout=self.timeout)
        except Empty:
            return None, "timeout"
        return (candidate if verdict == "allow" else None), verdict
