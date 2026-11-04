import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {canLoad, checkGGUFMagic, onlyLocalRuntimePaths, RUNTIME_PATHS, RUNTIME_VERSION, validateFileMetadata, validateFiles} from './probe-contract.mjs';

const file=(name,size)=>new File([new Uint8Array(Number.isFinite(size) && size>0 && size<2000 ? Math.ceil(size) : 0)],name);

test('zero-file and no-consent states deny runtime initialization',()=>{
  assert.equal(canLoad([],true),false);
  assert.equal(canLoad([file('small.gguf',1024)],false),false);
  assert.equal(canLoad([file('small.gguf',1024)],true),true);
});

test('files must be plausible GGUF, unique, nonempty and under each cap',()=>{
  for(const files of [
    [file('zero.gguf',0)], [file('too-big.gguf',563_000_000)],
    [file('model.bin',1024)], [file('.hidden.gguf',1024)],
    [file('model.gguf',4),file('model.gguf',4)],
    [file('model.gguf',Number.NaN)], [file('model.gguf',1.3)],
  ]) assert.equal(validateFiles(files).ok,false);
  assert.equal(validateFiles([file('a-00001-of-00002.gguf',4),file('a-00002-of-00002.gguf',4)]).ok,true);
  for(const size of [563_000_000,Number.NaN,1.3,0,3]) {
    assert.equal(validateFileMetadata('too-large.gguf',size).ok,false);
  }
});

test('all version-pinned runtime assets are local, rejecting URL and traversal injection',()=>{
  assert.equal(RUNTIME_VERSION,'3.8.1');
  assert.equal(onlyLocalRuntimePaths(),true);
  for(const poisoned of ['https://cdn.jsdelivr.net/esm/index.js','//evil.example/x.js','./vendor/../private.js','file:///etc/passwd']) {
    assert.equal(onlyLocalRuntimePaths({...RUNTIME_PATHS,module:poisoned}),false);
  }
});

test('HTML remains source-only, single-origin, and has no auto-imported runtime',async()=>{
  const html=await readFile(new URL('./index.html',import.meta.url),'utf8');
  assert.match(html,/connect-src 'self'/);
  assert.match(html,/worker-src 'self' blob:/);
  assert.match(html,/type="file"[^>]*accept="\.gguf"/);
  assert.match(html,/id="load-model"[^>]*disabled/);
  assert.doesNotMatch(html,/<script\s+[^>]*src="https?:/i);
});

test('unconfigured UI stays idle with no automatic network calls, fails closed on explicit load',async()=>{
  const ids=['model-files','load-consent','load-model','ask-model','prompt',
    'runtime-report','response','selection-report','isolation-report','chat-form'];
  const dom=Object.fromEntries(ids.map(id=>[id,{
    files:[],checked:false,disabled:true,textContent:'',value:'',
    handlers:{},addEventListener(kind,cb){this.handlers[kind]=cb},focus(){},
  }]));
  globalThis.document={getElementById(id){assert.ok(dom[id],id);return dom[id]}};
  globalThis.window={crossOriginIsolated:false};
  let fetchCalls=0;
  globalThis.fetch=async()=>{fetchCalls++;throw new Error('Unexpected fetch')};
  await import('./probe.mjs');
  assert.equal(fetchCalls,0);
  assert.equal(dom['load-model'].disabled,true);
  // The browser's initial status text comes from HTML; this minimal mock starts empty.
  assert.equal(dom['runtime-report'].textContent,'');
  dom['model-files'].files=[file('synthetic.gguf',123)];
  dom['load-consent'].checked=true;
  dom['model-files'].handlers.change();
  assert.equal(dom['load-model'].disabled,false);
  await dom['load-model'].handlers.click();
  assert.equal(fetchCalls,0);
  assert.equal(dom['ask-model'].disabled,true);
  assert.match(dom['runtime-report'].textContent,/Not initialized/);
  assert.match(dom['runtime-report'].textContent,/does not start with GGUF magic bytes/,
    'Header failure must occur before import of the absent Wllama module');
  delete globalThis.document;
  delete globalThis.window;
  delete globalThis.fetch;
});

test('adversarial forged metadata, mixed-case duplicate and throwing getter fail closed',()=>{
  assert.equal(validateFiles([{name:'a.gguf',size:42,content:'not a model'}]).ok,false,
    'Plain objects may not impersonate browser File instances');
  assert.equal(validateFiles([file('A.gguf',42),file('a.gguf',42)]).ok,false,
    'Casefold-equivalent names must not be accepted together');
  const malicious={size:42};
  Object.defineProperty(malicious,'name',{get(){throw new Error('hostile getter')}});
  assert.doesNotThrow(()=>validateFiles([malicious]));
  assert.equal(validateFiles([malicious]).ok,false);
  const prototypeSpoof=Object.create(File.prototype);
  assert.doesNotThrow(()=>validateFiles([prototypeSpoof]));
  assert.equal(validateFiles([prototypeSpoof]).ok,false);
});

test('real File with deceptive gguf extension but non-GGUF bytes fails header preflight',async()=>{
  const arbitrary=new File(['not a model'],'a.gguf');
  assert.equal(validateFiles([arbitrary]).ok,true,'Metadata alone cannot prove GGUF format');
  assert.equal((await checkGGUFMagic([arbitrary])).ok,false);
  const minimalHeader=new File(['GGUF','fake-body'],'a.gguf');
  assert.equal((await checkGGUFMagic([minimalHeader])).ok,true,
    'Magic check only, not full parser or valid model proof');
});
