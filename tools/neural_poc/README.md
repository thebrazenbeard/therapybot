# TherapyBot browser-local neural proof (isolated, UNQUALIFIED)

Source base: private TherapyBot PR #24, exact head `03d197e84021fd1f640561053acee9fabcb914e2`.
This is a **local scratch branch**, not an application deployment, clinical product, or completed neural inference proof.

- Windows isolated path: `D:\VERA\scratch\bt2-therapybot-neural-poc-20261104\tools\neural_poc`.
- `npm ci --ignore-scripts --no-audit --no-fund` after generating/committing package lock, then `py -m http.server 43187 --bind 127.0.0.1` from this directory (port must be free).
- Browse `http://127.0.0.1:43187/index.html`; no automatic model request. Click **Test only 32-byte model header/CORS** first.
- Only explicit checkbox then button permits one 396,704,416-byte GGUF GET; `fetch` uses `cache:'no-store'`, no CacheStorage/IndexedDB/service worker. Browser startup still may cache static JS/WASM under own profile; do not store downloaded GGUF.
- Model: official Qwen/Qwen3-0.6B-GGUF `Qwen3-0.6B-Q4_K_M.gguf`, pinned revision `1208e45d782fe18602c5eaf10e5758d5b0f24c03`; SHA256 `b0638f08417a2d3c8652760462eb5407c6e30173cf9608ad0820757a281eea0e`, Apache-2.0.
- Runtime: self-hosted `@wllama/wllama@3.8.1` + compat `@wllama/wllama-compat@3.8.1`, local wasm+worker; explicit `setCompat` disables jsDelivr CDN fallback, CSP blocks third-party runtime scripts.
- Params: CPU only (`n_threads:1,n_gpu_layers:0,n_ctx:1024,n_parallel:1`). No transcript egress programmed; use synthetic prompts only.
- Real Edge and Firefox preconsent: no external requests; explicit 32-byte Range preflight PASS from Hugging Face redirect to `us.aws.cdn.hf.co`. **Full model fetch / token generation NOT TESTED**; no claim of local inference success or therapeutic safety.
- To repeat smoke: `node smoke.cjs` and `node smoke.cjs --firefox`. Puppeteer is referenced through the Lappy Executor runtime absolute path (test-only environment coupling).
- Do not commit `node_modules` or browser profiles. No model weights belong in the repository or permanently on Lappy.
