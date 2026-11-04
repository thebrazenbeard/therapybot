# TherapyBot

**Status: development-only experimental local-first prototype — not a public interactive mental-health release, professional psychotherapy, medical treatment, a diagnosis tool, or an emergency service.**

TherapyBot is a $0, offline-capable mental-health **support and education** prototype for Windows and Linux. A self-contained HTML/JavaScript **embedded guide** works without a separately installed language model or local server. The fuller local application optionally connects to a GGUF model (KoboldCPP or llama.cpp-compatible endpoint), and offers passphrase-encrypted personal records, a local journal, and an inspectable, source-linked psychology/sociology reference register. There are no accounts, analytics, advertising IDs, cloud inference fallbacks, or subscription APIs.

**Web interface distinction:** Open `static/offline.html` directly from a local checkout for a browser-only, unsaved conversation; keep `static/semantic_core.js` alongside it. No Python, model daemon, CDN, internet, or account is required for that limited mode. The fuller HTML interface runs at `http://127.0.0.1:8768` after starting the Python application and offers a choice between the embedded guide and an optional local GGUF model. The [GitHub Pages introduction](https://thebrazenbeard.github.io/therapybot/) links to a [read-only interface preview](https://thebrazenbeard.github.io/therapybot/interface-preview.html). Neither public page has chat submission, vault unlock, or model connection. The Pages workflow publishes only `pages/`, never `static/`, personal records, or the repository root.

**Release boundary:** The owner has withheld a general-public interactive release until the documented safety, model-output, privacy, accessibility, source-grounding, and record-compatibility failures are repaired and independently checked. Local development and testing may continue; the public Pages preview remains read-only. The [multi-team T’Kal-in-ket debate](docs/TKAL_HEARING_20261104.md) is an **open design review**, not a release authorization or clinical validation.

> This software has not been clinically validated. The embedded guide's rules can miss urgent dangers, overreact to language, repeat themselves, and give unsuitable prompts; they are **not a trained language model**. A separate LLM can also give harmful, biased, or inaccurate advice. Passing synthetic tests proves neither mode safe or effective as treatment. For immediate danger, contact emergency services; in the United States, you can call or text **988**.

## Open the standalone offline HTML — no installation

1. Download or clone this repository to your own computer.
2. Open **`static/offline.html`** in a modern browser (double-clicking works). Keep the adjacent `static/semantic_core.js` file in the same directory.
3. Type a message. The limited rule-based guide responds entirely in the browser. It retains a few topic and preference labels during the current tab's conversation, supports explicit corrections, and clears them with **Clear session**. It does **not** store raw messages or send them to the TherapyBot server. Nothing needs to be installed or configured.

This mode offers a small, transparent semantic map with original reflection prompts and links to public sources. Its related reading does **not** establish that any individualized reply is clinically correct. It cannot offer open-ended generative reasoning or a genuine replacement for an LLM. **Do not use it to assess emergencies, make diagnoses, or decide medication.** External source links initiate a normal internet request only if clicked.

## Run locally

Requirements for the **fuller local vault/server experience**: Python 3.10+; Windows PowerShell or Linux shell. A separately installed local GGUF model server is needed **only for the Local GGUF mode**, not for the embedded guide. Download model weights separately (never into this repository). Python's `cryptography` package is required for encrypted records.

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

If the model server is offline, **Local GGUF mode** returns an explicit error; **Embedded guide mode** still works using bundled browser rules. TherapyBot **never** silently switches to an online service. Both modes have unvalidated safety handling and cannot reliably detect every dangerous situation or interpret every negation.

One bounded synthetic runtime probe on VN2 verified the **actual TherapyBot HTTP → ModelClient → local llama.cpp GGUF** path using Granite 3.3 2B Q4_K_M (HTTP 200, approximately 11.6 seconds, no saved record). That does not qualify other models, clinical safety, Windows inference, or browser E2E behavior.

## Current capabilities

- Standalone, browser-only `file://` conversation with bundled semantic rules, no backend and no persistent records; a bounded topic/preference context can be corrected and cleared.
- Full local browser conversation with explicit embedded-vs-GGUF selection, style and response depth.
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
