import { API_BASE } from "./api.js";

const token = localStorage.getItem("token");
if (!token) location.href = "login.html";

const headers = {
  "Content-Type": "application/json",
  Authorization: "Bearer " + token
};



document.getElementById("logoutBtn").onclick = () => {
  localStorage.removeItem("token");
  location.href = "login.html";
};

const SYMPTOMS = [
  "Fever",
  "Headache",
  "Cough",
  "Sore throat",
  "Runny nose",
  "Body pain",
  "Fatigue",
  "Dizziness",
  "Shortness of breath",
  "Chest pain",
  "Nausea",
  "Vomiting",
  "Diarrhea",
  "Stomach pain",
  "Loss of appetite",
  "Joint pain",
  "Muscle pain",
  "Skin rash",
  "Leg swelling",
  "Sleepiness"
];

const DISEASE_HOSPITAL_MAP = {
  "Influenza (Flu)": "general hospital",
  "COVID-19": "hospital",
  "Common Cold": "clinic",
  "Pneumonia": "pulmonologist hospital",
  "Bronchitis": "chest specialist hospital",
  "Food Poisoning": "gastroenterology hospital",
  "Hypertension": "cardiology hospital",
  "Diabetes": "diabetes clinic",
  "Dengue": "multi speciality hospital"
};

const chipsEl = document.getElementById("chips");
const outEl = document.getElementById("out");
const loadingEl = document.getElementById("loading");
const analyzeBtn = document.getElementById("analyzeBtn");

const selected = new Set();
async function loadGoogleMaps() {
  const res = await fetch(`${API_BASE}/api/config/maps-key`);
  const data = await res.json();

  const script = document.createElement("script");
  script.src = `https://maps.googleapis.com/maps/api/js?key=${data.key}&libraries=places,marker&callback=initMap`;
  script.async = true;
  script.defer = true;

  document.head.appendChild(script);
}

function renderChips() {
  chipsEl.innerHTML = "";
  SYMPTOMS.forEach(s => {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "chip" + (selected.has(s) ? " active" : "");
    b.textContent = s;
    b.onclick = () => {
      selected.has(s) ? selected.delete(s) : selected.add(s);
      renderChips();
    };
    chipsEl.appendChild(b);
  });
}

function redirectIf401(res) {
  if (res.status === 401) {
    localStorage.removeItem("token");
    location.href = "login.html";
    return true;
  }
  return false;
}

let pieChartInstance = null;

function renderMlPieChart(predictions) {
  const canvas = document.getElementById("mlPie");
  if (!canvas) return;

  const labels = predictions.map(p => p.disease);
  const values = predictions.map(p =>
    p.confidence ? Math.round(p.confidence * 100) : 0
  );

  if (pieChartInstance) {
    pieChartInstance.destroy();
  }

  pieChartInstance = new Chart(canvas, {
    type: "pie",
    data: {
      labels,
      datasets: [{
        data: values
      }]
    },
    options: {
      plugins: {
        legend: {
          position: "top",
          labels: {
            generateLabels(chart) {
              const data = chart.data;
              return data.labels.map((label, i) => ({
                text: `${label} (${data.datasets[0].data[i]}%)`,
                fillStyle: chart.data.datasets[0].backgroundColor?.[i]
              }));
            }
          }
        },
        datalabels: {
          color: "#fff",
          font: {
            weight: "bold",
            size: 14
          },
          formatter: value => value + "%"
        }
      }
    },
    plugins: [ChartDataLabels]
  });
}



async function analyze() {
  if (selected.size === 0) {
    alert("Select at least 1 symptom");
    return;
  }

  loadingEl.style.display = "block";
  outEl.innerHTML = "";

  const symptomsArr = Array.from(selected);

  // 1) Rule-based analyze
  const res = await fetch(`${API_BASE}/symptom/analyze`, {
    method: "POST",
    headers,
    body: JSON.stringify({ symptoms: symptomsArr })
  });

  if (redirectIf401(res)) return;

  const data = await res.json();

  // 2) ML predictions (Top-5)
  let mlData = null;
  try {
    const mlRes = await fetch(`${API_BASE}/symptom/predict-ml`, {
      method: "POST",
      headers,
      body: JSON.stringify({ symptoms: symptomsArr, top_k: 5 })
    });

    if (redirectIf401(mlRes)) return;

    mlData = await mlRes.json(); // {predictions:[...]}
  } catch (e) {
    console.error("ML prediction failed:", e);
  }

  loadingEl.style.display = "none";

  // ---- ML Block with Pie chart + list (no note) ----
  let mlBlock = "";
  if (mlData && Array.isArray(mlData.predictions) && mlData.predictions.length) {
    const preds = mlData.predictions;

    const mlList = preds.map(p => `
    <div style="display:flex;gap:16px;margin:8px 0;">
      <div style="width:220px;font-weight:700;">
        ${p.disease}
      </div>
      <div style="font-weight:700;">
        ${(p.confidence * 100).toFixed(2)}%
      </div>
    </div>
  `).join("");


    mlBlock = `
      <div class="panel" style="margin-top:14px;">
        <h3 style="margin:0 0 10px;">ML Predictions (Top ${preds.length})</h3>

        <div style="display:grid;grid-template-columns: 1.2fr 0.8fr; gap:14px; align-items:center;">
          <div>
            ${mlList}
          </div>

          <div style="display:flex;justify-content:center;">
            <canvas id="mlPie" width="220" height="220"></canvas>
          </div>
        </div>
      </div>
    `;

    // render chart after HTML inserted
    setTimeout(() => renderMlPieChart(preds), 0);
  }

  // ---- Rule-based cards ----
  const cards = (data.results || []).map(r => `
    <div class="analysis-card">
      <div class="card-head">
        <h3 class="dname">${r.name}</h3>
        <span class="risk-pill ${String(r.risk).toLowerCase()}">${r.risk}</span>
      </div>

      <div class="risk-bar ${String(r.risk).toLowerCase()}"></div>

      <div class="reason-title">Reason</div>
      <div class="reason-text">${r.reason}</div>

      <div class="matched">
        <b>Matched symptoms:</b> ${(r.matched_symptoms || []).join(", ")}
      </div>
    </div>
  `).join("");

  const remedies = `
    <div class="panel">
      <h3>Home Remedies</h3>
      <ul>${(data.home_remedies||[]).map(x=>`<li>${x}</li>`).join("")}</ul>
    </div>
  `;

  const doctor = `
    <div class="panel">
      <h3>When to Visit a Doctor</h3>
      <ul>${(data.when_to_visit_doctor||[]).map(x=>`<li>${x}</li>`).join("")}</ul>
    </div>
  `;

  outEl.innerHTML = mlBlock + cards + remedies + doctor;
  // ✅ CHECK HIGH RISK
  
  const topDisease = data.results?.[0]?.name;
  const hospitalType = DISEASE_HOSPITAL_MAP[topDisease] || "hospital";

  // ✅ Determine which diseases are high or medium risk
  const riskyDiseases = (data.results || []).filter(r => r.risk === "High" || r.risk === "Medium");

  if (riskyDiseases.length) {
    const section = document.getElementById("hospitalSection");
    section.style.display = "block";

    // Load hospitals for each risky disease
    riskyDiseases.forEach((disease, index) => {
      const hospitalType = DISEASE_HOSPITAL_MAP[disease.name] || "hospital";

      // Use a small delay per disease to avoid race issues
      setTimeout(() => {
        loadHospitals(hospitalType, disease.name, disease.risk);
      }, index * 300);
    });
  } else {
    document.getElementById("hospitalSection").style.display = "none";
  }
}
let map; // global map instance

function initMap(userLocation) {
  if (!map) {
    map = new google.maps.Map(document.getElementById("map"), {
      center: userLocation,
      zoom: 14,
      mapId: "effd4ed6a8e9b2918636ffe0"
    });

    // mark user location
    new google.maps.marker.AdvancedMarkerElement({
      map,
      position: userLocation,
      title: "You are here"
    });
  } else {
    map.setCenter(userLocation);
  }
}

function loadHospitals(type, diseaseName = "", risk = "") {
  if (typeof google === "undefined") {
    alert("Map not loaded yet, refresh page");
    return;
  }

  navigator.geolocation.getCurrentPosition(
    position => {
      const lat = position.coords.latitude;
      const lng = position.coords.longitude;
      const userLocation = { lat, lng };

      // initialize or center map
      initMap(userLocation);

      const service = new google.maps.places.PlacesService(map);
      service.nearbySearch(
        {
          location: userLocation,
          radius: 5000,
          keyword: type
        },
        (results, status) => {
          if (status === google.maps.places.PlacesServiceStatus.OK && results) {
            let listHTML = `<h4>${diseaseName} (${risk} Risk)</h4>`;

            results.forEach(place => {
              const marker = new google.maps.marker.AdvancedMarkerElement({
                map,
                position: place.geometry.location,
                title: place.name
              });

              const address = place.vicinity || "Address not available";
              const rating = place.rating ? `⭐ ${place.rating} (${place.user_ratings_total || 0} reviews)` : "";
              const openStatus = place.opening_hours?.open_now ? "🟢 Open now" : "🔴 Closed";

              // marker click opens Google Maps directions
              const mapsUrl = `https://www.google.com/maps/dir/?api=1&origin=${lat},${lng}&destination=${encodeURIComponent(place.name + " " + address)}`;
              marker.addListener("click", () => window.open(mapsUrl, "_blank"));

              // also show in the list
              listHTML += `
                <div style="margin-bottom:8px;">
                  <p>🏥 <b><a href="${mapsUrl}" target="_blank">${place.name}</a></b></p>
                  <p>📍 ${address}</p>
                  <p>${rating} ${openStatus}</p>
                </div>
              `;
            });

            const container = document.getElementById("hospitalList");
            container.innerHTML += listHTML;
          }
        }
      );
    },
    () => {
      alert("Please allow location access");
    }
  );
}
analyzeBtn.onclick = analyze;
renderChips();
loadGoogleMaps();