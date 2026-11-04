# Wllama v3.8.1, zero-CDN browser boot — frozen plan

Frozen before result inspection, 2026-11-04. This is a successor experiment distinct from `RESEARCH_RECORD.md`.

## Question

Can a tiny static HTML page, without a backend, CDN, third-party model server, downloaded weights, or credentials, safely demonstrate the Wllama v3.8.1 integration boundary (self-hosted JS/WASM workers, model consent, offline requirements) without falsely claiming neural inference?

## Hypotheses and falsifiers

- H1: Tagged Wllama 3.8.1 supports an explicit local asset path configuration and explicit model loading, with no documented requirement for a network API. Falsifier: tagged source hard-codes a third-party service or cannot accept local WASM/worker paths.
- H2: A static proof can render clear no-model/no-inference state, explicit model consent, and refuse forbidden remote paths, even in a completely offline browser. Falsifier: tests reveal automatic network calls or misleading ready status.
- H3: Real Wllama inference requires additional files and browser-origin prerequisites beyond a single HTML file. Falsifier: official tagged docs demonstrate arbitrary file:// direct worker/WASM inference without browser origin requirements.

## Planned experiments

- S1 confirmatory: Inspect `therapybot` repository manifests/local embed to establish current Wllama dependency status; do not infer installed version.
- S2 confirmatory: Read official Wllama tag 3.8.1 README, package and compat integration instructions; inspect tagged runtime initialization and self-hosted worker API from first-party source where possible. Log exact links/identities.
- E1 confirmatory: Implement static HTML/JS self-hosted integration *contract probe* with no model weights or execution. It should display missing runtime/asset state and use only locally supplied paths.
- E2 confirmatory: Execute stdlib static/JS test(s), plus HTTP-served UI smoke test in local server/cloud browser only if supported; show no outward request when unconfigured. Capture exact exit codes/results.
- R1 confirmatory: Request independent subagent adversarial review of source-only proof; record verdict and unresolved external environment proof.

## Stopping rule

Close after primary-source tag inspection (three source lookups max), synthetic tests, and independent review request. If browser unavailable, label browser execution UNVERIFIED. Never download weights, publish, or write the shared repo.

## Evidence log

To be appended only; source labels and exact commands required.

### S1 — Project version inventory (confirmatory, 2026-11-04)

- SOURCE: local `/workspace/scratch/898f60fe057c/therapybot/embedded/README.md` and `embedded/index.html`; `rg -n -i 'wllama|wasm|webgpu|model' therapybot/...`.
- OBSERVATION: No installed browser Wllama in the embedded implementation. It is a deterministic conversation engine; genuine Wllama is proposed in docs. **No active installed version** to match, so research is pinned to a proposed exact release `3.8.1`.
- STATUS: COMPLETE; evidence class SOURCE_INSPECTION, not browser inference.

### S2 — Tag-matched primary-source contract (confirmatory, 2026-11-04)

- SOURCE: [ngxson/wllama README at 3.8.1](https://github.com/ngxson/wllama/blob/3.8.1/README.md), prior recorded Git blob `43915e6528c87d7fcee6a49d6cbf04b31a35e575`.
- OBSERVATION: WASM runs in browser worker; one-thread mode documented; multi-thread requires COOP/COEP headers; model files may be passed as local Blobs or loaded from URLs; docs recommend <=512 MB parts. Documentation also offers a **CDN WASM option**, which this prototype deliberately does not use.
- SOURCE: [3.8.1 compat README](https://github.com/ngxson/wllama/blob/3.8.1/compat/README.md), Git blob `1b3d101c67b059d502beebdd37a176c605578ed9`.
- OBSERVATION: Default compatibility fallback **fetches jsDelivr**. `setCompat({wasm:'local',worker:'local'})` explicitly overrides. Firefox compatibility mode can be slower.
- SOURCE: [3.8.1 `src/wllama.ts`](https://github.com/ngxson/wllama/blob/3.8.1/src/wllama.ts), Git blob `6ecbb68bebed16085bab341b96e3f7b67887a2c8`; [tagged basic example](https://github.com/ngxson/wllama/blob/3.8.1/examples/basic/index.html).
- OBSERVATION: Constructor initially sets CDN compatibility *configuration* but does not download model; page must override `setCompat` before load. `loadModel(Blob[])` directly accepts user-selected files, while `loadModelFromUrl` and `loadModelFromHF` initiate download management. `loadModel` accepts `n_threads:1`, `n_gpu_layers:0`. Tagged demo shows local asset paths and local file input.
- STATUS: COMPLETE. Contract supported by first-party source inspection; no actual runtime executed.

### E1 — Minimal source-only static page (confirmatory, 2026-11-04)

- ARTIFACT: `browser_probe/index.html`, `probe.css`, `probe-contract.mjs`, `probe.mjs`, `README.md`; all isolated, no external repo mutation. HTML has restrictive CSP and no auto-initialization. JS imports Wllama's self-hosted local module **only after file selection plus explicit consent**, sets local compat worker/WASM before `loadModel(selected.files, {...})`, no URL model loaders; conversation disabled unless load succeeded.
- EXACT SHA-256: `index.html` `be6fb6f3f0482f08af0a2cd49ef1ac27ee6b260a34265ea7416092e6f2975766`; `probe.css` `7bdf157e54ec091cecc58a64cd895500f19a45f6bac62d61d3abc11349ea6129`; `probe.mjs` `c9e73953bd8a629c7f1d7a512896da20278eddc5f896fc84d9cb5ed909d50894`; `probe-contract.mjs` `3a022f3af7367114886102e6e2c9e389c86f0e9e8f6f9b321e3a6c3ed982c9e9`.
- STATUS: COMPLETE as source-only proof, not actual Wllama load.

### E2 — Synthetic tests and browser blocker (confirmatory plus dead end, 2026-11-04)

- COMMAND: `node --test browser_probe/probe.test.mjs`; exit **0**, output **tests 5, pass 5, fail 0**. Tests cover gating, file size/type, only-local runtime paths, no remote script tags/CSP and mock DOM initial no-network/fail-closed missing module.
- COMMAND: `node --check browser_probe/probe.mjs && node --check browser_probe/probe-contract.mjs`; exit **0**.
- COMMAND: `python -m unittest test_validate_manifest.py`; exit **0**, **Ran 12 tests**, **OK** (previous custody lane).
- BROWSER DEAD END: Cloud Browser rejected `file:///workspace/.../browser_probe/index.html` with **protocol not allowed; http/https only; explicit direction not to circumvent via alternate browser surfaces**. No workaround attempted. The page was not observed in a real browser, and no screenshots can be claimed.
- STATUS: Synthetic E2 COMPLETE; browser UI smoke test UNVERIFIED. No downloads of Wllama JS/WASM or model weights.

### R1 — Independent review attempt (confirmatory, 2026-11-04)

- ATTEMPT: Replenish prior independent reviewer `/root/asset_independent_review` with exact browser proof paths and adversarial criteria.
- RESULT: Collaboration rejected followup with `agent thread limit reached`. Parent notified. Independent review for **this successor artifact** is **OPEN**, not silently replaced by the earlier manifest-only qualified pass.

### Current bounded verdict

- H1: **PARTIALLY SUPPORTED** by tag-matched source. Local `Blob[]` model loading and explicit local compat API are real documented/source interfaces. Full packaged asset closure and offline runtime behavior UNKNOWN.
- H2: **SUPPORTED BY 5 SYNTHETIC TESTS ONLY**. No genuine browser execution, model, WASM or network trace. UI must not be described as a functioning chat.
- H3: **SUPPORTED for multithreaded mode** by official COOP/COEP requirement and for runtime file dependency by tagged examples. Ordinary `file://` single-thread behavior remains UNKNOWN.
- Final independent verifier verdict: **OPEN** (agent slot limit). This research cannot be marked independently complete. Deployment/merge/medical-release gates remain closed.

### E3 — Reviewer falsifiers and exact red-green repair (confirmatory successor, 2026-11-04)

- SOURCE/REVIEW: independent native reviewer `chatgpt.therapybot.wllama_probe_hostile` Blotter **#4312** (same OpenAI provider), advised that `validateFiles()` accepted an ordinary metadata duck object `{name:'a.gguf',size:42,content:'not a model'}`, accepted mixed-case duplicate names, and could throw from a hostile `name` getter. This is **internal independent technical review**, not a separate provider or browser/security audit.
- ROOT CAUSE: `probe-contract.mjs` copied `Array.from()` and immediately trusted `file.name`/`file.size` as arbitrary JS properties. Neither `File`/`Blob` native brand nor binary signature was checked; duplicate key comparison was case-sensitive.
- RED REPRO (test added before code fix): `node --test browser_probe/probe.test.mjs` exit **1**, output `tests 6`, `pass 5`, `fail 1` and `AssertionError: Plain objects may not impersonate browser File instances` (`true !== false`). This is the smallest unattended symptom-specific regression test.
- REPAIR: require a genuine native `File` object; read name/size via native brand-checking `File.prototype` and `Blob.prototype` getters, catching errors; normalize filename for duplicates; bound size with a pure metadata checker; and asynchronously read the first 4 bytes via native Blob methods and require `GGUF` before local runtime module import. Module remains unbundled. Header check is **not** a complete GGUF format or model integrity assessment.
- GREEN: `node --test browser_probe/probe.test.mjs` exit **0**, output `tests 7`, `pass 7`, `fail 0`. Additional adversarial checks include `Object.create(File.prototype)` spoof, malicious name getter, casefold duplicate, genuine `File` containing non-GGUF body, and minimal `GGUF` magic proof. `node --check browser_probe/probe.mjs && node --check browser_probe/probe-contract.mjs` exit **0**.
- EXACT SHA-256 of post-fix files: `probe.mjs` `f7f1986d5eae43db0690533d82c0c15dcc979f59a34101182e20082bcdf100d9`; `probe-contract.mjs` `bb051090779ec5ad6652ffe6767d89572b3ff72e24e29ee65b2c225953dd47a2`; `probe.test.mjs` `8e9e6ac694c07243f9720a4c464b6c8877b0b83f922c3cd6f023294e448a94a9`; HTML `be6fb6f3f0482f08af0a2cd49ef1ac27ee6b260a34265ea7416092e6f2975766`; CSS `7bdf157e54ec091cecc58a64cd895500f19a45f6bac62d61d3abc11349ea6129`.
- POST-FIX REVIEW: sent exact SHA and tests to `/root/wllama_probe_hostile` and coordinator; **re-review result pending**. No real browser, WASM, network trace, downloaded weights, or public deployment was performed.

### E4 — Internal independent post-fix re-review (2026-11-04)

- SOURCE: Blotter **#4333**, actor `chatgpt.therapybot.wllama_probe_hostile`, internal independent native reviewer (same OpenAI provider/model family).
- OBSERVATION: Reviewer read the repaired source artifacts (validator SHA prefix `bb051090`, browser probe SHA prefix `f7f1986d`), reran **7/7 Node tests**, and independently challenged spoofed `File` values, own fake `size`/`name` getters, casefold-equivalent names, truncated/bad magic, proxy-wrapped File and minimal four-byte-only GGUF header.
- REVIEW VERDICT: **QUALIFIED PASS FOR SOURCE-ONLY RESEARCH**; Proxy-wrapped real Files remain backed by native slot data; a four-byte `GGUF` prefix is not a parser/integrity proof. This does not close runtime/rights/browser/safety gates. The earlier E3 “pending” was accurate at that time, and this is the append-only successor result.
- REMAINING: no actual browser, Wllama runtime, WASM, credentials, weights, no-CDN packet trace, model output, or clinical behavior validated. Public release remains blocked.
