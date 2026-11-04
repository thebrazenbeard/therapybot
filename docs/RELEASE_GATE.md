# Pre-release checkpoint and falsifiers

**Current status: experimental MVP; NOT clinical or security validated.**

- [x] HTML interface tested in an isolated browser on Windows (pre-backup UI commit).
- [x] Current-head HTML encrypted-backup download and API-level offline restore to a new vault verified with synthetic records in isolated Windows Edge.
- [ ] Interactive restore CLI and Linux-browser tests; Windows ACL verification.
- [ ] Real GGUF KoboldCPP or llama.cpp process verified on an authorized host; latency/CPU/RAM/VRAM benchmarked.
- [ ] Encrypted vault, wrong key, hostile Host/Origin, CSRF, XSS and deletion tested against real persistence and HTTP behavior.
- [ ] Synthetic tests cover current danger, historic/hypothetical self-harm, credible violence, unusual experiences, mania, medication and diagnosis, dependency and prompt injection.
- [ ] Real local model outputs independently reviewed for false reassurance, false escalation, misinformation, belief reinforcement and boundaries.
- [x] Synthetic encrypted-backup and new-only restore round-trip implemented and tested locally.
- [ ] Windows restore-directory ACL behavior qualified; external backup copies accounted for.
- [ ] Actual host and clinical/security review gates cleared.

Testing one component is not clinical effectiveness. Source review is not runtime verification. The user should not rely on this application for urgent care, medical decisions, or security guarantees.

See [2026-11-04 host and independent review evidence](HOST_PROBE_2026-11-04.md).
