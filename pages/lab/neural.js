/* Explicit opt-in experimental browser neural inference, not clinical advice. */
const MODEL = Object.freeze({
  label: 'SmolLM2-135M-Instruct Q4_K_M',
  size: 105454144,
  hash: '8030f04528538d47bda434f6f0bdf3952c40a58123e4d5e755332f23731a8684',
  url: 'https://huggingface.co/QuantFactory/SmolLM2-135M-Instruct-GGUF/resolve/a6b7826ed969c3926a98359e39912af137b464cb/SmolLM2-135M-Instruct.Q4_K_M.gguf'
});
const core = new URL('./runtime/wllama/esm/wasm/wllama.wasm', import.meta.url);
const compatWasm = new URL('./runtime/wllama-compat/wasm/wllama.wasm', import.meta.url);
const compatWorker = new URL('./runtime/wllama-compat/wasm/wllama.js', import.meta.url);
const runtimePaths = [core, compatWasm, compatWorker];
let instance = null;
let loading = false;
let generating = false;

function info(callback, message) {
  if (typeof callback === 'function') callback(message);
}
async function ensureLocalRuntime(signal) {
  for (const path of runtimePaths) {
    const reply = await fetch(path, { method:'HEAD', cache:'no-store', signal });
    if (!reply.ok) throw new Error('Self-hosted Wllama 3.8.1 assets are absent; no model was downloaded.');
  }
}
async function readExact(response, signal, progress) {
  const sizeHeader = Number(response.headers.get('content-length'));
  if (sizeHeader && sizeHeader !== MODEL.size) {
    await response.body?.cancel();
    throw new Error('Model Content-Length differs from pinned bytes.');
  }
  if (!response.ok || !response.body?.getReader()) throw new Error('Model download could not start.');
  const reader = response.body.getReader();
  const bytes = new Uint8Array(MODEL.size);
  let offset = 0;
  try {
    while (true) {
      if (signal?.aborted) throw new DOMException('Canceled', 'AbortError');
      const part = await reader.read();
      if (part.done) break;
      if (offset + part.value.byteLength > MODEL.size) throw new Error('Model exceeded pinned size.');
      bytes.set(part.value, offset);
      offset += part.value.byteLength;
      if (offset % (8*1024*1024) < part.value.byteLength) {
        info(progress,'Downloading verified model: ' + Math.round(100*offset/MODEL.size) + '%');
      }
    }
  } catch (error) {
    try { await reader.cancel(); } catch (_) {}
    throw error;
  } finally { reader.releaseLock(); }
  if (offset !== MODEL.size) throw new Error('Model transfer ended before pinned size.');
  return bytes.buffer;
}
async function verify(bytes) {
  if (bytes.byteLength !== MODEL.size || new TextDecoder().decode(new Uint8Array(bytes,0,4)) !== 'GGUF') {
    throw new Error('Model bytes or GGUF signature incorrect.');
  }
  const digest = await crypto.subtle.digest('SHA-256',bytes);
  const hash = Array.from(new Uint8Array(digest),x=>x.toString(16).padStart(2,'0')).join('');
  if (hash !== MODEL.hash) throw new Error('Pinned SHA-256 mismatch; model refused.');
  return new File([bytes], 'SmolLM2-135M-Instruct.Q4_K_M.gguf', {type:'application/octet-stream'});
}
async function load(options={}) {
  if (loading || generating) throw new Error('Model operation already running.');
  if (instance) return;
  const { signal, onStatus } = options;
  loading = true;
  let candidate = null;
  try {
    info(onStatus,'Checking self-hosted Wllama assets before model transfer…');
    await ensureLocalRuntime(signal);
    const { Wllama } = await import('./runtime/wllama/esm/index.js');
    info(onStatus,'Downloading 105 MB after explicit consent; no application model cache.');
    const response = await fetch(MODEL.url, {cache:'no-store',signal});
    const bytes = await readExact(response,signal,onStatus);
    info(onStatus,'Verifying exact SHA-256; temporary memory usage may be high…');
    const file = await verify(bytes);
    if (signal?.aborted) throw new DOMException('Canceled','AbortError');
    candidate = new Wllama({default:core.href},{allowOffline:true});
    candidate.setCompat({wasm:compatWasm.href,worker:compatWorker.href},'firefox_safari');
    info(onStatus,'Initializing local CPU model. Please wait…');
    await candidate.loadModel([file], {
      n_threads:1,n_gpu_layers:0,n_ctx:1024,n_parallel:1,reasoning:false
    });
    instance = candidate;
    info(onStatus,'Opt-in model loaded locally. Responses remain unqualified.');
  } catch (error) {
    if (candidate) { try { await candidate.exit(); } catch (_) {} }
    throw error;
  } finally { loading = false; }
}
async function respond(history) {
  if (!instance) throw new Error('Experimental neural model is not loaded.');
  if (generating) throw new Error('A neural reply is still generating.');
  generating = true;
  try {
    const recent = history.filter(x=>['user','assistant'].includes(x.role))
      .slice(-6).map(x=>({role:x.role,content:String(x.content).slice(0,320)}));
    const completion = await instance.createChatCompletion({
      messages:[
        {role:'system',content:'Experimental small-model chat. Be brief and acknowledge uncertainty. Never claim to be a therapist, clinician or emergency assessor.'},
        ...recent
      ],
      max_tokens:64,temperature:0.4
    });
    const raw = String(completion?.choices?.[0]?.message?.content || '');
    const visible = raw.replace(/<think>[\s\S]*?<\/think>/g,'')
      .replace(/<think>[\s\S]*$/g,'').trim().slice(0,2400);
    return visible || 'The local model returned no visible text.';
  } finally { generating = false; }
}
window.TherapyBotNeural = Object.freeze({
  model: MODEL,
  load, respond,
  isLoaded:()=>Boolean(instance),
  isBusy:()=>loading||generating
});
