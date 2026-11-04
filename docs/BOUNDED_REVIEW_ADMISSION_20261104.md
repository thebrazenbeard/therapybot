# Developer callback admission limit — PR #26 descendant

**Scope:** Python TherapyBot local loopback server only. This is a distinct draft
branch built from PR #26 commit `eb43d2e713ca8a6bf3252245d248462cf5747b2b`.
It does not change the default no-reviewer `review_hold` behavior or qualify
any reviewer, clinical workflow, remote service, or public multiuser access.

## Observed failure and smallest bounded mitigation

Synthetic local probes on PR #26 ran a reviewer that waited indefinitely on a
`threading.Event`. Three independent loopback `/api/chat` requests entered
three blocking callbacks concurrently. The HTTP server could still answer
`/api/status`, but had no admission limit or reviewer wait deadline.

The new `ReviewAdmission` is **per AppServer**, with two nonblocking slots.
A request must acquire a slot **before** local model generation. If all slots
are held, it returns a neutral `review_hold` with `saved=false` and does not
invoke the model. The handler waits at most 2.0 seconds for a worker callback
verdict, then quarantines the candidate when late or unknown.

**Important:** Timing out the handler does not kill or cancel the Python
callback. The slot remains held by that worker until it actually exits. A
reviewer that hangs forever can exhaust both slots permanently; later
generated-output requests fail closed without additional callback threads.
The thread is daemonized; it is neither sandboxed nor trusted.

## Exact focused test

The adversarial test uses two concurrently blocked callbacks, then sends a
third request before timeout and a fourth **after** both HTTP waiters time
out but while both callbacks still hang. Neither extra request generates.
The test checks that unrelated status responds, the first two replies
quarantine, a late reviewer `allow` cannot enter JSON or vault, and capacity
recovers only after out-of-band callback release. A synthetic opt-in saved
chat still leaves the vault empty on timeout.

- **RED on PR #26:** third request stuck; focused unittest failed exit 1.
- **GREEN on isolated branch:** focused unittest passed.
- Windows Python 3.14 full regression: **171 tests OK (skipped=2), 42.604 seconds, exit 0**. Synthetic generator failure and worker-start failure also demonstrate permit reclamation. The pre-existing HTTPError cleanup ResourceWarnings remain.

## Explicit unresolved boundaries

> REVIEW: The 2-second deadline limits time waiting for the **reviewer**
> verdict, not the separate local model generation/network call. A hung
> generator can occupy one of the two slots until its own call exits.

> REVIEW: This is not a process sandbox, resource quota, operating-system
> cancellation, independent safety reviewer, or public-service DoS defense.
> `ThreadingHTTPServer` still spawns handler threads, and a reviewer itself
> could launch unmanaged work or leak candidate text in developer code.

> FAIL: The process-global CSRF/session/vault is not multiuser isolation.
> Separate authenticated identities and per-user vault/key/session ownership
> are required before considering public deployment.

**Disposition:** source/test mitigation only; clinical and public release
remain **HOLD**. No shared service restart, deployment or merge is implied.
