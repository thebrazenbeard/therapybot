"""Fail-closed handling of untrusted local model output.

No qualified generated-output reviewer is bundled with this prototype.
"""

import threading
from queue import Empty, Queue

REVIEW_HOLD_REPLY = (
    "I cannot independently review generated answers in this build, so I "
    "won't display one. This experimental conversation path is still being tested."
)


def review_candidate(*, message, candidate, context, input_route, reviewer):
    """Only an explicit reviewer decision can release a bounded candidate.

    The optional reviewer remains an unqualified developer injection point.
    ReviewAdmission bounds the HTTP wait, not arbitrary Python execution.
    """
    if not callable(reviewer) or type(candidate) is not str or not candidate.strip() or len(candidate) > 12_000:
        return "unknown"
    try:
        verdict = reviewer(message=message, candidate=candidate, context=context, input_route=input_route)
    except Exception:
        return "unknown"
    return verdict if type(verdict) is str and verdict in ("allow", "block") else "unknown"


MAX_REVIEW_CALLBACKS = 2
REVIEW_WAIT_SECONDS = 2.0


class ReviewAdmission:
    """Limit reviewer workers and the HTTP wait without claiming cancellation.

    Each worker holds an admission slot until it exits, even if its HTTP
    waiter times out. A stuck reviewer can permanently exhaust both slots;
    further requests fail closed and do not spawn additional reviewer work.
    This is neither a process sandbox nor a total HTTP response deadline.
    """

    def __init__(self, capacity=MAX_REVIEW_CALLBACKS, timeout=REVIEW_WAIT_SECONDS):
        if type(capacity) is not int or capacity < 1 or type(timeout) not in (int, float) or timeout <= 0:
            raise ValueError("Invalid reviewer admission limits")
        self._slots = threading.BoundedSemaphore(capacity)
        self.timeout = timeout

    def generate_reviewed(self, generate, *, message, context, input_route, reviewer):
        """Return (approved_candidate, verdict), never unapproved text."""
        if not self._slots.acquire(blocking=False):
            return None, "saturated"

        try:
            # This call still has its separate model-client network timeout;
            # an untrusted custom generator is not forcibly cancellable.
            candidate = generate()
        except BaseException:
            self._slots.release()
            raise

        verdict_queue = Queue(maxsize=1)

        def worker():
            verdict = "unknown"
            try:
                verdict = review_candidate(message=message, candidate=candidate,
                                           context=context, input_route=input_route,
                                           reviewer=reviewer)
            except BaseException:
                # A developer callback may raise BaseException; don't turn
                # that into released model prose or a noisy private traceback.
                verdict = "unknown"
            finally:
                try:
                    verdict_queue.put_nowait(verdict)
                finally:
                    self._slots.release()

        try:
            threading.Thread(target=worker, name="therapybot-output-review",
                             daemon=True).start()
        except Exception:
            self._slots.release()
            return None, "unknown"

        try:
            verdict = verdict_queue.get(timeout=self.timeout)
        except Empty:
            return None, "timeout"
        return (candidate if verdict == "allow" else None), verdict
