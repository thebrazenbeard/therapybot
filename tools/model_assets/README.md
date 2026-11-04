# TherapyBot browser-neural model asset custody — isolated prototype

**Development only, not connected to TherapyBot, not distributed, no downloaded weights.**

This folder contains an original source-only safety boundary for eventual Wllama
browser inference. `asset_manifest.schema.json` describes the JSON shape;
`validate_manifest.py` enforces its stricter path/HTTPS/commit/memory/size policy
and optionally verifies actual on-disk bytes. The runtime and any model are
**not implemented here**.

## Source evidence at 2026-11-04

| Asset candidate | Primary source | Verified metadata | Missing qualification |
|---|---|---|---|
| `@wllama/wllama` **3.8.1** | [Official release](https://github.com/ngxson/wllama/releases/tag/3.8.1), [tagged package](https://github.com/ngxson/wllama/blob/3.8.1/package.json) | MIT declared in tagged package; browser WASM llama.cpp binding, WebGPU optional, worker and split-model support in tagged README | Executable asset SHA-256, browser compatibility/performance, cost of first download |
| Wllama compatibility bundle | [Tagged compat instructions](https://github.com/ngxson/wllama/blob/3.8.1/compat/README.md) | Default compat may fetch **jsDelivr** unless local WASM+worker URLs are supplied; explicit self-hosting documented | Full network-isolation proof; Firefox/Safari device performance |
| Qwen3.5-0.8B `Q4_0` | [Pinned GGUF file](https://huggingface.co/ggml-org/Qwen3.5-0.8B-GGUF/blob/9447f74101aeb4e93621884dfa36ee8effb8831b/Qwen3.5-0.8B-Q4_0.gguf); [upstream model](https://huggingface.co/Qwen/Qwen3.5-0.8B) | HF listing: Apache-2.0, rounded size **563 MB**, file SHA-256 `57d1997790d1744fba5b40a7317df71ea5e2acee28c47e78f0cce39c0703f8cf` | **REJECT AS-IS**: single GGUF exceeds current 512 MiB policy. Exact bytes unconfirmed; split format, new per-chunk hashes and memory safety require separate qualification |
| SmolLM2-360M-Instruct `Q4_K_M` | [Pinned community GGUF](https://huggingface.co/bartowski/SmolLM2-360M-Instruct-GGUF/blob/ddde4293f6050e8b81cca2ea2438c2fe444a0d5b/SmolLM2-360M-Instruct-Q4_K_M.gguf); [upstream model](https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct) | HF listing: Apache-2.0, rounded size **271 MB**, file SHA-256 `2fa3f013dcdd7b99f9b237717fa0b12d75bbb89984cc1274be1471a465bac9c2` | Exact bytes, conversion/repackaging sign-off, browser behavior, conversation quality |

The human-readable model-card license label is **evidence about declared licensing**,
not a legal clearance judgment for a new redistributed package. The validator
intentionally never sets `rights_clearance` itself. `reviewed` is a supplied
claim; whoever packages assets must separately document rights review.

Do **not** silently translate the source digest of a monolithic GGUF to a split
GGUF chunk: the chunk SHA-256 and exact size are different bytes and must be
computed after splitting. This prototype doesn't download, split, cache,
execute, or provide any ready model.

## Manifest contract

- Version 1 only. Pinned exact 40-hex source revision and **exact Wllama
  `3.8.1`** runtime version, source URL bound to revision, explicit SPDX/evidence pointer.
- Bundled relative paths under `assets/` or `vendor/` only: no `http(s):`, CDN,
  file URLs, `../`, `%` escapes, query strings, drive letters, or symlinks.
- Mandatory local runtime JS, runtime WASM, compat WASM and compat worker,
  plus 1–16 GGUF parts. Each declared with exact byte length and SHA-256.
- Per-part limit 512 MiB (conservative packaging policy), total <=4 GiB,
  manifest <=64 KiB, unknown fields rejected.
- Explicit download consent required; no automatic download, no external
  runtime fetch, offline-after-install required, private data absent, and
  conversation persistence defaults to none.
- Structural validation and even matching checksums **do not** establish
  clinical efficacy, no-network behavior of vendored code, model quality,
  licensing truth, GGUF format validity, or browser compatibility.

The JSON Schema adds lexical path/HTTPS restrictions; the Python validator
remains stricter (including source URL↔revision equality and symlink ancestry).
Draft 2020-12 schema validation has **not** been run in this environment.

## Developer commands

```bash
python -m unittest -v test_validate_manifest.py
python validate_manifest.py path/to/manifest.json
python validate_manifest.py path/to/manifest.json --verify-files path/to/bundle-root
```

The final command refuses any manifest with `rights_clearance: pending` and
compares each local asset's exact byte size and digest after checking for
symlink/path escapes. It performs **no network calls**.

### Remaining acceptance gates

1. Obtain exact file lengths and verify asset digests from downloaded bytes,
   with versioned runtime/npm artifacts and licenses included.
2. Pin and separately review model and converter provenance; document rights
   decisions and redistribution obligations.
3. Verify all Wllama WASM, worker and JS runtime files are self-hosted with
   network instrumentation (including compat fallbacks), and no remote model
   request occurs without explicit user consent.
4. Exercise actual browser model inference in Firefox/Edge on representative
   RAM/CPU/GPU profiles; measure first load and offline repeat. Test `file://`
   explicitly; it may not support required WASM/worker fetch semantics.
5. Keep mental-health support publicly disabled until independent behavioral,
   privacy, accessibility and appropriate clinical review gates are met.
