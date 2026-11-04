# TherapyBot experimental browser conversation lab

This is a **source-only, unshipped, rules-based** visitor interface. It is not an LLM, medically validated product, emergency response service, or production safety classifier. It should not be promoted to users in its present form. The conversation is interactive and uses the existing browser-local TherapyBot embedded semantic engine and adapter from PR #24.

## Local preview

From the repository root, run:

    python pages/lab/build_preview.py --out <new-empty-directory-outside-repo>

Then serve the staged directory on an isolated localhost-only HTTP server or use a browser with file access enabled. This command is for the **developer**, not future visitors. A future hosted static page would require no installation, account, API key, or user-run CLI.

The output includes **only** the three lab UI files and three approved JavaScript runtime files. It deliberately excludes Python backend, datasets, personal information, vault files, neural models, and any other repository content. It creates no cache. No fetch, telemetry, browser persistence, or model download occurs. Opening the page alone makes no requests for remote weights or cloud inference.

Run tests from anywhere:

    python -m unittest discover -s pages/lab -p test_preview.py -v
    node pages/lab/test_browser_turn.cjs

The Node smoke executes two genuine local adapter turns and verifies transcript clearing; it does not replace browser compatibility or safety testing.

## Release / hostile-review gate

- **Not published or merged:** the existing Pages workflow publishes the pages tree; do not merge this lab into a deployed branch before an explicit release decision. Source-only is not a privacy or behavior verification.
- Test a real user-submitted turn in Chrome, Firefox, and a constrained mobile browser, plus blank, multi-turn, reset, malformed, unsafe, and hostile HTML input cases.
- Screen for accessible keyboard navigation, screen reader transcript announcement, and viewport/scroll behavior.
- Conduct independent emergency and self-harm response evaluation. Existing reports indicate unacceptable emergency-route false negatives; **do not claim safe user deployment**.
- Any future neural option must be explicit opt-in after disclosure of first-use model download size, license, versioned Wllama runtime, memory footprint, and no-persistent-cache status. It must not silently replace this rules engine or imply clinical utility.
- Verify source hashes, license notices, CSP network boundary, and real Chrome/Firefox WebAssembly behavior before changing the static Pages publish path.

No keys, third-party tracking, analytics, accounts, local storage, remote inference, or browser model weights are part of this lab.
