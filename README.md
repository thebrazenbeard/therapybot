# TherapyBot — experimental local mental-health support

TherapyBot is a **free, local-first HTML application** for talking to your own GGUF-compatible local language-model server. It also provides a passphrase-encrypted conversation/journal vault and a small searchable index of attributed public-health references.

It is **not psychotherapy, diagnosis, treatment, a clinically validated safety system, or an emergency response service**. A language model can make serious mistakes.

## Implemented in this MVP

- Local responsive browser interface at `127.0.0.1`, without CDN, accounts, telemetry, cloud storage or paid APIs.
- KoboldCPP/llama.cpp OpenAI-compatible `/v1/chat/completions` adapter; unavailable models are reported honestly.
- Direct/warm/analytical style; brief/balanced/detailed responses.
- SQLite conversation and journal records encrypted individually with AES-256-GCM and `scrypt` passphrase-derived key.
- Journal with optional mood, record search/deletion, plaintext JSON export on user request.
- Offline search of original short summaries linking to NIMH, NICE, WHO, CDC and 988.
- Narrow, explicitly limited present-danger interception; not a suicide or violence risk score.

## Setup (Windows or Linux)

Python 3.10+ and a modern browser are required. For AI chat, run a separately installed local GGUF model with KoboldCPP or llama.cpp exposing `/v1/chat/completions`.

Clone the repository, then use the Python inside its virtual environment—no shell activation or execution-policy change required.

```bash
git clone https://github.com/thebrazenbeard/therapybot.git
cd therapybot
```

Windows PowerShell (Lappy has Python 3.12 available):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m therapybot --model-url http://127.0.0.1:5001
```

Linux:

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -e .
./.venv/bin/python -m therapybot --model-url http://127.0.0.1:5001
```

The example uses model port 5001; configure the actual one. No weights are bundled or downloaded. Without `--model-url`, the journal and knowledge search still work, but ordinary chat reports **model unavailable** instead of fabricating an AI response. The browser should open automatically at <http://127.0.0.1:8766/>. To choose another port/data file, run `python -m therapybot --help`.

The browser opens automatically with a private access link. If using `--no-browser`, open the **full private link** printed in the terminal, including `#access=...`; do not share it. The browser stores the capability only in tab session storage and removes it from the address bar. It rotates on each unlock/lock, invalidating older tabs. On first use choose a vault passphrase (12+ characters), then unlock with it on later launches. There is **no passphrase recovery**. Data defaults to `~/.therapybot/vault.sqlite3`. Stop the process or lock the vault to drop its key reference. Store model weights separately; never commit private data or model weights to GitHub.

Run tests with `python -m unittest discover -s tests -v` after installing dependencies.

## Privacy and safety limits

- Stored chat/journal **contents** are encrypted, but record type, timestamps and IDs are visible in SQLite. This is not full-disk encryption or protection against malware, a compromised OS account or an unlocked browser.
- The separate model server may have its own logging/network behavior. Check its settings. The TherapyBot adapter only accepts loopback HTTP and rejects redirects and proxies.
- **Export downloads plaintext JSON.** Browser downloads, OS backups and disk snapshots fall outside the vault. Deleting a live record does not guarantee forensic erasure of SSD blocks or external copies.
- The app does not contact emergency services for you. Its safety intercept can miss crises or overreact to ambiguous language; its safety and clinical efficacy are unvalidated.
- Literature and research links are publicly readable but their full-text redistribution/training licenses are not established. Only original short summaries ship.

The app supports psychological, sociological, philosophical and spiritual inquiry without presuming diagnosis or forcing wellness exercises. It may explain evidence-informed approaches, but a chatbot interaction is not professionally delivered psychotherapy. In the US, call/text **988** for crisis support or **911** for immediate danger; elsewhere use local services.

See [Threat model](docs/SECURITY.md), [source register](docs/SOURCES.md), and [release gaps](docs/RELEASE_GATE.md).
