// frontend/js/admin.js
const BASE_URL = "https://ai-chatbot-0r5n.onrender.com";

// stats
const statUsers = document.getElementById("statUsers");
const statChats = document.getElementById("statChats");
const statMsgs  = document.getElementById("statMsgs");

// users
const usersBody = document.getElementById("usersBody");
const msgBox = document.getElementById("msgBox");

// buttons
const btnRefresh = document.getElementById("btnRefresh");
const btnLogout = document.getElementById("btnLogout");

// filters
const searchInput = document.getElementById("searchInput");
const filterRole = document.getElementById("filterRole");
const filterActive = document.getElementById("filterActive");

// bars
const barUsers = document.getElementById("barUsers");
const barChats = document.getElementById("barChats");
const barMsgs  = document.getElementById("barMsgs");
const barUsersVal = document.getElementById("barUsersVal");
const barChatsVal = document.getElementById("barChatsVal");
const barMsgsVal  = document.getElementById("barMsgsVal");

// quiz + feedback
const quizBody = document.getElementById("quizBody");
const feedbackBody = document.getElementById("feedbackBody");

// pdf
const pdfBody = document.getElementById("pdfBody");
const pdfFile = document.getElementById("pdfFile");
const btnUploadPdf = document.getElementById("btnUploadPdf");
const btnIngestPdf = document.getElementById("btnIngestPdf");

// ---------- helpers ----------
function getToken() {
  return localStorage.getItem("token") || localStorage.getItem("access_token") || "";
}

function setMsg(text, type="") {
  if (!msgBox) return;
  msgBox.className = "msg " + (type === "err" ? "err" : type === "ok" ? "ok" : "");
  msgBox.textContent = text || "";
}

window.goHome = function goHome() {
  window.location.href = "index.html";
};

function authHeaders(extra={}) {
  const token = getToken();
  return { "Authorization": `Bearer ${token}`, ...extra };
}

function safeJsonParse(txt) {
  try { return txt ? JSON.parse(txt) : {}; } catch { return {}; }
}

async function apiGet(path) {
  const res = await fetch(`${BASE_URL}${path}`, { headers: authHeaders() });
  const txt = await res.text();
  if (!res.ok) throw new Error(txt || `GET failed: ${res.status}`);
  return safeJsonParse(txt);
}

async function apiPost(path, body) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body || {})
  });
  const txt = await res.text();
  if (!res.ok) throw new Error(txt || `POST failed: ${res.status}`);
  return safeJsonParse(txt);
}

async function apiPatch(path) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "PATCH",
    headers: authHeaders({ "Content-Type": "application/json" })
  });
  const txt = await res.text();
  if (!res.ok) throw new Error(txt || `PATCH failed: ${res.status}`);
  return safeJsonParse(txt);
}

async function apiPatchJson(path, body) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "PATCH",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(body || {})
  });
  const txt = await res.text();
  if (!res.ok) throw new Error(txt || `PATCH failed: ${res.status}`);
  return safeJsonParse(txt);
}

async function apiDelete(path) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "DELETE",
    headers: authHeaders()
  });
  const txt = await res.text();
  if (!res.ok) throw new Error(txt || `DELETE failed: ${res.status}`);
  return safeJsonParse(txt);
}

// ---------- bars ----------
function setBars(u, c, m) {
  const max = Math.max(u, c, m, 1);
  const hU = Math.round((u / max) * 150);
  const hC = Math.round((c / max) * 150);
  const hM = Math.round((m / max) * 150);

  if (barUsers) barUsers.style.height = `${hU}px`;
  if (barChats) barChats.style.height = `${hC}px`;
  if (barMsgs)  barMsgs.style.height  = `${hM}px`;

  if (barUsersVal) barUsersVal.textContent = u;
  if (barChatsVal) barChatsVal.textContent = c;
  if (barMsgsVal)  barMsgsVal.textContent  = m;
}

// ---------- users ----------
function renderUsers(users) {
  const q = (searchInput?.value || "").trim().toLowerCase();
  const roleF = filterRole?.value || "ALL";
  const activeF = filterActive?.value || "ALL";

  const filtered = (users || []).filter(u => {
    const text = `${u.full_name || ""} ${u.email || ""}`.toLowerCase();
    if (q && !text.includes(q)) return false;
    if (roleF !== "ALL" && u.role !== roleF) return false;

    const isActive = !!u.is_active;
    if (activeF === "ACTIVE" && !isActive) return false;
    if (activeF === "BLOCKED" && isActive) return false;
    return true;
  });

  if (!usersBody) return;

  if (!filtered.length) {
    usersBody.innerHTML = `<tr><td colspan="6" style="opacity:.7;">No users found.</td></tr>`;
    return;
  }

  usersBody.innerHTML = filtered.map(u => {
    const rolePill = u.role === "ADMIN"
      ? `<span class="pill pill-admin">ADMIN</span>`
      : `<span class="pill">USER</span>`;

    const statusPill = u.is_active
      ? `<span class="pill">Active</span>`
      : `<span class="pill pill-block">Blocked</span>`;

    const blockBtnText = u.is_active ? "Block" : "Unblock";

    return `
      <tr>
        <td>${u.id}</td>
        <td>${u.full_name || ""}</td>
        <td>${u.email || ""}</td>
        <td>${rolePill}</td>
        <td>${statusPill}</td>
        <td>
          <button class="btn btn-small btn-outline" data-action="role" data-id="${u.id}">Toggle Role</button>
          <button class="btn btn-small ${u.is_active ? "btn-danger" : "btn-primary"}" data-action="block" data-id="${u.id}">
            ${blockBtnText}
          </button>
        </td>
      </tr>
    `;
  }).join("");
}

// ---------- quiz (DELETE ONLY) ----------
function renderQuiz(rows){
  if(!quizBody) return;
  if(!rows || !rows.length){
    quizBody.innerHTML = `<tr><td colspan="6" style="opacity:.7;">No quiz history.</td></tr>`;
    return;
  }

  quizBody.innerHTML = rows.map((r)=>`
    <tr>
      <td>${r.id}</td>
      <td>${r.user_email || ""}</td>
      <td><b>${r.score}</b></td>
      <td>${r.total}</td>
      <td>${r.created_at || ""}</td>
      <td>
        <button class="btn btn-small btn-danger" data-quiz-del="${r.id}">Delete</button>
      </td>
    </tr>
  `).join("");
}

// ---------- feedback (EDIT + DELETE) ----------
function escapeHtml(s){
  return String(s || "")
    .replaceAll("&","&amp;")
    .replaceAll("<","&lt;")
    .replaceAll(">","&gt;")
    .replaceAll('"',"&quot;")
    .replaceAll("'","&#039;");
}

function renderFeedback(rows){
  if(!feedbackBody) return;
  if(!rows || !rows.length){
    feedbackBody.innerHTML = `<tr><td colspan="7" style="opacity:.7;">No feedback.</td></tr>`;
    return;
  }

  feedbackBody.innerHTML = rows.map((r)=>`
    <tr>
      <td>${r.id}</td>
      <td>${r.user_email || ""}</td>
      <td>${r.rating ?? ""}</td>
      <td>${r.category ?? ""}</td>
      <td>${escapeHtml((r.message||"").slice(0,200))}</td>
      <td>${r.created_at || ""}</td>
      <td>
        <button class="btn btn-small btn-outline" data-fb-edit="${r.id}">Edit</button>
        <button class="btn btn-small btn-danger" data-fb-del="${r.id}">Delete</button>
      </td>
    </tr>
  `).join("");
}

// ---------- PDFs ----------
function renderPdfs(files){
  if(!pdfBody) return;
  if(!files || !files.length){
    pdfBody.innerHTML = `<tr><td colspan="2" style="opacity:.7;">No PDFs.</td></tr>`;
    return;
  }
  pdfBody.innerHTML = files.map((f)=>`
    <tr>
      <td>${escapeHtml(f.filename)}</td>
      <td>
        <button class="btn btn-small btn-danger" data-pdf-del="${escapeHtml(f.filename)}">Delete</button>
      </td>
    </tr>
  `).join("");
}

async function refreshPdfs(){
  const pdfs = await apiGet("/api/admin/pdfs");
  renderPdfs(pdfs.files || []);
}

// ---------- loadAll ----------
let cachedUsers = [];

async function loadAll() {
  setMsg("");
  const token = getToken();
  if (!token) {
    alert("Token not found. Please login first.");
    window.location.href = "./login.html";
    return;
  }

  try {
    const stats = await apiGet("/api/admin/stats");
    if (statUsers) statUsers.textContent = stats.total_users ?? 0;
    if (statChats) statChats.textContent = stats.total_chats ?? 0;
    if (statMsgs)  statMsgs.textContent  = stats.total_messages ?? 0;
    setBars(stats.total_users ?? 0, stats.total_chats ?? 0, stats.total_messages ?? 0);

    cachedUsers = await apiGet("/api/admin/users");
    renderUsers(cachedUsers);

    renderQuiz(await apiGet("/api/admin/quiz-history"));
    renderFeedback(await apiGet("/api/admin/feedback-history"));

    await refreshPdfs();

    setMsg("Loaded successfully ✅", "ok");
  } catch (e) {
    console.error(e);
    setMsg("Error: " + (e.message || "Failed"), "err");
  }
}

// ---------- events ----------

// Users actions
if (usersBody) {
  usersBody.addEventListener("click", async (e) => {
    const btn = e.target.closest("button");
    if (!btn) return;
    const action = btn.dataset.action;
    const id = btn.dataset.id;
    if (!action || !id) return;

    try {
      if (action === "block") await apiPatch(`/api/admin/users/${id}/block`);
      if (action === "role")  await apiPatch(`/api/admin/users/${id}/role`);
      cachedUsers = await apiGet("/api/admin/users");
      renderUsers(cachedUsers);
      setMsg("Updated ✅", "ok");
    } catch (err) {
      setMsg("Error: " + err.message, "err");
    }
  });
}

// Filters
if (searchInput) searchInput.addEventListener("input", () => renderUsers(cachedUsers));
if (filterRole) filterRole.addEventListener("change", () => renderUsers(cachedUsers));
if (filterActive) filterActive.addEventListener("change", () => renderUsers(cachedUsers));

// Quiz delete (ONLY)
if (quizBody) {
  quizBody.addEventListener("click", async (e) => {
    const del = e.target.closest("[data-quiz-del]");
    if (!del) return;

    const id = del.getAttribute("data-quiz-del");
    if (!confirm("Delete this quiz record?")) return;

    try {
      await apiDelete(`/api/admin/quiz-history/${id}`);
      renderQuiz(await apiGet("/api/admin/quiz-history"));
      setMsg("Quiz deleted ✅", "ok");
    } catch (err) {
      setMsg("Error: " + err.message, "err");
    }
  });
}

// Feedback edit + delete
if (feedbackBody) {
  feedbackBody.addEventListener("click", async (e) => {
    const del = e.target.closest("[data-fb-del]");
    const edit = e.target.closest("[data-fb-edit]");

    try {
      if (del) {
        const id = del.getAttribute("data-fb-del");
        if (!confirm("Delete this feedback?")) return;

        await apiDelete(`/api/admin/feedback-history/${id}`);
        renderFeedback(await apiGet("/api/admin/feedback-history"));
        setMsg("Feedback deleted ✅", "ok");
      }

      if (edit) {
        const id = edit.getAttribute("data-fb-edit");

        const rating = prompt("New rating (1-5):", "5");
        if (rating === null) return;

        const category = prompt("New category:", "chatbot");
        if (category === null) return;

        const message = prompt("New message:", "Very Good");
        if (message === null) return;

        await apiPatchJson(`/api/admin/feedback-history/${id}`, {
          rating: Number(rating),
          category: category.trim(),
          message: message.trim()
        });

        renderFeedback(await apiGet("/api/admin/feedback-history"));
        setMsg("Feedback updated ✅", "ok");
      }
    } catch (err) {
      setMsg("Error: " + err.message, "err");
    }
  });
}

// PDF delete
if (pdfBody) {
  pdfBody.addEventListener("click", async (e) => {
    const del = e.target.closest("[data-pdf-del]");
    if (!del) return;

    const fn = del.getAttribute("data-pdf-del");
    try {
      await apiDelete(`/api/admin/pdfs/${encodeURIComponent(fn)}`);
      await refreshPdfs();
      setMsg("PDF deleted ✅", "ok");
    } catch (err) {
      setMsg("Error: " + err.message, "err");
    }
  });
}

// PDF upload
if (btnUploadPdf) {
  btnUploadPdf.addEventListener("click", async () => {
    try {
      if (!pdfFile.files || !pdfFile.files[0]) {
        alert("Select a PDF file");
        return;
      }

      const fd = new FormData();
      fd.append("file", pdfFile.files[0]);

      const res = await fetch(`${BASE_URL}/api/admin/pdfs/upload`, {
        method: "POST",
        headers: authHeaders(), // don't set content-type
        body: fd
      });

      const txt = await res.text();
      if (!res.ok) throw new Error(txt || "Upload failed");

      pdfFile.value = "";
      await refreshPdfs();
      setMsg("PDF uploaded ✅", "ok");
    } catch (err) {
      setMsg("Error: " + err.message, "err");
    }
  });
}

// PDF ingest
if (btnIngestPdf) {
  btnIngestPdf.addEventListener("click", async () => {
    try {
      btnIngestPdf.disabled = true;
      btnIngestPdf.textContent = "Ingesting...";
      setMsg("Ingest running... (only new PDFs will be indexed)", "ok");

      const out = await apiPost("/api/admin/pdfs/ingest", {});
      const processed = out.processed ?? 0;
      const skipped = out.skipped ?? 0;
      const files = out.processed_files || [];

      if (processed === 0) {
        setMsg(`✅ ${out.message || "No new PDFs to ingest"} | skipped: ${skipped}`, "ok");
      } else {
        const list = files.length ? `\nFiles:\n- ${files.join("\n- ")}` : "";
        setMsg(`✅ Ingest done | processed: ${processed}, skipped: ${skipped}${list}`, "ok");
      }

      await refreshPdfs();
    } catch (err) {
      setMsg("Error: " + err.message, "err");
    } finally {
      btnIngestPdf.disabled = false;
      btnIngestPdf.textContent = "Ingest Now";
    }
  });
}

// refresh/logout
if (btnRefresh) btnRefresh.addEventListener("click", loadAll);

if (btnLogout) {
  btnLogout.addEventListener("click", () => {
    localStorage.removeItem("token");
    localStorage.removeItem("access_token");
    window.location.href = "./login.html";
  });
}

// start
loadAll();