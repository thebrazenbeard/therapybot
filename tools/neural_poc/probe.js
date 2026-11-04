// Isolated real-inference experiment. No auto-download, persistence, CDN runtime or clinical claim.
const PINNED='https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/resolve/1208e45d782fe18602c5eaf10e5758d5b0f24c03/Qwen3-0.6B-Q4_K_M.gguf';
const EXPECTED_SIZE=396704416;
const EXPECTED_SHA='b0638f08417a2d3c8652760462eb5407c6e30173cf9608ad0820757a281eea0e';
const byId=id=>document.getElementById(id);
const consent=byId('consent'),filePicker=byId('file'),preflight=byId('preflight');
const download=byId('download'),loadFile=byId('load-file'),cancel=byId('cancel');
const status=byId('status'),prompt=byId('prompt'),generate=byId('generate'),reply=byId('reply');
const CORE_WASM=new URL('./node_modules/@wllama/wllama/esm/wasm/wllama.wasm',import.meta.url).href;
const COMPAT_WASM=new URL('./node_modules/@wllama/wllama-compat/wasm/wllama.wasm',import.meta.url).href;
const COMPAT_WORKER=new URL('./node_modules/@wllama/wllama-compat/wasm/wllama.js',import.meta.url).href;
let engine=null,busy=false,abort=null,verifiedBytes=0;
function note(value){status.textContent=String(value)}
function ready(){download.disabled=busy||!!engine||!consent.checked;loadFile.disabled=busy||!!engine||!filePicker.files?.length;preflight.disabled=busy;generate.disabled=busy||!engine;prompt.disabled=!engine||busy}
consent.addEventListener('change',ready);filePicker.addEventListener('change',ready);ready();
async function verifyBytes(bytes){
  if(!(bytes instanceof ArrayBuffer)||bytes.byteLength!==EXPECTED_SIZE)throw new Error('Only the pinned 396,704,416-byte GGUF is accepted in this pilot.');
  note('Checking SHA-256 of '+bytes.byteLength+' bytes in browser memory; this may briefly require extra RAM.');
  const dig=await crypto.subtle.digest('SHA-256',bytes);
  const sha=Array.from(new Uint8Array(dig),b=>b.toString(16).padStart(2,'0')).join('');
  if(sha!==EXPECTED_SHA)throw new Error('Checksum mismatch; rejected before loading.');
  if(new TextDecoder().decode(new Uint8Array(bytes,0,4))!=='GGUF')throw new Error('GGUF signature missing.');
  verifiedBytes=bytes.byteLength;
  return new File([bytes],'Qwen3-0.6B-Q4_K_M.gguf',{type:'application/octet-stream'});
}
async function inspect(file){
  if(!file||file.size!==EXPECTED_SIZE)throw new Error('Only the pinned 396,704,416-byte GGUF is accepted in this pilot.');
  return verifyBytes(await file.arrayBuffer());
}
async function initialize(verified){
  note('Importing self-hosted Wllama 3.8.1; no external runtime or model API.');
  const {Wllama}=await import('./node_modules/@wllama/wllama/esm/index.js');
  const candidate=new Wllama({default:CORE_WASM},{allowOffline:true});
  candidate.setCompat({wasm:COMPAT_WASM,worker:COMPAT_WORKER},'firefox_safari');
  const started=performance.now();
  try {
    await candidate.loadModel([verified],{n_threads:1,n_gpu_layers:0,n_ctx:1024,n_parallel:1,reasoning:false});
    engine=candidate;
  }catch(err){try{await candidate.exit()}catch{} throw err}
  note('Loaded locally in '+((performance.now()-started)/1000).toFixed(1)+'s; verified '+verifiedBytes+' bytes; safety and output are unqualified.');
}
async function run(action){
  if(busy||engine)return;
  busy=true;ready();abort=new AbortController();
  try {await action()} catch(err){note('NOT LOADED: '+(err instanceof Error?err.message:String(err)))}
  finally {abort=null;busy=false;ready()}
}
preflight.addEventListener('click',()=>run(async()=>{
  note('Fetching only first 32 bytes of pinned model to test browser CORS and GGUF magic.');
  const response=await fetch(PINNED,{headers:{Range:'bytes=0-31'},cache:'no-store',signal:abort.signal});
  if(response.status!==206)throw new Error('Expected HTTP 206 Range response, received '+response.status);
  const bytes=new Uint8Array(await response.arrayBuffer());
  if(bytes.length!==32||new TextDecoder().decode(bytes.subarray(0,4))!=='GGUF')throw new Error('Header did not match expected 32-byte GGUF range.');
  note('CORS/Range preflight PASS: 32 bytes only from '+new URL(response.url).host+'. No model is loaded.');
}));
async function obtainVerifiedModel(signal){
  note('Downloading the pinned 397 MB GGUF after consent (no persistent cache).');
  const response=await fetch(PINNED,{cache:'no-store',signal});
  if(!response.ok)throw new Error('Model download HTTP '+response.status);
  const headerSize=Number(response.headers.get('content-length'));
  if(headerSize&&headerSize!==EXPECTED_SIZE)throw new Error('Unexpected model Content-Length '+headerSize);
  const bytes=await response.arrayBuffer();
  if(bytes.byteLength!==EXPECTED_SIZE)throw new Error('Download size mismatch: '+bytes.byteLength);
  return verifyBytes(bytes);
}
download.addEventListener('click',()=>run(async()=>{
  if(!consent.checked)throw new Error('Explicit download consent is required.');
  await initialize(await obtainVerifiedModel(abort.signal));
}));
loadFile.addEventListener('click',()=>run(async()=>{await initialize(await inspect(filePicker.files?.[0]))}));
cancel.addEventListener('click',()=>{if(abort){abort.abort();note('Download/header request canceled. No model loaded.')}});
byId('chat').addEventListener('submit',async event=>{
  event.preventDefault();
  if(!engine||busy||!prompt.value.trim())return;
  busy=true;ready();reply.textContent='Generating locally (experimental; no medical advice)…';
  const t=performance.now();
  try{
    const response=await engine.createChatCompletion({
      messages:[{role:'system',content:'Experimental concise assistant. Do not claim medical qualifications. /no_think'},{role:'user',content:prompt.value.slice(0,800)+' /no_think'}],
      max_tokens:96,temperature:0.4
    });
    const raw=String(response?.choices?.[0]?.message?.content||'');
    const visible=raw.replace(/<think>[\s\S]*?<\/think>/g,'').replace(/<think>[\s\S]*$/g,'').trim();
    reply.textContent=(visible||'(No visible reply; model may have emitted only reasoning tokens.)')+'\n\nTime: '+((performance.now()-t)/1000).toFixed(1)+'s. Unvalidated output.';
  }catch(err){reply.textContent='Local generation failed: '+(err instanceof Error?err.message:String(err))}
  finally{busy=false;ready()}
});
