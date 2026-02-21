import { API_BASE } from "./api.js";

const token = localStorage.getItem("token") || localStorage.getItem("access_token");
if (!token) location.href = "login.html";

const headers = { Authorization: "Bearer " + token };

document.getElementById("logoutBtn").onclick = () => {
  localStorage.removeItem("token");
  localStorage.removeItem("access_token");
  location.href = "login.html";
};

const rowsEl = document.getElementById("rows");
const emptyEl = document.getElementById("empty");

function fmtDate(s) {
  try {
    if (!s) return "";
    const hasTZ = /Z$|[+-]\d\d:\d\d$/.test(s);
    const iso = hasTZ ? s : s + "Z";
    return new Date(iso).toLocaleString("en-IN", { timeZone: "Asia/Kolkata" });
  } catch {
    return s;
  }
}

async function load() {
  const res = await fetch(`${API_BASE}/api/quiz/my-scores`, { headers });
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
      <td><b>${x.score}</b></td>
      <td>${x.total}</td>
      <td>${fmtDate(x.created_at || x.date || x.timestamp || "")}</td>
    `;
    rowsEl.appendChild(tr);
  });
}

load();