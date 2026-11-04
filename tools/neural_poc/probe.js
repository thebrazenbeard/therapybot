// Isolated browser neural proof. No default download, persistence, runtime CDN, or clinical claim.
const CATALOG=Object.freeze({
  smol:Object.freeze({
    label:'SmolLM2 135M Instruct, Q4_K_M', size:105454144,
    sha:'8030f04528538d47bda434f6f0bdf3952c40a58123e4d5e755332f23731a8684',
    url:'https://huggingface.co/QuantFactory/SmolLM2-135M-Instruct-GGUF/resolve/a6b7826ed969c3926a98359e39912af137b464cb/SmolLM2-135M-Instruct.Q4_K_M.gguf',
    file:'SmolLM2-135M-Instruct.Q4_K_M.gguf', description:'105 MB licensed small instruction model; quality and safety are unqualified.'
  }),
  qwen:Object.freeze({
    label:'Qwen3 0.6B, Q4_K_M', size:396704416,
    sha:'b0638f08417a2d3c8652760462eb5407c6e30173cf9608ad0820757a281eea0e',
    url:'https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/resolve/1208e45d782fe18602c5eaf10e5758d5b0f24c03/Qwen3-0.6B-Q4_K_M.gguf',
    file:'Qwen3-0.6B-Q4_K_M.gguf', description:'397 MB experimental Qwen path; requires substantially more memory.'
  })
});
const byId=id=>document.getElementById(id);
const chooser=byId('model'),details=byId('model-info'),consentCopy=byId('consent-copy');
const consent=byId('consent'),filePicker=byId('file'),preflight=byId('preflight');
const download=byId('download'),loadFile=byId('load-file'),cancel=byId('cancel');
const status=byId('status'),prompt=byId('prompt'),generate=byId('generate'),reply=byId('reply');
const CORE_WASM=new URL('./node_modules/@wllama/wllama/esm/wasm/wllama.wasm',import.meta.url).href;
const COMPAT_WASM=new URL('./node_modules/@wllama/wllama-compat/wasm/wllama.wasm',import.meta.url).href;
const COMPAT_WORKER=new URL('./node_modules/@wllama/wllama-compat/wasm/wllama.js',import.meta.url).href;
let engine=null,busy=false,abort=null,activeModel=null;
function chosen(){return CATALOG[chooser.value]||CATALOG.smol}
function note(value){status.textContent=String(value)}
function ready(){
  const model=chosen(),mb=Math.round(model.size/1000000);
  details.textContent=model.description;
  consentCopy.textContent='I consent to this one-time '+mb+' MB test-model download from Hugging Face; no model is cached by this page.';
  download.textContent='Download and verify '+mb+' MB model';
  chooser.disabled=busy||!!engine;
  consent.disabled=busy||!!engine;
  filePicker.disabled=busy||!!engine;
  download.disabled=busy||!!engine||!consent.checked;
  loadFile.disabled=busy||!!engine||!filePicker.files?.length;
  preflight.disabled=busy||!!engine;
  cancel.disabled=!abort;
  generate.disabled=busy||!engine;
  prompt.disabled=!engine||busy;
}
chooser.addEventListener('change',()=>{consent.checked=false;filePicker.value='';note('Idle. No model loaded.');ready()});
consent.addEventListener('change',ready);
filePicker.addEventListener('change',ready);
ready();
async function verifyBytes(bytes,model){
  if(!(bytes instanceof ArrayBuffer)||bytes.byteLength!==model.size)throw new Error('Wrong file size; only selected pinned GGUF is accepted.');
  note('Checking SHA-256 for '+model.label+' in browser memory; extra RAM may briefly be needed.');
  const hash=await crypto.subtle.digest('SHA-256',bytes);
  const actual=Array.from(new Uint8Array(hash),b=>b.toString(16).padStart(2,'0')).join('');
  if(actual!==model.sha)throw new Error('Checksum mismatch; rejected before model load.');
  if(new TextDecoder().decode(new Uint8Array(bytes,0,4))!=='GGUF')throw new Error('GGUF signature missing.');
  return new File([bytes],model.file,{type:'application/octet-stream'});
}
async function inspect(file,model){
  if(!file||file.size!==model.size)throw new Error('Selected file does not match '+model.label+' size.');
  return verifyBytes(await file.arrayBuffer(),model);
}
async function readExactly(response,expected){
  const reader=response.body?.getReader();
  if(!reader)throw new Error('Readable response stream unavailable.');
  const bytes=new Uint8Array(expected);
  let offset=0;
  try{
    while(true){
      const part=await reader.read();
      if(part.done)break;
      if(offset+part.value.byteLength>expected)throw new Error('Download exceeded pinned size; canceled.');
      bytes.set(part.value,offset);offset+=part.value.byteLength;
    }
  }catch(err){try{await reader.cancel()}catch{}throw err}
  finally{reader.releaseLock()}
  if(offset!==expected)throw new Error('Transfer size mismatch '+offset+'/'+expected);
  return bytes.buffer;
}
async function initialize(verified,model){
  note('Loading self-hosted Wllama 3.8.1: '+model.label+'; no model API or external runtime.');
  const {Wllama}=await import('./node_modules/@wllama/wllama/esm/index.js');
  const candidate=new Wllama({default:CORE_WASM},{allowOffline:true});
  candidate.setCompat({wasm:COMPAT_WASM,worker:COMPAT_WORKER},'firefox_safari');
  const started=performance.now();
  try{
    await candidate.loadModel([verified],{n_threads:1,n_gpu_layers:0,n_ctx:1024,n_parallel:1,reasoning:false});
    engine=candidate;activeModel=model;
  }catch(err){try{await candidate.exit()}catch{}throw err}
  note('Loaded locally in '+((performance.now()-started)/1000).toFixed(1)+'s. Model output and safety remain unqualified.');
}
async function run(action){
  if(busy||engine)return;
  busy=true;abort=new AbortController();ready();
  try{await action()}catch(err){note('NOT LOADED: '+(err instanceof Error?err.message:String(err)))}
  finally{abort=null;busy=false;ready()}
}
preflight.addEventListener('click',()=>run(async()=>{
  const model=chosen();
  note('Fetching only first 32 bytes of selected pinned GGUF (CORS/header test).');
  const response=await fetch(model.url,{headers:{Range:'bytes=0-31'},cache:'no-store',signal:abort.signal});
  if(response.status!==206){await response.body?.cancel();throw new Error('Expected 206 Partial Content; refused whole download.')}
  const bytes=new Uint8Array(await readExactly(response,32));
  if(new TextDecoder().decode(bytes.subarray(0,4))!=='GGUF')throw new Error('Invalid 32-byte GGUF header.');
  note('CORS/Range preflight PASS for '+model.label+'. No model is loaded.');
}));
async function obtainVerifiedModel(model,signal){
  note('Downloading '+model.label+' after explicit consent; no persistent model cache.');
  const response=await fetch(model.url,{cache:'no-store',signal});
  if(!response.ok)throw new Error('Model download HTTP '+response.status);
  const header=Number(response.headers.get('content-length'));
  if(header&&header!==model.size){await response.body?.cancel();throw new Error('Unexpected Content-Length '+header)}
  return verifyBytes(await readExactly(response,model.size),model);
}
download.addEventListener('click',()=>run(async()=>{
  if(!consent.checked)throw new Error('Explicit model download consent required.');
  const model=chosen();
  await initialize(await obtainVerifiedModel(model,abort.signal),model);
}));
loadFile.addEventListener('click',()=>run(async()=>{
  const model=chosen();
  await initialize(await inspect(filePicker.files?.[0],model),model);
}));
cancel.addEventListener('click',()=>{if(abort){abort.abort();note('Cancellation requested; an already-started model load may continue.')}});
byId('chat').addEventListener('submit',async event=>{
  event.preventDefault();
  if(!engine||busy||!prompt.value.trim())return;
  busy=true;ready();
  reply.textContent='Generating locally with '+activeModel.label+' (test-only)…';
  const started=performance.now();
  try{
    const instruction='Experimental test assistant. Reply concisely. Not a therapist, clinician, or crisis assessor.';
    const text=prompt.value.slice(0,800);
    const response=await engine.createChatCompletion({
      messages:[{role:'system',content:instruction},{role:'user',content:text}],
      max_tokens:64,temperature:0.4
    });
    const raw=String(response?.choices?.[0]?.message?.content||'');
    const visible=raw.replace(/<think>[\s\S]*?<\/think>/g,'').replace(/<think>[\s\S]*$/g,'').trim();
    reply.textContent=(visible||'(No visible model reply.)')+'\n\nTime: '+((performance.now()-started)/1000).toFixed(1)+'s. No clinical reliability established.';
  }catch(err){reply.textContent='Local generation failed: '+(err instanceof Error?err.message:String(err))}
  finally{busy=false;ready()}
});
