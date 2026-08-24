const invoke = (command, args) => window.__TAURI__.core.invoke(command, args);

const $ = (id) => document.getElementById(id);
const HISTORY_KEY = "mikoo.desktop.history.v1";
let history = JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
let activePrompt = "";

function saveHistory() {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(history.slice(-40)));
}

function setState(label, kind = "") {
  const state = $("agent-state");
  state.textContent = label;
  state.className = `state-pill ${kind}`.trim();
}

function appendMessage(role, text, pending = false) {
  const transcript = $("transcript");
  const message = document.createElement("article");
  message.className = `message ${role}${pending ? " pending" : ""}`;
  const label = document.createElement("div");
  label.className = "label";
  label.textContent = role === "user" ? "You" : "Mikoo";
  const body = document.createElement("div");
  body.textContent = text;
  message.append(label, body);
  transcript.append(message);
  transcript.scrollTop = transcript.scrollHeight;
  return message;
}

function showView(name) {
  document.querySelectorAll(".view").forEach((view) => view.classList.remove("active-view"));
  $(`view-${name}`).classList.add("active-view");
  document.querySelectorAll(".nav-item").forEach((button) => button.classList.toggle("active", button.dataset.view === name));
  if (window.innerWidth <= 900) {
    $("sidebar").classList.remove("open");
    $("menu-button").setAttribute("aria-expanded", "false");
  }
  if (name === "history") renderHistory();
}

function renderHistory() {
  const list = $("history-list");
  list.innerHTML = "";
  if (!history.length) {
    list.innerHTML = '<div class="empty-panel">No local conversations yet.</div>';
    return;
  }
  [...history].reverse().forEach((entry) => {
    const item = document.createElement("div");
    item.className = "history-entry";
    item.textContent = entry.prompt;
    const date = document.createElement("small");
    date.textContent = new Date(entry.createdAt).toLocaleString();
    item.append(date);
    item.addEventListener("click", () => {
      showView("chat");
      $("transcript").innerHTML = "";
      appendMessage("user", entry.prompt);
      appendMessage("assistant", entry.response);
      setState("RESTORED");
      activePrompt = entry.prompt;
    });
    list.append(item);
  });
}

async function sendPrompt(prompt) {
  const value = prompt.trim();
  if (!value) return;
  activePrompt = value;
  showView("chat");
  $("suggestions").style.display = "none";
  appendMessage("user", value);
  const pending = appendMessage("assistant", "Mikoo is thinking locally…", true);
  setState("THINKING", "thinking");
  $("send-button").disabled = true;
  $("stop-button").disabled = false;
  try {
    const response = await invoke("generate_response", { prompt: value, maxTokens: 768, contextTokens: 1024 });
    pending.remove();
    appendMessage("assistant", response);
    history.push({ prompt: value, response, createdAt: new Date().toISOString() });
    saveHistory();
    setState("REPLIED");
    $("runtime-status").textContent = "Offline local model • output ≤768 byte-tokens • history saved locally";
  } catch (error) {
    pending.remove();
    appendMessage("assistant", `Local runtime error: ${String(error)}`);
    setState("ERROR", "error");
    $("runtime-status").textContent = "Offline local runtime error; no remote fallback was used";
  } finally {
    $("send-button").disabled = false;
    $("stop-button").disabled = true;
  }
}

async function loadModel() {
  try {
    const status = await invoke("load_model");
    $("runtime-status").textContent = `${status} • output ≤768 byte-tokens`;
    $("agent-model").textContent = "Mikoo Nano local checkpoint";
    setState("READY");
  } catch (error) {
    $("runtime-status").textContent = `Local model unavailable: ${String(error)}`;
    setState("ERROR", "error");
  }
}

window.addEventListener("DOMContentLoaded", () => {
  $("menu-button").addEventListener("click", () => {
    const open = $("sidebar").classList.toggle("open");
    $("menu-button").setAttribute("aria-expanded", String(open));
  });
  document.querySelectorAll(".nav-item").forEach((button) => button.addEventListener("click", () => showView(button.dataset.view)));
  document.querySelectorAll("[data-prompt]").forEach((button) => button.addEventListener("click", () => sendPrompt(button.dataset.prompt)));
  $("composer-form").addEventListener("submit", (event) => { event.preventDefault(); sendPrompt($("prompt-input").value); $("prompt-input").value = ""; });
  $("stop-button").disabled = true;
  $("stop-button").addEventListener("click", async () => {
    try { await invoke("cancel_generation"); } catch (_) { /* local cancellation is best effort */ }
    setState("CANCELLED");
  });
  $("clear-button").addEventListener("click", () => {
    $("transcript").innerHTML = '<div class="welcome">Start a private offline coding session. Your prompt and response stay in this desktop profile.</div>';
    $("suggestions").style.display = "flex";
    setState("READY");
  });
  $("workspace-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const path = $("workspace-input").value.trim();
    if (!path) return;
    try {
      const result = await invoke("validate_workspace", { path });
      $("workspace-result").textContent = result;
    } catch (error) {
      $("workspace-result").textContent = `Workspace error: ${String(error)}`;
    }
  });
  $("transcript").innerHTML = '<div class="welcome">Start a private offline coding session. Your prompt and response stay in this desktop profile.</div>';
  loadModel();
  renderHistory();
});
