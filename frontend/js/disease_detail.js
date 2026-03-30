import { API_BASE } from "./api.js";

const token = localStorage.getItem("token");
if (!token) location.href = "login.html";

const headers = { Authorization: "Bearer " + token };

document.getElementById("logoutBtn").onclick = () => {
  localStorage.removeItem("token");
  location.href = "login.html";
};

const detailEl = document.getElementById("detail");
const params = new URLSearchParams(location.search);
const id = params.get("id");

function li(items) {
  return (items || []).map(x => `<li>${x}</li>`).join("");
}

async function load() {
  const res = await fetch(`${API_BASE}/diseases/${id}`, { headers });
  const d = await res.json();

  const medsRows = (d.medicines || []).map(m => `
    <tr>
      <td>${m.name || "-"}</td>
      <td>${m.purpose || "-"}</td>
      <td>${m.dosage || "-"}</td>
    </tr>
  `).join("");

  detailEl.innerHTML = `
    <div class="detail-card">

      <!-- ✅ IMAGE TOP -->
      <div class="detail-hero-img">
        <img src="${d.image || ""}" alt="${d.name || "Disease"}"
          onerror="this.src='https://images.unsplash.com/photo-1584036561566-baf8f5f1b144?w=800&q=80';" />
      </div>

      <!-- ✅ NAME BELOW IMAGE -->
      <div class="detail-title">
        <h2>${d.name || ""}</h2>
        <p class="detail-cat">${d.category || ""}</p>
      </div>

      <div class="detail-section">
        <h3>Information</h3>
        <p>${d.info || ""}</p>
      </div>

      <div class="detail-section">
        <h3>Symptoms</h3>
        <ul>${li(d.symptoms)}</ul>
      </div>

      <div class="detail-section">
        <h3>Precautions</h3>
        <ul>${li(d.precautions)}</ul>
      </div>

      <div class="detail-section">
        <h3>Prevention</h3>
        <ul>${li(d.prevention)}</ul>
      </div>

      <div class="detail-section">
        <h3>Medicines</h3>
        <div class="table-wrap">
          <table class="med-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Purpose</th>
                <th>Dosage</th>
              </tr>
            </thead>
            <tbody>
              ${medsRows || `<tr><td colspan="3">No data</td></tr>`}
            </tbody>
          </table>
        </div>
      </div>
      <div class="detail-section">
        <h3>More Information</h3>
        ${
          d.article_link
            ? `<a href="${d.article_link}" target="_blank" class="article-btn">
                👉 Read Full Article
              </a>`
            : `<p>No article available</p>`
        }
      </div>

    </div>
  `;
}

load();
