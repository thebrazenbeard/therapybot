"use strict";

// The launch fragment is never sent in HTTP requests. Keep the capability only
// in this tab's session storage; never put it in localStorage, HTML or logs.
const launchedToken = new URLSearchParams(location.hash.slice(1)).get("access");
let accessToken = launchedToken || "";
try {
  if (launchedToken) sessionStorage.setItem("therapybotAccess", launchedToken);
  else accessToken = sessionStorage.getItem("therapybotAccess") || "";
} catch (_) { /* Some browsers disallow session storage; current tab still works. */ }
if (launchedToken) history.replaceState(null, "", location.pathname + location.search);

const $ = (id) => document.getElementById(id);
const memory = [];
let unlocked = false;
let busy = false;
let locking = false;
let chatAbortController = null;
let requestGeneration = 0;
let toastTimer;
const tabChannel = typeof BroadcastChannel === "function" ? new BroadcastChannel("therapybot-vault-events") : null;
if (tabChannel) tabChannel.onmessage = (event) => {
  if (event.data?.type === "vault-revoked" || event.data?.type === "vault-locked") {
    requestGeneration += 1;
    if (chatAbortController) chatAbortController.abort();
    setVaultState(false);
    $("unlockError").textContent = "Another tab changed the vault session. Restart TherapyBot for a new private link if needed.";
  }
};

function rememberToken(value) {
  if (typeof value !== "string" || !value) return;
  accessToken = value;
  try { sessionStorage.setItem("therapybotAccess", value); } catch (_) { /* In-memory only. */ }
}

async function api(path, options = {}) {
  const method = options.method || "GET";
  const headers = { Accept: "application/json" };
  if (!options.public) {
    if (!accessToken) throw new Error("Open the full private link from the TherapyBot terminal to access your vault.");
    headers["X-TherapyBot-Token"] = accessToken;
  }
  if (method !== "GET") headers["Content-Type"] = "application/json";
  const result = await fetch(path, {
    method,
    headers,
    body: method === "GET" ? undefined : JSON.stringify(options.body || {}),
    cache: "no-store",
    credentials: "omit",
    mode: "same-origin",
    signal: options.signal
  });
  let json;
  try { json = await result.json(); } catch (_) { throw new Error(`Local server returned HTTP ${result.status}.`); }
  if (!result.ok) throw new Error(json.error || `Local server returned HTTP ${result.status}.`);
  return json;
}

function toast(message, isError = false) {
  const element = $("toast");
  element.textContent = String(message);
  element.classList.toggle("error", isError);
  element.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { element.hidden = true; }, 4900);
}

function node(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = String(text);
  return element;
}

function safeExternalLink(url, title) {
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== "https:") return node("span", "tiny-muted", title);
    const anchor = node("a", "source-link", title);
    anchor.href = parsed.href;
    anchor.target = "_blank";
    anchor.rel = "noopener noreferrer";
    return anchor;
  } catch (_) {
    return node("span", "tiny-muted", title);
  }
}

function showView(name) {
  for (const element of document.querySelectorAll(".view")) {
    const active = element.id === `view-${name}`;
    element.hidden = !active;
    element.classList.toggle("active", active);
  }
  for (const button of document.querySelectorAll(".nav-button")) {
    const active = button.dataset.view === name;
    button.classList.toggle("active", active);
    if (active) button.setAttribute("aria-current", "page");
    else button.removeAttribute("aria-current");
  }
  $("viewBreadcrumb").textContent = ({chat:"Conversation", journal:"Journal", history:"History", sources:"Knowledge", privacy:"Privacy"})[name] || name;
  if (name === "history" && unlocked) loadHistory();
  if (name === "sources") loadSources();
}

function setVaultState(isUnlocked) {
  const wasUnlocked = unlocked;
  unlocked = isUnlocked;
  $("unlockOverlay").hidden = isUnlocked;
  $("lockButton").disabled = !isUnlocked;
  $("vaultStatus").textContent = `Vault: ${isUnlocked ? "unlocked" : "locked"}`;
  $("vaultStatus").classList.toggle("muted", !isUnlocked);
  if (!isUnlocked && wasUnlocked) {
    memory.length = 0;
    $("messages").replaceChildren();
    $("messages").appendChild(node("p", "tiny-muted", "Session cleared. Unlock to continue."));
    $("saveHistory").checked = false;
    $("chatInput").value = "";
    $("journalInput").value = "";
    $("historySearch").value = "";
    $("sourceSearch").value = "";
    $("historyResults").replaceChildren();
    $("passphraseInput").value = "";
  }
  if (isUnlocked && !wasUnlocked && !$("messages").querySelector(".empty-chat")) {
    const welcome = node("div", "empty-chat");
    welcome.appendChild(node("h2", "", "What’s on your mind?"));
    welcome.appendChild(node("p", "", "Start anywhere. You decide whether to save the conversation."));
    $("messages").replaceChildren(welcome);
  }
}

async function refreshStatus() {
  if (locking) return;
  const generation = requestGeneration;
  try {
    const status = await api("/api/status", { public: true });
    if (locking || generation !== requestGeneration) return;
    $("modelStatus").textContent = status.model_configured ? "Model: configured (not verified)" : "Model: not configured";
    $("modelStatus").title = status.model_configured ? status.model_url : "Start a local KoboldCPP/llama.cpp server to enable AI replies.";
    if (!accessToken) {
      $("unlockError").textContent = "Open the private link from the TherapyBot terminal. Direct access to this address cannot unlock the vault.";
      $("unlockButton").disabled = true;
    } else if (status.unlocked) {
      // A valid capability is required for private routes, even when the process is unlocked.
      try {
        const session = await api("/api/session");
        if (locking || generation !== requestGeneration) return;
        if (!session.unlocked) { setVaultState(false); return; }
        if (!locking && generation === requestGeneration) setVaultState(true);
      }
      catch (_) {
        if (locking || generation !== requestGeneration) return;
        setVaultState(false);
        $("unlockError").textContent = "Your access link has expired. Restart TherapyBot to open a fresh private link.";
        $("unlockButton").disabled = true;
      }
    } else setVaultState(false);
  } catch (error) {
    if (locking || generation !== requestGeneration) return;
    $("modelStatus").textContent = "Local server unavailable";
    $("unlockError").textContent = error.message;
  }
}

async function unlockVault(event) {
  event.preventDefault();
  if (busy || locking) return;
  requestGeneration += 1; // invalidate any status request begun before unlock
  const passphrase = $("passphraseInput").value;
  $("unlockError").textContent = "";
  if (passphrase.length < 12) return $("unlockError").textContent = "Use at least 12 characters.";
  busy = true;
  $("unlockButton").disabled = true;
  try {
    const response = await api("/api/vault", { method: "POST", body: { passphrase } });
    rememberToken(response.token);
    setVaultState(true);
    refreshStatus();
    if (tabChannel) tabChannel.postMessage({ type: "vault-revoked" });
    showView("chat");
    $("chatInput").focus();
    toast("Vault unlocked locally.");
  } catch (error) {
    $("unlockError").textContent = error.message;
  } finally {
    busy = false;
    $("unlockButton").disabled = !accessToken;
    $("passphraseInput").value = "";
  }
}

async function lockVault() {
  if (locking || !unlocked) return;
  locking = true;
  requestGeneration += 1;
  if (chatAbortController) chatAbortController.abort();
  chatAbortController = null;
  busy = false;
  $("sendButton").disabled = false;
  // Clear sensitive local UI immediately, even if inference is still running.
  setVaultState(false);
  $("vaultStatus").textContent = "Vault: locking…";
  if (tabChannel) tabChannel.postMessage({ type: "vault-locked" });
  try {
    const response = await api("/api/lock", { method: "POST" });
    rememberToken(response.token);
    $("vaultStatus").textContent = "Vault: locked";
    $("passphraseInput").focus();
    toast("Vault locked. Session messages cleared.");
  } catch (error) {
    $("vaultStatus").textContent = "Vault: lock unconfirmed";
    toast("Could not confirm server lock. Stop TherapyBot in its terminal. " + error.message, true);
  } finally { locking = false; }
}

function addMessage(role, text, sources = [], mode = "") {
  const list = $("messages");
  const placeholder = list.querySelector(".empty-chat");
  if (placeholder) placeholder.remove();
  const bubble = node("article", `message ${role}`);
  const heading = node("div", "message-label", role === "user" ? "YOU" : role === "assistant" ? "THERAPYBOT" : "SYSTEM");
  bubble.appendChild(heading);
  bubble.appendChild(node("div", "message-text", text));
  if (role === "assistant" && Array.isArray(sources) && sources.length) {
    const sourcesBox = node("div", "message-sources");
    sourcesBox.appendChild(node("span", "tiny-muted", "Related reading (not verification of every claim): "));
    for (const source of sources.slice(0, 5)) {
      if (typeof source?.url === "string" && typeof source?.title === "string") sourcesBox.appendChild(safeExternalLink(source.url, source.title));
    }
    bubble.appendChild(sourcesBox);
  }
  if (mode === "local-model") bubble.appendChild(node("div", "tiny-muted", "Local model · Claims not clinically verified"));
  if (mode === "safety") bubble.appendChild(node("div", "tiny-muted", "Safety fallback · Not emergency monitoring"));
  list.appendChild(bubble);
  list.scrollTop = list.scrollHeight;
}

async function sendMessage() {
  if (!unlocked || busy) return;
  const input = $("chatInput");
  const text = input.value.trim();
  if (!text) return input.focus();
  busy = true;
  const generation = ++requestGeneration;
  chatAbortController = new AbortController();
  $("sendButton").disabled = true;
  input.value = "";
  addMessage("user", text);
  try {
    const response = await api("/api/chat", {
      method: "POST",
      body: {
        text,
        style: $("styleSelect").value,
        depth: $("depthSelect").value,
        history: memory.slice(-16),
        save_history: $("saveHistory").checked
      },
      signal: chatAbortController.signal
    });
    if (!unlocked || generation !== requestGeneration) return;
    memory.push({ role: "user", text }, { role: "assistant", text: response.reply.slice(0, 8000) });
    if (memory.length > 16) memory.splice(0, memory.length - 16);
    addMessage("assistant", response.reply, response.sources, response.mode);
  } catch (error) {
    if (unlocked && generation === requestGeneration && error.name !== "AbortError") addMessage("system", error.message);
  } finally {
    if (generation === requestGeneration) {
      busy = false;
      chatAbortController = null;
      $("sendButton").disabled = false;
      if (unlocked) input.focus();
    }
  }
}

async function saveJournal() {
  if (!unlocked) return;
  const generation = requestGeneration;
  const text = $("journalInput").value.trim();
  if (!text) return toast("Write an entry before saving.", true);
  const mood = $("moodInput").value;
  try {
    await api("/api/journal", { method: "POST", body: { text, mood: mood === "" ? null : Number(mood) } });
    if (!unlocked || generation !== requestGeneration) return;
    $("journalInput").value = "";
    $("moodInput").value = "";
    toast("Journal entry saved in your encrypted vault.");
  } catch (error) { if (unlocked && generation === requestGeneration) toast(error.message, true); }
}

function emptyResult(target, message) {
  target.replaceChildren(node("p", "tiny-muted", message));
}

async function loadHistory() {
  if (!unlocked) return;
  const generation = requestGeneration;
  const target = $("historyResults");
  emptyResult(target, "Searching encrypted records…");
  try {
    const q = $("historySearch").value.trim();
    const response = await api("/api/records" + (q ? `?q=${encodeURIComponent(q.slice(0, 200))}` : ""));
    if (!unlocked || generation !== requestGeneration) return;
    target.replaceChildren();
    if (!response.records.length) return emptyResult(target, "No saved records match. Conversation history is opt-in.");
    for (const record of [...response.records].reverse()) {
      const article = node("article", "result-item");
      const top = node("div", "result-heading");
      top.appendChild(node("strong", "", record.kind === "journal" ? "Journal entry" : record.data.role === "user" ? "Your message" : "TherapyBot reply"));
      const date = Number.isFinite(record.created) ? new Date(record.created * 1000).toLocaleString() : "Unknown date";
      top.appendChild(node("span", "tiny-muted", date));
      article.appendChild(top);
      article.appendChild(node("p", "result-text", record.data.text || ""));
      if (record.kind === "journal" && record.data.mood !== null && record.data.mood !== undefined) article.appendChild(node("span", "tiny-muted", `Mood: ${record.data.mood}/10`));
      const remove = node("button", "text-button danger", "Delete record");
      remove.type = "button";
      remove.addEventListener("click", async () => {
        if (!confirm("Delete this saved record? This does not erase independent backups or downloaded exports.")) return;
        try { await api("/api/delete", { method: "POST", body: { id: record.id } }); await loadHistory(); toast("Record deleted from active vault."); }
        catch (error) { toast(error.message, true); }
      });
      article.appendChild(remove);
      target.appendChild(article);
    }
  } catch (error) { if (unlocked && generation === requestGeneration) emptyResult(target, error.message); }
}

async function loadSources() {
  const target = $("sourceResults");
  emptyResult(target, "Searching local knowledge library…");
  try {
    const q = $("sourceSearch").value.trim();
    const response = await api(`/api/sources?q=${encodeURIComponent(q.slice(0, 200))}`, { public: true });
    target.replaceChildren();
    if (!response.sources.length) return emptyResult(target, "No matching curated references.");
    for (const source of response.sources) {
      const article = node("article", "result-item");
      const heading = node("div", "result-heading");
      heading.appendChild(node("strong", "", source.title));
      heading.appendChild(node("span", "tiny-muted", source.institution || source.evidence_type || "Source"));
      article.appendChild(heading);
      article.appendChild(node("p", "result-text", source.summary));
      article.appendChild(safeExternalLink(source.url, "Read primary source ↗"));
      target.appendChild(article);
    }
  } catch (error) { emptyResult(target, error.message); }
}

async function exportRecords() {
  if (!unlocked) return;
  if (!confirm("Download all saved records as UNENCRYPTED JSON? Anyone with this file can read its contents.")) return;
  const generation = requestGeneration;
  try {
    const result = await api("/api/export");
    if (!unlocked || generation !== requestGeneration) return;
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `therapybot-export-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    toast("Plaintext export downloaded. Store it securely.");
  } catch (error) { if (unlocked && generation === requestGeneration) toast(error.message, true); }
}

async function downloadEncryptedBackup() {
  if (!unlocked || !accessToken) return;
  if (!confirm("Download an encrypted backup of your local vault? You will need your original passphrase to restore it.")) return;
  const generation = requestGeneration;
  try {
    const response = await fetch("/api/backup", {
      headers: { "X-TherapyBot-Token": accessToken },
      cache: "no-store",
      credentials: "omit",
      mode: "same-origin"
    });
    if (!response.ok) {
      let message = `Backup failed (HTTP ${response.status}).`;
      try { message = (await response.json()).error || message; } catch (_) { /* Non-JSON error. */ }
      throw new Error(message);
    }
    const bytes = await response.arrayBuffer();
    if (!unlocked || generation !== requestGeneration) return;
    const blob = new Blob([bytes], { type: "application/octet-stream" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `therapybot-backup-${new Date().toISOString().slice(0, 10)}.tbbak`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    toast("Encrypted backup downloaded. Store it safely with your passphrase.");
  } catch (error) {
    if (unlocked && generation === requestGeneration) toast(error.message, true);
  }
}

document.querySelectorAll(".nav-button").forEach((button) => button.addEventListener("click", () => showView(button.dataset.view)));
document.querySelectorAll(".suggestion").forEach((button) => button.addEventListener("click", () => { $("chatInput").value = button.textContent; $("chatInput").focus(); }));
$("openSourcesButton").addEventListener("click", () => showView("sources"));
$("unlockForm").addEventListener("submit", unlockVault);
$("lockButton").addEventListener("click", lockVault);
$("sendButton").addEventListener("click", sendMessage);
$("chatInput").addEventListener("keydown", (event) => { if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) { event.preventDefault(); sendMessage(); } });
$("saveJournalButton").addEventListener("click", saveJournal);
$("searchHistoryButton").addEventListener("click", loadHistory);
$("historySearch").addEventListener("keydown", (event) => { if (event.key === "Enter") loadHistory(); });
$("searchSourcesButton").addEventListener("click", loadSources);
$("sourceSearch").addEventListener("keydown", (event) => { if (event.key === "Enter") loadSources(); });
$("exportButton").addEventListener("click", exportRecords);
$("backupButton").addEventListener("click", downloadEncryptedBackup);
document.addEventListener("visibilitychange", () => { if (!document.hidden) refreshStatus(); });
window.addEventListener("focus", () => { refreshStatus(); });
refreshStatus();
