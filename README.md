# TherapyBot

**Status: experimental local-first prototype — not professional psychotherapy, medical treatment, a diagnosis tool, or an emergency service.**

TherapyBot is a $0, offline-capable mental-health **support and education** application for Windows and Linux. It pairs a local GGUF model (KoboldCPP or llama.cpp-compatible endpoint) with optional passphrase-encrypted personal records, a local journal, and an inspectable, source-linked psychology/sociology reference register. There are no accounts, analytics, advertising IDs, cloud inference fallbacks, or subscription APIs.

> This software has not been clinically validated. Passing synthetic tests does not show that generated responses are safe or effective treatment. An LLM can give harmful, biased, or inaccurate advice. For immediate danger, contact emergency services; in the United States, you can call or text **988**.

## Run locally

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

## Current capabilities

- Local browser conversation, selectable style and response depth.
- Optional saved conversation history; saving defaults **off**. No silent memory or training on user conversations.
- Passphrase-encrypted SQLite journal and saved records, local search, encrypted SQLite backup, and record deletion. Unlocking is necessary before saving.
- Local keyword retrieval over original evidence summaries with clickable external source references. Those references may help ground an answer; they are **not** automatic fact-checking of generated claims.
- Model-independent heuristic safeguards for direct danger disclosures and explanatory crisis resources.
- Loopback-only HTTP listener, Host/Origin checks, per-process request token for mutations, and disabled request logging.
- Curated external scientific, clinical and philosophical source metadata: 22 researched entries, combined with built-in records to yield 23 distinct source URLs for local retrieval. `research/` also contains 30 original synthetic train/dev/eval examples (18/6/6). No model fine-tuning has occurred; source rights and clinical quality need separate review.

## Privacy and limits

The SQLite vault uses a passphrase-derived key (scrypt) with Fernet authenticated encryption. The passphrase and derived key are not deliberately saved to disk. The model receives conversation text **on the local configured endpoint**; you remain responsible for the model server's separate logging and retention settings. The app protects against obvious unauthorized access but has **not** undergone independent penetration testing, forensic secure deletion validation, or professional privacy certification.

The app stores an encrypted copy of each explicitly saved conversation or journal entry; some metadata (record type and timestamp) remains visible. Backup downloads contain encrypted SQLite records, but **browser downloads, filesystem snapshots, swap, crash dumps, and externally created copies can persist**. Deleting in-app records cannot remove every external backup or filesystem snapshot. Keep passphrases safe: there is no remote account-based recovery.

The app does **not** ingest personal medical records, other conversations, or private attachments by default. Do not commit sensitive user data, vaults, or model weights. The evidence register contains original brief summaries and pointers to external pages, not bulk third-party article text. Readability is not a license to redistribute or train on source material.

## Development and evidence

```sh
python -m unittest discover -s tests -v
python -m compileall -q therapybot
python scripts/validate_research.py
```

See `docs/ARCHITECTURE.md`, `docs/THREAT_MODEL.md`, `docs/RESEARCH_POLICY.md`, `docs/REVIEW_FINDINGS.md` and `research/` for currentness and source provenance. The exact checkpoint and tests belong in `docs/CHECKPOINT.md`.

The project seeks **evidence-informed support**, not automated psychotherapy, and does not claim HIPAA compliance or guaranteed confidentiality. No chargeable infrastructure should be introduced.
