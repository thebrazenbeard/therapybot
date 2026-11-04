import {RUNTIME_PATHS, validateFiles, checkGGUFMagic, canLoad, onlyLocalRuntimePaths} from './probe-contract.mjs';

const el=id=>document.getElementById(id);
const filesInput=el('model-files');
const consent=el('load-consent');
const load=el('load-model');
const ask=el('ask-model');
const prompt=el('prompt');
const status=el('runtime-report');
const answer=el('response');
let instance=null;
let busy=false;

function refresh() {
  const result=validateFiles(filesInput.files);
  el('selection-report').textContent=result.ok
    ? `${result.files.length} file(s) selected (${(result.total/1048576).toFixed(1)} MiB). Content and rights not verified.`
    : result.reason;
  filesInput.disabled=busy || instance!==null;
  consent.disabled=busy || instance!==null;
  load.disabled=busy || instance!==null || !canLoad(filesInput.files, consent.checked);
}

filesInput.addEventListener('change', refresh);
consent.addEventListener('change', refresh);
el('isolation-report').textContent = `Cross-origin isolated: ${window.crossOriginIsolated ? 'yes' : 'no'}. This probe requests CPU-only, single-thread mode; multithreading requires COOP/COEP HTTP headers.`;
refresh();

load.addEventListener('click', async () => {
  if (busy || instance || !onlyLocalRuntimePaths() || !canLoad(filesInput.files, consent.checked)) return;
  const selected=validateFiles(filesInput.files);
  busy=true;refresh();status.textContent='Trying local Wllama assets and selected files…';
  let candidate=null;
  try {
    const header=await checkGGUFMagic(selected.files);
    if (!header.ok) throw new Error(header.reason);
    // Never load a CDN runtime, call loadModelFromHF, or fetch a remote GGUF.
    // This import fails cleanly in the source-only fixture (runtime not bundled).
    const {Wllama}=await import(RUNTIME_PATHS.module);
    candidate=new Wllama({default:RUNTIME_PATHS.wasm}, {allowOffline:true});
    // Explicit local fallback even on Firefox. Tagged docs warn this can be slow.
    candidate.setCompat({wasm:RUNTIME_PATHS.compatWasm, worker:RUNTIME_PATHS.compatWorker}, 'firefox_safari');
    // User-picked File/Blob objects bypass the URL downloader entirely.
    await candidate.loadModel(selected.files, {n_threads:1, n_gpu_layers:0, n_ctx:1024});
    instance=candidate;
    status.textContent='Local model initialized. This proves load only, not reply safety or clinical quality.';
    prompt.disabled=false;ask.disabled=false;prompt.focus();
  } catch(err) {
    if (candidate) { try { await candidate.exit(); } catch {} }
    status.textContent='Not initialized: local runtime/model could not load. No inference occurred. '+(err instanceof Error ? err.message : String(err));
  } finally {busy=false;refresh()}
});

el('chat-form').addEventListener('submit', async event => {
  event.preventDefault();
  if (busy || !instance || !prompt.value.trim()) return;
  busy=true;ask.disabled=true;answer.textContent='Generating locally…';
  try {
    const response=await instance.createChatCompletion({messages:[{role:'user',content:prompt.value.slice(0,1000)}],max_tokens:100,temperature:0.5});
    answer.textContent=response?.choices?.[0]?.message?.content || '(The local model returned no message.)';
  } catch(err) {answer.textContent='Local inference failed: '+(err instanceof Error ? err.message : String(err))}
  finally {busy=false;ask.disabled=false}
});
