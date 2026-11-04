// Pure contract: no network APIs, model execution or ambient storage.
export const RUNTIME_VERSION = '3.8.1';
export const RUNTIME_PATHS = Object.freeze({
  module: './vendor/wllama/esm/index.js',
  wasm: './vendor/wllama/esm/wasm/wllama.wasm',
  compatWasm: './vendor/wllama-compat/wasm/wllama.wasm',
  compatWorker: './vendor/wllama-compat/wasm/wllama.js',
});
export const MAX_PART_BYTES = 512 * 1024 * 1024;
export const MAX_TOTAL_BYTES = 4 * 1024 * 1024 * 1024;

const REJECT_FILE = 'Only genuine browser-selected File objects are supported.';

export function validateFileMetadata(name, size) {
  if (typeof name !== 'string' || !/^[A-Za-z0-9][A-Za-z0-9._-]*\.gguf$/i.test(name)) {
    return {ok:false, reason:'Only named .gguf files are supported.'};
  }
  if (!Number.isSafeInteger(size) || size < 4 || size > MAX_PART_BYTES) {
    return {ok:false, reason:'Each part must contain a GGUF header and be at most 512 MiB.'};
  }
  return {ok:true, normalizedName:name.toLowerCase()};
}

export function validateFiles(fileLikeList) {
  let files;
  try { files=Array.from(fileLikeList ?? []); }
  catch { return {ok:false, reason:'Malformed file selection.'}; }
  if (files.length < 1 || files.length > 16) return {ok:false, reason:'Choose 1–16 local GGUF files.'};
  let total=0;
  const seen=new Set();
  for (const file of files) {
    // instanceof alone can be forged via Object.create(File.prototype), so
    // also read *native brand-checked* slots. Never invoke a hostile getter.
    if (typeof File !== 'function' || !(file instanceof File)) return {ok:false, reason:REJECT_FILE};
    let name, size;
    try {
      name=Object.getOwnPropertyDescriptor(File.prototype,'name').get.call(file);
      size=Object.getOwnPropertyDescriptor(Blob.prototype,'size').get.call(file);
    } catch { return {ok:false, reason:REJECT_FILE}; }
    const meta=validateFileMetadata(name,size);
    if (!meta.ok) return meta;
    if (seen.has(meta.normalizedName)) return {ok:false, reason:'Duplicate file names are not supported.'};
    seen.add(meta.normalizedName);
    total += size;
    if (total > MAX_TOTAL_BYTES) return {ok:false, reason:'Selected files exceed the 4 GiB cap.'};
  }
  return {ok:true, files, total};
}

export async function checkGGUFMagic(fileLikeList) {
  const selected=validateFiles(fileLikeList);
  if (!selected.ok) return selected;
  try {
    for (const file of selected.files) {
      const prefix=Blob.prototype.slice.call(file,0,4);
      const bytes=new Uint8Array(await Blob.prototype.arrayBuffer.call(prefix));
      if (bytes.length !== 4 || bytes[0] !== 0x47 || bytes[1] !== 0x47 || bytes[2] !== 0x55 || bytes[3] !== 0x46) {
        return {ok:false,reason:'The selected file does not start with GGUF magic bytes.'};
      }
    }
  } catch { return {ok:false,reason:'Could not inspect selected local file header.'}; }
  return {ok:true,files:selected.files,total:selected.total};
}

export function canLoad(fileLikeList, explicitConsent) {
  const selected = validateFiles(fileLikeList);
  return selected.ok && explicitConsent === true;
}

export function onlyLocalRuntimePaths(paths = RUNTIME_PATHS) {
  return Object.values(paths).every(p => typeof p === 'string'
    && /^\.\/vendor\/[A-Za-z0-9/_-]+\.(?:js|wasm)$/.test(p)
    && !p.includes('//') && !p.includes('..'));
}
