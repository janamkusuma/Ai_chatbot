import { API_BASE } from "./api.js";

const token = localStorage.getItem("token");
if (!token) location.href = "login.html";

const headers = { Authorization: "Bearer " + token };

document.getElementById("logoutBtn").onclick = () => {
  localStorage.removeItem("token");
  location.href = "login.html";
};

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function fmtDate(s) {
  try { return new Date(s).toLocaleString(); } catch { return s; }
}

async function load() {
  const res = await fetch(`${API_BASE}/api/reports/summary`, { headers });
  const data = await res.json();

  // ---- KPIs ----
  setText("k1", data?.kpis?.quiz_attempts ?? 0);
  setText("k2", (data?.kpis?.avg_quiz_percent ?? 0) + "%");
  setText("k3", data?.kpis?.total_chats ?? 0);
  setText("k4", data?.kpis?.total_messages ?? 0);

  // ---- Quiz (last 10) charts ----
  const quiz = data.quiz_last10 || [];
  const labels = quiz.map((_, i) => "A" + (i + 1));
  const perc = quiz.map(x => x.percent);

  new Chart(document.getElementById("quizLine"), {
    type: "line",
    data: { labels, datasets: [{ label: "Score %", data: perc }] }
  });

  new Chart(document.getElementById("quizBar"), {
    type: "bar",
    data: { labels, datasets: [{ label: "Score %", data: perc }] }
  });

  // ---- Messages per day chart ----
  const mpd = data.messages_per_day || {};
  const msgLabels = Object.keys(mpd).sort();
  const msgCounts = msgLabels.map(k => mpd[k]);

  new Chart(document.getElementById("msgLine"), {
    type: "line",
    data: { labels: msgLabels, datasets: [{ label: "Messages", data: msgCounts }] }
  });

  // ---- Role ratio chart ----
  const rr = data.role_ratio || { user: 0, assistant: 0 };
  new Chart(document.getElementById("rolePie"), {
    type: "pie",
    data: {
      labels: ["User", "Assistant"],
      datasets: [{ data: [rr.user || 0, rr.assistant || 0] }]
    }
  });

  // ---- Fill quiz table ----
  const rowsEl = document.getElementById("quizRows");
  const emptyEl = document.getElementById("quizEmpty");
  rowsEl.innerHTML = "";

  if (!quiz.length) {
    emptyEl.style.display = "block";
    return;
  }
  emptyEl.style.display = "none";

  quiz.forEach((x, i) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${i + 1}</td>
      <td><b>${x.score}</b></td>
      <td>${x.total}</td>
      <td>${x.percent}%</td>
      <td>${fmtDate(x.date)}</td>
    `;
    rowsEl.appendChild(tr);
  });
}

load();