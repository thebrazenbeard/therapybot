# Architecture and scope decisions

**2026-11-04 — first vertical slice.** Python stdlib loopback HTTP server + `cryptography` + SQLite; static responsive UI and pluggable localhost GGUF inference. Selected for inspectability, $0 operation, Windows/Linux compatibility and no mandatory hosted services. Supabase is deliberately not used for personal data.

```text
Browser (same host)
  |  127.0.0.1 + request token + Origin/Host validation
TherapyBot HTTP handler
  |-- opt-in encrypted SQLite records (key held in process memory)
  |-- keyword evidence retrieval (source metadata + original summaries)
  |-- rules-based safety route (pre-model)
  `-- local KoboldCPP / llama.cpp HTTP endpoint (no external fallback)
```

The application handles user-approved chat persistence. Model prompt context is explicit, bounded to recent messages from the browser, not silently sourced from unrelated private documents. The API is intentionally local-only, without plugins capable of arbitrary actions. The model can generate false information or dangerous advice; basic prompts and rules are not a clinical safety proof. Independent human clinical review is still required.

Potential future: better retrieval, consented long-term memory, backup restoration, rigorous safety evaluations, locally measured model selection and inference. Do not claim first-release requirements complete without actual local model and host demonstration.
