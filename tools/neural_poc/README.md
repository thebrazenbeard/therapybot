# TherapyBot browser-local neural proof (isolated, UNQUALIFIED)

Source base: private TherapyBot draft PR #24 at `03d197e84021fd1f640561053acee9fabcb914e2`. This experiment is **not the released TherapyBot conversation UI, a clinical product, or a safety assessment**. It adds two selectable models for real opt-in local WASM inference, not a patient-facing model provider.

## Run an isolated test (Windows/Linux)

1. From `tools/neural_poc`: `npm ci --ignore-scripts --no-audit --no-fund` (installs only self-hosted Wllama 3.8.1 + compat).
2. Start a dedicated loopback-only static server from this directory, e.g. `py -m http.server 43877 --bind 127.0.0.1`. Verify port is free and avoid changing other services.
3. Open `http://127.0.0.1:43877/index.html`. No model is requested on page load. Select a model, optionally click the 32-byte GGUF preflight, explicitly check download consent, then click Download. The Generate button remains disabled until SHA-256 and actual WASM model load succeed.
4. Use only synthetic prompts. Runtime is CPU single-thread (`n_threads:1,n_gpu_layers:0,n_ctx:1024,n_parallel:1`); output is experimental and must not be used for clinical triage.
5. A browser model is downloaded once per explicit click with `fetch({cache:'no-store'})`, an expected-byte ceiling and exact SHA-256 check before load. The page never writes GGUF to CacheStorage, IndexedDB or a service worker. Static JS/WASM may still be cached by the browser.

## Pinned model selections

- **Default small:** `QuantFactory/SmolLM2-135M-Instruct-GGUF/SmolLM2-135M-Instruct.Q4_K_M.gguf`, exact Hugging Face revision `a6b7826ed969c3926a98359e39912af137b464cb`, size **105,454,144 bytes**, SHA-256 `8030f04528538d47bda434f6f0bdf3952c40a58123e4d5e755332f23731a8684`. Quantized from the Apache-2.0 `HuggingFaceTB/SmolLM2-135M-Instruct` family. License and source: https://huggingface.co/QuantFactory/SmolLM2-135M-Instruct-GGUF and https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct .
- **Preserved larger path:** official `Qwen/Qwen3-0.6B-GGUF/Qwen3-0.6B-Q4_K_M.gguf`, revision `1208e45d782fe18602c5eaf10e5758d5b0f24c03`, size **396,704,416 bytes**, SHA-256 `b0638f08417a2d3c8652760462eb5407c6e30173cf9608ad0820757a281eea0e`, Apache-2.0. **Full 397 MB inference remains untested**.

## Trust boundaries and reproducibility

- Runtime files are served locally from locked `@wllama/wllama@3.8.1` and `@wllama/wllama-compat@3.8.1`. Explicit `setCompat` avoids default jsDelivr asset fallback. CSP restricts scripts/workers to local and blob origins; model transfers to pinned Hugging Face/CDN origins only.
- Optional `click-smoke.cjs` drives **normal UI controls** under headless Edge/Firefox; `--puppeteer-dir /absolute/path/to/puppeteer`, `--port 43877` and `--firefox` select isolated runner configuration. No Puppeteer path is hardcoded into application source. Browser profiles/screenshots are ignored, and no GGUF belongs in Git or permanent Lappy storage.
- Initial independent direct tiny-model token test and single Edge normal-click SmolLM2 trial are **runtime probes**, not evaluations of therapeutic safety or quality. Conversation provider integration, counterfactual crisis handling, full-model performance, public privacy and release readiness remain unqualified.
