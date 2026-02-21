import { API_BASE } from "./api.js";

const token =
  localStorage.getItem("token") ||
  localStorage.getItem("access_token");

if (!token) location.href = "login.html";

const headers = {
  "Content-Type": "application/json",
  Authorization: "Bearer " + token,
};

const msgEl = document.getElementById("msg");
const rowsEl = document.getElementById("rows");
const emptyEl = document.getElementById("empty");

function showMsg(t) { msgEl.textContent = t || ""; }

function fmtDate(s) {
  try {
    return new Date(s).toLocaleString("en-IN", { timeZone: "Asia/Kolkata" });
  } catch {
    return s;
  }
}

async function loadMyFeedback() {
  const res = await fetch(`${API_BASE}/api/feedback/my`, { headers });
  const data = await res.json();

  rowsEl.innerHTML = "";
  if (!Array.isArray(data) || data.length === 0) {
    emptyEl.style.display = "block";
    return;
  }
  emptyEl.style.display = "none";

  data.forEach((x, i) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${i + 1}</td>
      <td><b>${x.rating}</b></td>
      <td>${x.category}</td>
      <td style="text-align:left">${(x.message || "").slice(0, 200)}</td>
      <td>${fmtDate(x.created_at)}</td>
    `;
    rowsEl.appendChild(tr);
  });
}

document.getElementById("sendBtn").onclick = async () => {
  showMsg("");

  const rating = Number(document.getElementById("rating").value || 0);
  const category = document.getElementById("category").value || "general";
  const message = (document.getElementById("message").value || "").trim();

  if (!rating || rating < 1 || rating > 5) return showMsg("Please select rating.");
  if (!message) return showMsg("Please write feedback message.");

  const res = await fetch(`${API_BASE}/api/feedback/submit`, {
    method: "POST",
    headers,
    body: JSON.stringify({ rating, category, message }),
  });

  const out = await res.json();
  if (!res.ok) return showMsg(out?.detail || "Failed.");

  document.getElementById("message").value = "";
  document.getElementById("rating").value = "";
  showMsg("✅ Feedback submitted.");
  loadMyFeedback();
};

loadMyFeedback();
