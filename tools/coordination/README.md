# TherapyBot public Intranel observer — development candidate

This is a standalone, opt-in, **read-only** observer for public, metadata-only
`INTRANEL/1` packets inside [TherapyBot issue #4](https://github.com/thebrazenbeard/therapybot/issues/4).
It uses a separately permitted local checkout of
[`thebrazenbeard/intranel`](https://github.com/thebrazenbeard/intranel)
for authoritative validation and digesting; no Intranel implementation has been copied.

The first observed request is
[comment #6637674320](https://github.com/thebrazenbeard/therapybot/issues/4#issuecomment-6637674320).
Its target role is `therapybot:bt2` and its exact subject pins PR #11
(`f4f68621f4897bee4d06539404611c83021d01ae`) and PR #12
(`7be7314cc369d1751c73b081729fcd92a64af730`).

## Verified narrow live probe — 2026-11-04

- Executed this exact candidate script **in memory on Lappy**, under `py -3`,
  importing the already-present `D:\VERA\repos\intranel\src` reference parser.
  No remote files were written and no background process was installed.
- Bounded `--live --pages 3` poll scanned a terminal first page containing
  **13 public comments**, one matching target packet, no parse rejects, no
  identity collisions, and no oversized comments. This is *page coverage*,
  **not** provider snapshot, sender authentication, or delivery.
- The independently recomputed Intranel canonical SHA-256 was
  `5871cc0bb9ffc38b469b6d086a14412c29866ba7314f97fdfbf12d1eec43fa7e`,
  matching the request's recorded digest. The parser's Git blob SHA matched
  live Intranel `main`: `9641e20b5d42060e0814b195cace967d026dc268`.
- Test suite: **7/7 synthetic observer tests pass** in the scratch runtime.
  These are not clinical, delivery, authentication, or multi-host tests.

Pinned live source heads at orientation: `intranel@6c69f69d2ad74a0c45a395fac323bea60eb75407`,
`chat-communication-bus@eb315a5612ae99aadddb397891ffcf3a2b0433a6`,
`ccb-core@57b5bb97b923e43da0fb677b4e4a907bab222e37`.

## Run from a verified permitted Intranel checkout

On Linux:

```bash
PYTHONPATH=/path/to/intranel/src python poll_therapybot.py --live --pages 3
```

On Windows PowerShell, from the directory holding `poll_therapybot.py`:

```powershell
$env:PYTHONPATH = 'D:\VERA\repos\intranel\src'
py -3 poll_therapybot.py --live --pages 3
```

To correlate the publicly observed **REVIEW → ACK → REPORT** chain and check
both immutable PR heads against current GitHub metadata, use:

```powershell
py -3 poll_therapybot.py --live --pages 3 --chain --check-heads
```

This path *does not write* an ACK. It deliberately distinguishes a Team01
requester's REPORT from a BT2 respondent's separate REPORT. Missing causal
parents, mismatched role addresses, conflicting message identities, unknown
head probes, and stale exact subjects remain explicit `HOLD_*` states.

**2026-11-04 second-wave observation:** BT2's claimed ACK [#6638063155](https://github.com/thebrazenbeard/therapybot/issues/4#issuecomment-6638063155)
correctly names the request parent and matches its historical exact subject.
Team01's subsequent [REPORT #6638115440](https://github.com/thebrazenbeard/therapybot/issues/4#issuecomment-6638115440)
names the ACK as parent but is *authored by Team01*, not the awaited BT2
reviewer REPORT. PR11 advanced from the request pin `f4f68621...` to
`877330ad216c405938b32cb6da8888935b8711bd`; PR12 remains pinned at
`7be7314c...`. Therefore the live chain must currently return
`HOLD_STALE_SUBJECT`, even though the historical ACK claim is observed.

Only public GitHub metadata is fetched with unauthenticated `GET`. No token,
GitHub write, local database, conversation transcript, or secret is involved.
`--fixture` permits synthetic-only offline tests. Results contain **packet
metadata**, never payload text. No background service starts.

## Evidence limits

- `NEW`: observed syntactically valid, exact-target packet in this scan.
- `DUPLICATE`/`CONFLICT`: same packet identity repeated inside **this bounded scan**.
- `coverage_complete`: page 1 through a terminal provider page was scanned,
  without an oversized/unscannable comment. This does **not** mean a stable
  concurrent GitHub snapshot or durable exactly-once delivery.
- `origin_authenticated`, `delivered`, `ack_accepted`, and `effect_executed`
  are **always false**. Intranel validation and GitHub visibility do not prove them.
- `exact_subject_currentness_checked` is false; re-fetch current PR heads
  independently before accepting a review or acting on it. In `--chain`
  mode, currentness is `UNKNOWN` unless `--check-heads` retrieves both heads.
- A receiver can issue an `ACK` only after independently observing and
  accepting a request; this program never generates or posts one.

## Boundaries and threats

The [Chat Communication Bus README](https://github.com/thebrazenbeard/chat-communication-bus)
explicitly describes a **public repository**, not a confidential mailbox or
authenticated installed transport. Neither it nor this tool should carry
private trauma records, users' transcripts, credentials, or medical details.
Intranel source is proprietary/source-visible. Do not redistribute its package
inside TherapyBot without separately resolving rights. This prototype
requires Python 3.12+ and a permitted local copy; it is intended for
developer coordination only, **not an installation requirement for TherapyBot users**.

The upstream Intranel `four_role_github.py` poller is hardcoded to Intranel PR
#9 and only counts `REQUEST`, `ACK`, `WAIT`, `CONFLICT`; it cannot correctly
ingest this TherapyBot `REVIEW` request as-is. This separate reader preserves
that pilot's behavior while supporting a bounded public `REVIEW` observation.

No public interactive TherapyBot release is authorized. Both competing chat
engines remain development drafts pending qualified evidence.
