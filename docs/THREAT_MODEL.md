# Privacy/security threat model — prototype, not certification

## Assets and trust boundaries

- Sensitive chat/journal content belongs to the person using the local computer.
- Browsers and arbitrary websites are potentially hostile; only same-origin requests with verified Host/Origin and a random local request token should mutate data.
- Local GGUF runtime is a distinct process. TherapyBot cannot attest that it does not log prompts; its endpoint is strictly restricted to loopback addresses to prevent unexpected third-party transfer.
- Evidence snippets and model completions are untrusted text, never executable instructions or source of authority to perform file/network actions.
- An adversary with local machine access, keylogging, a compromised browser, or process memory access may defeat these protections.

## Implemented controls

1. Loopback-only bind, local endpoint URL validation, no outbound model fallback.
2. No HTTP request logs; content length limits; response `no-store` and clickjacking defenses.
3. Browser-origin and Host validation plus per-process CSRF token for state-changing requests. Every sensitive record read, write, export and deletion also requires a separate session credential issued only after a correct vault passphrase.
4. scrypt key derivation with random salt; Fernet authenticated per-record encryption; no saved key; passphrase minimum length when initializing.
5. Explicit user opt-in before persistence; journal submission is an explicit write; backup contains ciphertext rather than plaintext export.
6. No external scripts or UI telemetry; UI must use `textContent` for model and user messages.

## Outstanding and release-blocking

- No independent penetration testing, key-management review, or full local threat-environment assessment.
- No assurance against model misinformation, prompt injection in natural language, dangerous completions, or clinical misjudgment. Rules can miss danger and over-trigger on ambiguous language.
- No recovery for forgotten passphrases; backup **restore** not yet exposed in UI. Browser-based record search decrypts locally in process memory, not into a plaintext database index.
- No proof of secure erasure across SSD, snapshots, WAL, browser, local model caches or filesystem backups.
- CSP currently permits inline scripts because of self-contained UI; harden before wider deployment.
- No independent test of Lappy+GGUF inference yet. A reachable port check is not model-quality evidence.

> Hostile question: Would a motivated malicious website or compromised local model retain user data despite the absence of cloud services? Until tested on each supported platform, the privacy claim must stay narrow.
