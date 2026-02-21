import { API_BASE } from "./api.js";

const token = localStorage.getItem("token");
if (!token) location.href = "login.html";

const headers = { Authorization: "Bearer " + token };

document.getElementById("logoutBtn").onclick = () => {
  localStorage.removeItem("token");
  location.href = "login.html";
};

const groupedEl = document.getElementById("grouped");
const searchEl = document.getElementById("search");
const catEl = document.getElementById("category");

function groupByCategory(items) {
  const g = {};
  for (const d of items || []) {
    const cat = d.category || "Other";
    (g[cat] ||= []).push(d);
  }
  return g;
}

function redirectIf401(res) {
  if (res.status === 401) {
    localStorage.removeItem("token");
    location.href = "login.html";
    return true;
  }
  return false;
}

async function load() {
  const q = encodeURIComponent(searchEl.value.trim());

  // ✅ IMPORTANT: "All" selected => send "All" (backend should treat it as no-filter)
  const selectedCat = (catEl.value || "All").trim();
  const c = encodeURIComponent(selectedCat);

  const url = `${API_BASE}/diseases/list?q=${q}&category=${c}`;
  const res = await fetch(url, { headers });

  if (redirectIf401(res)) return;

  if (!res.ok) {
    groupedEl.innerHTML = `<p style="opacity:.7;">Failed to load diseases</p>`;
    return;
  }

  const data = await res.json();

  if (!Array.isArray(data) || data.length === 0) {
    groupedEl.innerHTML = `<p style="opacity:.7;">No diseases found.</p>`;
    return;
  }

  const groups = groupByCategory(data);

  groupedEl.innerHTML = "";

  Object.keys(groups).sort().forEach(category => {
    const section = document.createElement("section");
    section.className = "group-section";
    section.innerHTML = `<h3 class="group-title">${category}</h3>`;

    const grid = document.createElement("div");
    grid.className = "disease-grid";

    groups[category].forEach(d => {
      const card = document.createElement("button");
      card.type = "button";
      card.className = "disease-card";
      card.innerHTML = `
        <div class="disease-img">
          <img
            src="${d.image || ""}"
            alt="${d.name || "Disease"}"
            onerror="this.src='https://images.unsplash.com/photo-1584036561566-baf8f5f1b144?w=800&q=80';"
          />
        </div>
        <div class="disease-meta">
          <div class="disease-name">${d.name || ""}</div>
          <div class="disease-cat">${d.category || ""}</div>
        </div>
      `;
      card.onclick = () => location.href = `disease_detail.html?id=${d.id}`;
      grid.appendChild(card);
    });

    section.appendChild(grid);
    groupedEl.appendChild(section);
  });
}

searchEl.addEventListener("input", load);
catEl.addEventListener("change", load);

load();