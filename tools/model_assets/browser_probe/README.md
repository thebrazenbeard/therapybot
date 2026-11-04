# Static browser neural boundary probe (source-only)

This is an isolated **UI and integration-contract prototype** for TherapyBot.
No Wllama runtime JavaScript, WASM, compatibility worker, GGUF weights,
account, API key, inference server, or third-party CDN is bundled.
Opening it therefore starts **no model**. Even after selecting a fake/real file
and consenting, model load correctly fails until independently verified and
rights-reviewed local runtime assets are placed in the documented paths.

## Proposed all-local asset layout

The tagged [Wllama 3.8.1 README](https://github.com/ngxson/wllama/blob/3.8.1/README.md)
shows `Wllama({default:'.../esm/wasm/wllama.wasm'})` and passing selected
`File`/`Blob` objects via `loadModel(files)`; the
[compat README](https://github.com/ngxson/wllama/blob/3.8.1/compat/README.md)
warns that the default compatibility path fetches jsDelivr and documents
explicit self-hosted wasm + worker URLs. The
[tagged implementation](https://github.com/ngxson/wllama/blob/3.8.1/src/wllama.ts)
confirms `setCompat({wasm,worker},'firefox_safari')`, `loadModel(Blob[])`,
`n_threads:1`, and `n_gpu_layers:0`.

If a later rights/security gate approves bundling runtime assets, they must be
integrity checked at these same-origin paths, all beneath this directory:

```
vendor/wllama/esm/index.js
vendor/wllama/esm/wasm/wllama.wasm
vendor/wllama-compat/wasm/wllama.wasm
vendor/wllama-compat/wasm/wllama.js
```

The JS import may require additional packaged sibling files: **not mapped or
audited yet**. These example paths are not proof that copying four files is
sufficient. Use an asset build manifest with exact size + SHA-256, immutable
version provenance, and a verified offline dependency closure. Never wire the
upstream `WasmFromCDN` export, default CDN-compatible fallback, HF model URL,
or model auto-download into the release.

## Behavior represented by this proof

1. At boot, no model is initialized and no runtime module is imported.
2. The user chooses **genuine browser File objects** with `.gguf` names
   (1–16; max 512 MiB/part and 4 GiB total), then explicitly opts into
   loading. The contract reads native File/Blob getters rather than arbitrary
   object properties; it rejects case-insensitive duplicate names, throwing
   property getters, and fake objects inheriting from `File.prototype`.
   Before importing the runtime, it checks each file's first four bytes for
   `GGUF` magic. This is **not** a full GGUF parser, checksum verification,
   trusted model evidence, or rights check; a forged magic header can pass.
3. Only after both actions does the page dynamic-import its **local** runtime
   module, set local compat assets *before model loading*, and invoke the Blob
   path. There is no `loadModelFromHF` or `loadModelFromUrl` invocation.
4. If assets are absent, fail closed and keep conversation disabled.
5. If a future validated runtime and model load, a short chat uses local
   `createChatCompletion`; no transcript is intentionally persisted by this app.

The restrictive inline CSP permits local static assets and WASM evaluation,
same-origin requests and blob workers; it does not grant an internet-origin
fallback. CSP is defense in depth; it does **not** independently audit
third-party vendored JS or the browser's network trace. A service worker is
**not** installed, so offline reopening of an HTTP-served page is not yet
guaranteed. A local static HTTP server is not a model/inference backend;
ordinary `file://` module/worker loading is browser dependent and **untested**.

The page requests CPU-only single-thread inference, avoiding a multithread
dependency on COOP/COEP. For multithreading the tagged Wllama README requires
`Cross-Origin-Opener-Policy` and `Cross-Origin-Embedder-Policy` HTTP headers.
The Firefox compatibility fallback is explicitly local, but the tagged docs
warn it can be slow. Performance has not been tested.

## Synthetic tests

```bash
node --test browser_probe/probe.test.mjs
node --check browser_probe/probe.mjs
```

The mocked DOM test proves initial idle state, explicit consent gating,
adversarial File object rejection and fail-closed non-GGUF header behavior,
**not an actual browser or WASM load**.
No CLI tests here download anything.

### Release blockers

- Independent runtime asset hash/licensing and package dependency-closure audit.
- Browser tests in Firefox/Edge, including CSP, worker, WASM, static-hosting
  headers, network logs and memory usage, all on actual release bytes.
- Exact model bytes/checksums and rights; Qwen3.5-0.8B Q4_0 monolith is above
  the prototype's 512 MiB per-part cap and cannot be used as-is.
- Human review of model behavior, privacy and crisis response before public use.
