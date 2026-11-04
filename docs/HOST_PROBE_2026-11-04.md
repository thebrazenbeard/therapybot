# 2026-11-04 runtime and review evidence checkpoint

This is a bounded provenance record, **not** a clinical release certificate. All
conversation prompts, vault entries and browser profiles used in probes were
synthetic. No private personal records were ingested.

| Evidence tier | Subject / actual result | Limit |
| --- | --- | --- |
| SOURCE INSPECTION | Local Flask-free `http.server` backend, HTML/CSS/JS client, GGUF-server HTTP adapter, encrypted SQLite vault, backup/restore | Source inspection does not prove deployment |
| TEST | GitHub Actions run `41838031538` on `33fbc1a73340e224a52385eb9f6bababcf12c1e8` passed Ubuntu and Windows | Earlier commit only; rerun for current head |
| REAL RUNTIME PROBE | Authorized VN2 llama.cpp-compatible server at loopback `127.0.0.1:11435` returned a TherapyBot synthetic chat reply via its local-model adapter: HTTP 200, about 14.48 s, `saved=false`, zero records | Single real request on earlier source; no clinical evaluation or hardware benchmark |
| REAL BROWSER PROBE | Isolated headless Windows Edge on Lappy loaded HTML, unlocked synthetic vault, wrote a journal entry, searched history and sources, locked, and cleared sensitive DOM; genuine screenshot in `docs/images/therapybot-html-preview.png` | This preceded the encrypted-backup UI button; not a current-head browser E2E |
| REAL BROWSER + RESTORE PROBE | On exact GitHub head `b8577f6c03a47c46a27af747e2e740e0840986a8`, isolated Windows Edge clicked the HTML **encrypted backup** button; `.tbbak` download was 20,550 bytes, with no plaintext synthetic canary or SQLite header. Original server stopped, a separate offline Python process called `restore_backup` to create a new vault, then a new Edge session against a new loopback server unlocked and displayed the one restored synthetic record; wrong passphrase failed without output, and locking cleared the browser DOM | This verifies Python API-level restoration plus a real HTML backup click, **not** interactive `restore-backup` CLI prompt or Linux/Windows-ACL qualification |
| INTERNAL INDEPENDENT MODEL REVIEW | Clinical safety review found missed and over-triggered phrases; an expanded synthetic boundary suite was added | Still misses novel expressions; no professional clinical validation |
| INTERNAL INDEPENDENT MODEL REVIEW | Backup review reproduced SQLite `CHECK`-constraint restore defect; exact-DDL check and regression added. POSIX shared-writable parents now rejected | Windows ACL verification and hostile filesystem races remain constrained by host ownership |

One 4-prompt real-model behavior sample in the same local model environment
reported three expected responses and one partial failure: the model
unnecessarily introduced a psychiatric category for an unusual experience.
The system prompt was subsequently tightened, but that change has **not** been
qualified against a larger adversarial model sample.

A successor six-prompt real-model probe at the same VN2 service reported
**3 PASS, 1 PARTIAL and 2 FAIL**, notably unsupported psychiatric labeling of a
persecutory-belief report and a fabricated citation. See the
[full bounded model probe](MODEL_BEHAVIOR_2026-11-04.md). A narrow
post-generation attribution guard is implemented in source, but it has only
unit/mock-HTTP validation so far; clinical behavioral safety remains unknown.

## Known unqualified gates

- Sustained real-model mental-health safety / clinical efficacy.
- Runtime on both Windows and Linux with actual user-selected GGUF weights.
- Full CPU/RAM/VRAM measurements at the selected inference quantization.
- Interactive restore CLI and Linux-browser restore tests; verify Windows destination ACLs.
- Windows-specific ACL validation and target-host installation/readback.
- Model post-generation assurance for dangerous medical or harm-method outputs.

The [release gate](RELEASE_GATE.md) remains open until corresponding real
probes and independent evidence exist. Review statements cannot elevate a
single synthetic test to clinical qualification.
