# Browser model asset custody — pre-registered investigation

Frozen 2026-11-04 before external documentation retrieval.

## Question

Can a TherapyBot developer-only browser neural adapter use a source-only, $0, local/offline asset manifest with independently checkable provenance and fail-closed validation, without promising inference, clinical safety, or redistribution rights not proved by the evidence?

## Hypotheses and falsifiers

- H1: Wllama's documented browser runtime can be self-hosted without a mandatory third-party CDN for runtime assets. Falsifier: official current integration docs require external CDN or proprietary managed service.
- H2: At least one small GGUF candidate publishes accessible machine-readable size, immutable revision, model-license information and checksums suitable for a future explicit model-asset manifest. Falsifier: no inspectable rights/revision/digests are available.
- H3: A source-only validator can reject missing SHA-256, mutable asset URLs, broad cross-origin fetches, out-of-range byte sizes, unsupported file kinds, unpinned versions, and accidental default network download, using synthetic fixtures. Falsifier: deliberately invalid fixtures pass.

## Planned experiments

- R1 (confirmatory): Inspect local TherapyBot manifests/lockfiles for installed neural runtime/version, then retrieve current primary-source Wllama docs and relevant official files. Record citation URLs and date.
- R2 (confirmatory): Inspect primary-source Hugging Face model files/model-card metadata for Qwen3.5-0.8B and one alternative. Separate base-model rights from conversion/distribution permissions; leave claims unresolved if source incomplete.
- E1 (confirmatory): Implement original Python schema/validator + synthetic unit tests. Run tests and record command, exit code and decisive lines.
- E2 (confirmatory): Test malformed manifests (untrusted external URL, mutable revision, missing digest, invalid offline policy) and a plausible pinned manifest. No model weights download.

## Stopping rule

Stop after three primary-source documentation lookups, an executed standalone validator test suite, and an independent check request. Unknown rights/compatibility remain blockers; no remote push or model download.

## Evidence log

Entries to be appended below. No evidence yet.

### E-R1 — Local installation inventory (confirmatory; 2026-11-04)

- SOURCE: `therapybot/README.md`, `docs/REPOSITORY_RESIDENT_MODEL.md`, and `embedded/README.md`, searched with `rg -n 'wllama|web-llm|transformers.js|onnx|GGUF|model_manifest' ...`.
- OBSERVATION: Wllama is proposed, **not installed as a browser inference dependency**. The embedded engine is deterministic JS and no neural weights are delivered. Local repo, not external docs, is authority for current implementation.
- STATUS: `R1` local-version phase COMPLETE; no installed Wllama to version-match, so looked up latest official release, then pinned docs to tag.

### E-R2 — Wllama official version and self-hosting (confirmatory; 2026-11-04)

- SOURCE: [GitHub latest release](https://github.com/ngxson/wllama/releases/tag/3.8.1), `ngxson/wllama@3.8.1/package.json` (`Git blob 1dd1d6e17fab0f9036bcafd86566adc25fa33c89`) and `README.md` (`Git blob 43915e6528c87d7fcee6a49d6cbf04b31a35e575`).
- OBSERVATION: Latest GitHub release returned tag **3.8.1**, 2026-10-02; package declares version `3.8.1` and MIT. WASM browser inference and optional WebGPU are documented. V3.1 introduction document is historically relevant but NOT the current version.
- SOURCE: `ngxson/wllama@3.8.1/compat/README.md` (`Git blob 1b3d101c67b059d502beebdd37a176c605578ed9`).
- OBSERVATION: The compat README explicitly warns that fallback fetches jsDelivr assets by default, and documents local wasm+worker paths that prevent that default dependency. This supports *design feasibility*, not actual no-network testing.
- STATUS: `R1` source phase COMPLETE; H1 partially supported, no executable runtime probe.

### E-R3 — Pinned GGUF source metadata (confirmatory; 2026-11-04)

- SOURCE: [Pinned ggml-org/Qwen3.5-0.8B Q4_0 file](https://huggingface.co/ggml-org/Qwen3.5-0.8B-GGUF/blob/9447f74101aeb4e93621884dfa36ee8effb8831b/Qwen3.5-0.8B-Q4_0.gguf), [upstream Qwen](https://huggingface.co/Qwen/Qwen3.5-0.8B).
- OBSERVATION: Source UI shows Apache-2.0, rounded **563 MB** size and SHA-256 `57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf`. No bytes downloaded/hashed locally.
- SOURCE: [Pinned bartowski/SmolLM2-360M-Instruct Q4_K_M file](https://huggingface.co/bartowski/SmolLM2-360M-Instruct-GGUF/blob/ddde4293f6050e8b81cca2ea2438c2fe444a0d5b/SmolLM2-360M-Instruct-Q4_K_M.gguf), [upstream SmolLM2](https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct).
- OBSERVATION: Source UI shows Apache-2.0, rounded **271 MB** size and SHA-256 `2fa3f013dcdd7b99f9b237717fa0b12d75bbb89984cc1274be1471a465bac9c2`. No bytes downloaded/hashed locally.
- STATUS: `R2` source phase COMPLETE; H2 partially supported. Exact byte lengths and redistribution sign-off unknown.

### E-D1 — Unavailable HF metadata endpoint (dead end; exploratory)

- ATTEMPT: Web open on Hugging Face `/api/models/.../tree/<commit>?recursive=1` for exact byte lengths.
- RESULT: Tool rejected URL as inaccessible. Did not infer exact bytes from rounded MB. No alternative credentials, network bypass, or asset download attempted.
- STATUS: CLOSED dead end. A future authorized model-asset packaging step should retrieve verifiable byte lengths through supported primary-source tooling.

### E-E1 — Original source-only manifest validator (confirmatory; 2026-11-04)

- ARTIFACTS: `validate_manifest.py`, `asset_manifest.schema.json`, `test_validate_manifest.py`, all inside this isolated folder. Python validator is more restrictive than the draft JSON Schema for path and URL semantics.
- COMMAND: `python -m unittest -v test_validate_manifest.py`
- RESULT: exit **0**, `Ran 10 tests in 0.012s`, `OK`. Positive fixture structurally accepted; pending rights prevents readiness; synthetic bytes/hash verification passes for exact bytes and fails after tampering. The suite deliberately rejects malformed digests, mutable version, wrong commit, path traversal, CDN/remote path, automatic network fetch, privacy/storage policy violation, unknown fields, duplicates, oversized asset and symlink.
- COMMAND: `python -m json.tool asset_manifest.schema.json`
- RESULT: exit **0** (JSON syntax valid); **Draft2020-12 validation was not executed** because the `jsonschema` library was unavailable in this scratch Python runtime (`ModuleNotFoundError`). Do not claim schema/validator parity.
- STATUS: `E1` and `E2` COMPLETE at unit-fixture level, not actual model-asset level.

### Provisional verdict (independent pass pending)

- H1: **PARTIAL** — version-pinned documentation supports self-hosted Wllama assets, but browser/no-network behavior was not executed.
- H2: **PARTIAL** — source hashes and declared Apache-2.0 found; exact local bytes and redistribution review unknown.
- H3: **SUPPORTED ONLY BY LOCAL TESTS** — ten synthetic tests pass; no third-party schema conformance or production threat model review.
- Release implication: No model packaged, no browser neural inference verified, no clinical/behavioral qualification. This is a developer custody guardrail candidate, not a TherapyBot capability.
- Independent verdict: **OPEN**. Parent coordinator has been asked to assign a distinct reviewer when a slot opens. Self-verification will not be labeled independent.

### E-RV1 — Independent adversarial review and bounded corrections (2026-11-04)

- EVIDENCE CLASS: **INTERNAL_INDEPENDENT_AGENT_REVIEW** from native ChatGPT subagent `/root/asset_independent_review` (same OpenAI provider/model family, not an independent provider), forwarded by parent coordinator. Reviewer inspected isolated pre-fix artifacts (not a Git commit); post-fix SHA256 values are recorded below. Distinguish reviewer findings from my local test observations.
- REVIEW findings: malformed JSON value types could raise Python `TypeError`; malformed `https://[` can raise `ValueError`; nested directory symlinks resolving within the bundle could bypass leaf-only symlink checks; draft schema was looser than Python rules; self-declared rights clearance cannot prove actual review; source Qwen file is larger than the conservative per-file bound.
- FIXES: Enforce string type on asset roles and rights clearance; catch `urlsplit` `ValueError`; check *each* intermediate path component for symlinks; add lexical path and HTTPS primary-source restrictions to Draft2020-12 schema; pin runtime exactly `3.8.1`; explicitly reject monolithic Qwen 563 MB candidate under 512 MiB asset limit (future splitting is a separate qualification). Document self-asserted rights as insufficient for release.
- TEST: `python -m unittest -v test_validate_manifest.py` exit **0**; **12/12 synthetic tests passed**, including intermediate in-root directory symlink, malformed bracketed IPv6 URLs, object/list role and rights clearance values, numerically valid but wrong runtime versions, and 563,000,000-byte declared asset refusal. `python -m py_compile validate_manifest.py test_validate_manifest.py` exit **0**. `python -m json.tool asset_manifest.schema.json` exit **0**.
- CURRENT FILE HASHES (SHA-256, post-fix): `validate_manifest.py` `7deffce6544ab641565d167f007f0f125ac6fc6587f3f18262308a8cd771e9d4`; `asset_manifest.schema.json` `594341a9dc2571ed5b5a46f5dce98af8f8eacc2e6d661f3bc159a9d59ddd87cf`; `test_validate_manifest.py` `05da15204b9fe5968db885ec707ed830e75b87ae9dfc469e1b51117920fdca14`. Post-fix final label `rights_self_assertion_required` explicitly avoids `ready_claim` terminology; regression suite remains 12/12 pass.
- RESIDUAL: No Draft2020-12 runtime validation; no actual JS/WASM/GGUF tested; no exact source file length verified; no independent rights review proof. `verify_local_assets` checks paths then opens them and is not hardened against a concurrent local adversary replacing files/symlinks during that gap. Do not treat source-level validation as an adversarial secure installer.
- POST-FIX VERDICT: `/root/asset_independent_review` independently re-read the exact final three artifact SHA-256 files above and ran all **12/12** synthetic tests. It additionally probed malformed roles/rights, invalid URL syntax and spoofed hosts, encoded traversal, incorrect hashes, oversized files, unsupported versions, and intermediate directory symlinks. All previously raised cases were controlled rejections. **QUALIFIED PASS** for *developer-only source-only manifest validator integration*; `INTERNAL_INDEPENDENT_AGENT_REVIEW`, same OpenAI provider/model family, **not external** security/clinical/legal review. Reviewer logged Blotter **#4263**.
- RESIDUALS UNCHANGED: Draft2020-12 full schema execution, actual bytes, real browser inference/offline behavior, legal redistribution decision, clinical suitability, and filesystem concurrent replacement resistance remain **UNVERIFIED**. No user-facing neural model capability or safe public release can be inferred.
