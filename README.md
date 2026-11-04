# TherapyBot

**Status: development-only experimental local-first prototype — not a public interactive mental-health release, professional psychotherapy, medical treatment, a diagnosis tool, or an emergency service.**

TherapyBot is a $0, offline-capable mental-health **support and education** project for Windows and Linux. The existing Python application pairs an optional local GGUF endpoint (KoboldCPP or llama.cpp) with passphrase-encrypted personal records, a local journal, and source-linked psychology/sociology references. A **separate developer-only browser experiment** under [`embedded/`](embedded/README.md) ships limited conversational behavior in repository JavaScript without requiring a separately installed model server. Neither implementation is clinically qualified. There are no accounts, analytics, advertising IDs, cloud inference fallbacks, or subscription APIs.

**Web interface distinction:** The Python HTML/vault application runs at `http://127.0.0.1:8768` with a separately started GGUF endpoint. The experimental [`embedded/index.html`](embedded/index.html) is a second, standalone HTML interface that opens locally with bundled limited semantic logic, no vault, and no neural weights. When the Python server is running, its own home page also links to that same embedded client at `http://127.0.0.1:8768/embedded/`: serving its bundled CSS/JS over loopback does not activate inference, transfer messages to the vault, or require GGUF weights. The [GitHub Pages introduction](https://thebrazenbeard.github.io/therapybot/) and its [interface preview](https://thebrazenbeard.github.io/therapybot/interface-preview.html) remain **read-only**, without chat submission or personal-data inputs. The Pages workflow publishes **only** `pages/`, not `embedded/`, `static/`, personal records, or the repository root.

**Release boundary:** The owner has withheld a general-public interactive release until the documented safety, model-output, privacy, accessibility, source-grounding, and record-compatibility failures are repaired and independently checked. Local development and testing may continue; the public Pages preview remains read-only. The [multi-team T’Kal-in-ket debate](docs/TKAL_HEARING_20261104.md) is an **open design review**, not a release authorization or clinical validation.

> This software has not been clinically validated. Passing synthetic tests does not show that generated responses are safe or effective treatment. An LLM can give harmful, biased, or inaccurate advice. For immediate danger, contact emergency services; in the United States, you can call or text **988**.

## Run locally

### Repository-resident browser experiment (development only)

Open [`embedded/index.html`](embedded/index.html) from a local checkout in a browser with its neighboring JavaScript/CSS files intact. No Python, external inference service, model download, or internet connection is required for the bounded, in-memory **semantic conversation prototype**. It is **not a trained LLM** and cannot reliably interpret novel distress or danger. Node-based tests pass, but actual browser and assistive-technology behavior is not yet qualified. See [architecture and packaging](docs/REPOSITORY_RESIDENT_MODEL.md) and [privacy and safety gates](docs/EMBEDDED_PRIVACY_SAFETY.md). This experiment is intentionally excluded from public Pages.

### Existing Python/GGUF application

Requirements: Python 3.10+ and a separately installed local inference server; Windows PowerShell or Linux shell. Download model weights separately (never into this repository). Python's `cryptography` package is required for local encrypted records.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m therapybot --model-url http://127.0.0.1:5001/api/v1/generate
```

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m therapybot --model-url http://127.0.0.1:5001/api/v1/generate
```

Open `http://127.0.0.1:8768` in a browser on the same computer. Use `--no-browser` to prevent an automatic browser launch. Override the port with `--port`, or choose a database file with `--database`. Start your local model server first: supported URLs end in `/api/v1/generate` (KoboldCPP), `/completion` (llama.cpp), or `/v1/chat/completions` (OpenAI-compatible local server). For an OpenAI-compatible local endpoint, use `--model-name` with the installed model ID.

If the model server is offline, ordinary chat returns an explicit error. TherapyBot **never** silently switches to an online service. Its static safety response remains available for high-risk text, but the classifier is rudimentary and cannot reliably detect all danger or interpret every negation.

One bounded synthetic runtime probe on VN2 verified the **actual TherapyBot HTTP → ModelClient → local llama.cpp GGUF** path using Granite 3.3 2B Q4_K_M (HTTP 200, approximately 11.6 seconds, no saved record). That does not qualify other models, clinical safety, Windows inference, or browser E2E behavior.

## Current capabilities

- Local browser conversation, selectable style and response depth.
- Separate, nonpublished repository-resident HTML/JavaScript semantic experiment: limited topic/state dialogue, no model server, no recording, and no trained neural weights.
- Optional saved conversation history; saving defaults **off**. No silent memory or training on user conversations.
- Passphrase-encrypted SQLite journal and saved records, local search, encrypted SQLite backup, and record deletion. Unlocking is necessary before saving.
- Local keyword retrieval over original evidence summaries with clickable external source references. Those references may help ground an answer; they are **not** automatic fact-checking of generated claims.
- Experimental heuristic handling for some direct danger disclosures and always-visible emergency-help guidance in the local HTML. The heuristic remains unreliable on independent adversarial language.
- Loopback-only HTTP listener, Host/Origin checks, per-process request token for mutations, and disabled request logging.
- Curated external scientific, clinical, sociological, philosophical and publisher-rights metadata: **82 link-only research records**, combined with built-in records to yield **83 distinct local reference pointers**. Wave 3 added 10 clinical, 10 social-science, 10 trauma/cultural-context, and one publisher-permissions record. Independent audits were **partially confirmed for bibliographic/source-fit purposes**, not clinical or legal approval. All third-party model-training rights remain `not-cleared`; no external article/book bodies were copied.
- **62 original synthetic curriculum candidates** (`train/dev/eval`: **42/14/6**), including 16 wave-3 psychology/sociology conversations. Independent curriculum review required source-fit and proportionality corrections, which were made; these are still educational candidates rather than trained or clinically validated interventions.
- The original 34-case (**11/34 matched**) and independent 36-case (**14/36 matched**) safety holdouts still demonstrate poor routing. A separate, transparently authored wave-3 regression-canary set shows **3/8 matched** on the current heuristic; this is not a sealed holdout or clinical measure. Mock-model tests continue to confirm unreviewed generated text can be forwarded. **Public interactive release is held.**

## Privacy and limits

The SQLite vault uses a passphrase-derived key (scrypt) with Fernet authenticated encryption. The passphrase and derived key are not deliberately saved to disk. The model receives conversation text **on the local configured endpoint**; you remain responsible for the model server's separate logging and retention settings. The app protects against obvious unauthorized access but has **not** undergone independent penetration testing, forensic secure deletion validation, or professional privacy certification.

The app stores an encrypted copy of each explicitly saved conversation or journal entry; some metadata (record type and timestamp) remains visible. Backup downloads contain encrypted SQLite records, but **browser downloads, filesystem snapshots, swap, crash dumps, and externally created copies can persist**. Deleting in-app records cannot remove every external backup or filesystem snapshot. Keep passphrases safe: there is no remote account-based recovery.

The app does **not** ingest personal medical records, other conversations, or private attachments by default. Do not commit sensitive user data, vaults, or model weights. The evidence register contains original brief summaries and pointers to external pages, not bulk third-party article text. Readability is not a license to redistribute or train on source material.

Do not enter private medical or mental-health information into a public GitHub Pages copy of an application. Its public preview contains no active input fields and makes no requests to TherapyBot's local APIs. The private web interface is served from the loopback HTTP server above.

## Development and evidence

```sh
python -m unittest discover -s tests -v
python -m compileall -q therapybot
python scripts/validate_research.py
```

See `docs/ARCHITECTURE.md`, `docs/THREAT_MODEL.md`, `docs/RESEARCH_POLICY.md`, `docs/REVIEW_FINDINGS.md`, the independent `docs/WAVE2_*` and `docs/WAVE3_*` reviews, and `research/` for currentness and provenance. The source-merge utility runs in dry-run mode by default: `python scripts/merge_research_sources.py <new-reviewed-batch.json>`; an explicit `--apply` is available only for batches **not already included** in the register. A successful merge is a structural check, not scientific validation or a license grant. For a currently **failing safety characterization**, run `python -m scripts.evaluate_safety_canaries --strict` (nonzero is expected until the documented defects are fixed). The exact checkpoint and tests belong in `docs/CHECKPOINT.md` and `docs/WAVE3_CHECKPOINT_20261104.md`.

The project seeks **evidence-informed support**, not automated psychotherapy, and does not claim HIPAA compliance or guaranteed confidentiality. No chargeable infrastructure should be introduced.
