"use strict";
const $ = (s) => document.querySelector(s);
const token = () => sessionStorage.getItem("soarm_token") || "";
const headers = () => {
  const h = { "Content-Type": "application/json" };
  if (token()) h["Authorization"] = "Bearer " + token();
  return h;
};

async function api(path, method = "GET", body) {
  const r = await fetch("/api" + path, {
    method,
    headers: headers(),
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) {
    alert("API " + r.status + ": " + (await r.text()));
    throw new Error("api " + r.status);
  }
  const ct = r.headers.get("content-type") || "";
  return ct.includes("json") ? r.json() : {};
}

const rig = () => $("#rig").value || "rig01";

async function loadRigs() {
  try {
    const rigs = await api("/rigs");
    $("#rig").innerHTML = rigs
      .map((r) => `<option value="${r.name}">${r.name} — ${r.label}</option>`)
      .join("");
  } catch (e) {
    /* surfaced by api() */
  }
}

async function refresh() {
  let st;
  try {
    st = await api("/processes");
  } catch (e) {
    return;
  }
  const items = Object.values(st);
  $("#status").innerHTML =
    items
      .map(
        (p) =>
          `<div class="proc ${p.alive ? "" : "stopped"}">` +
          `<div class="proc-head"><strong class="proc-name">${p.key}</strong>` +
          (p.alive ? "" : `<span class="proc-exit">(exit ${p.returncode})</span>`) +
          `</div><code class="proc-cmd">${p.cmd}</code>` +
          `<pre class="proc-log">${(p.log || "").replace(/</g, "&lt;")}</pre>` +
          (p.alive
            ? `<button class="stop" onclick="stopProc('${p.key}')">Stop</button>`
            : `<button class="secondary" onclick="clearProc('${p.key}')">Dismiss</button>`) +
          `</div>`
      )
      .join("") || '<p class="hint italic">Nothing running.</p>';
}

async function start(action, body) {
  await api(`/rigs/${rig()}/${action}`, "POST", body || {});
  refresh();
}
function startTeleop() {
  start("teleop", { display_data: $("#teleop_display").checked });
}
function startRecord() {
  start("record", {
    episodes: +$("#rec_episodes").value,
    episode_time_s: +$("#rec_eps").value,
    reset_time_s: +$("#rec_reset").value,
    hf_user: $("#rec_hf").value || "local",
    dataset_name: $("#rec_name").value || null,
    resume: $("#rec_resume").checked,
  });
}
function startReplay() {
  start("replay", { repo_id: $("#rep_repo").value, episode: +$("#rep_ep").value });
}
async function stopProc(key) {
  await api(`/processes/${key}/stop`, "POST", {});
  refresh();
}
async function clearProc(key) {
  await api(`/processes/${key}`, "DELETE");
  refresh();
}
async function stopAll() {
  await api("/processes/stop-all", "POST", {});
  refresh();
}
function saveToken() {
  sessionStorage.setItem("soarm_token", $("#token").value);
  loadRigs();
  refresh();
}

window.addEventListener("load", () => {
  $("#token").value = token();
  loadRigs();
  refresh();
  setInterval(refresh, 5000);
});
