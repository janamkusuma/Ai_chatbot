import { API_BASE } from "./api.js";

const token = localStorage.getItem("token");
if (!token) location.href = "login.html";

const headersJSON = {
  "Content-Type": "application/json",
  Authorization: "Bearer " + token
};
const headersAuth = { Authorization: "Bearer " + token };

document.getElementById("logoutBtn").onclick = () => {
  localStorage.removeItem("token");
  location.href = "login.html";
};
let backState = "quiz"; 
// quiz → categories → hom
// ✅ You can add more questions here (10 shown)
let QUIZ = [];
let selectedCategory = "";

async function loadQuiz() {
  const res = await fetch(`${API_BASE}/api/quiz/questions?category=${encodeURIComponent(selectedCategory)}`, {
    headers: headersAuth
  });

  const data = await res.json();
  QUIZ = data.questions || [];
}


const restartBtn = document.getElementById("restartBtn");
const nextBtn = document.getElementById("nextBtn");

const quizStart = document.getElementById("quizStart");
const quizBox = document.getElementById("quizBox");
const resultBox = document.getElementById("resultBox");

const qnoEl = document.getElementById("qno");
const timerEl = document.getElementById("timer");
const questionEl = document.getElementById("question");
const optionsEl = document.getElementById("options");
const statusEl = document.getElementById("status");
const scoreText = document.getElementById("scoreText");

let idx = 0;
let score = 0;
let timeLeft = 15;
let t = null;
let locked = false;

function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

// If you want random order each time:


function startTimer() {
  clearInterval(t);
  timeLeft = 15;
  timerEl.textContent = timeLeft;

  t = setInterval(() => {
    timeLeft--;
    timerEl.textContent = timeLeft;
    if (timeLeft <= 0) {
      clearInterval(t);
      lockOptions(null); // timed out
      nextBtn.disabled = false;
      statusEl.innerHTML = `<span class="bad">⏱️ Time up!</span>`;
    }
  }, 1000);
}

function renderQuestion() {
  if (!QUIZ[idx]) {
    showResult();
    return;
  }
  locked = false;
  nextBtn.disabled = true;
  statusEl.textContent = "";

  const total = QUIZ.length;
  const item = QUIZ[idx];

  qnoEl.textContent = `Q${idx + 1}/${total}`;
  questionEl.textContent = item.question;

  optionsEl.innerHTML = "";
  const letters = ["A", "B", "C", "D"];

  item.options.forEach((opt, i) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "quiz-opt";
    btn.innerHTML = `
      <span class="quiz-letter">${letters[i]}</span>
      <span class="quiz-text">${opt}</span>
      <span class="quiz-mark"></span>
    `;
    btn.onclick = () => {
      if (locked) return;
      lockOptions(i);
      nextBtn.disabled = false;
    };
    optionsEl.appendChild(btn);
  });

  startTimer();
}

function lockOptions(selectedIndex) {
  locked = true;
  clearInterval(t);

  const item = QUIZ[idx];
  const correct = item.answer;

  const btns = [...optionsEl.querySelectorAll(".quiz-opt")];

  btns.forEach((b, i) => {
    b.disabled = true;
    const mark = b.querySelector(".quiz-mark");

    if (i === correct) {
      b.classList.add("correct");
      mark.textContent = "✓ Correct";
    }

    if (selectedIndex !== null && i === selectedIndex && selectedIndex !== correct) {
      b.classList.add("wrong");
      mark.textContent = "✗ Wrong";
    }
  });

  if (selectedIndex === correct) {
    score++;
    statusEl.innerHTML = `<span class="good">✅ Correct!</span>`;
  } else if (selectedIndex === null) {
    statusEl.innerHTML = `<span class="bad">⏱️ No answer selected</span>`;
  } else {
    statusEl.innerHTML = `<span class="bad">❌ Wrong</span>`;
  }
}

async function saveScore() {
  // ✅ adjust this endpoint if your backend uses different path
  // common in your project: /api/quiz/save
  try {
    await fetch(`${API_BASE}/api/quiz/save`, {
      method: "POST",
      headers: headersJSON,
      body: JSON.stringify({ score, total: QUIZ.length })
    });
  } catch (e) {
    // ignore if backend missing
  }
}

function showResult() {
  quizBox.style.display = "none";
  resultBox.style.display = "block";
  scoreText.textContent = `Your Score: ${score} / ${QUIZ.length}`;
  saveScore();
}

async function begin() {
  idx = 0;
  score = 0;

  await loadQuiz(); // 🔥 important
  if (QUIZ.length === 0) {
    alert("No questions found for this category");
    return;
  }


  quizStart.style.display = "none";
  resultBox.style.display = "none";
  quizBox.style.display = "block";

  renderQuestion();
}


restartBtn.onclick = () => location.reload();

nextBtn.onclick = () => {
  idx++;

  if (idx >= QUIZ.length) {
    showResult();
  } else {
    renderQuestion();
  }
};

window.startQuiz = async function(category) {
  selectedCategory = category;

  idx = 0;
  score = 0;

  await loadQuiz();

  if (QUIZ.length === 0) {
    alert("No questions found");
    return;
  }

  quizStart.style.display = "none";
  resultBox.style.display = "none";
  quizBox.style.display = "block";

  renderQuestion();
};

document.querySelectorAll(".start-btn").forEach(btn => {
  btn.addEventListener("click", async () => {
    const category = btn.getAttribute("data-category");

    selectedCategory = category;
    idx = 0;
    score = 0;

    backState = "quiz"; // 🔥 IMPORTANT

    await loadQuiz();

    if (QUIZ.length === 0) {
      alert("No questions found");
      return;
    }

    quizStart.style.display = "none";
    resultBox.style.display = "none";
    quizBox.style.display = "block";

    renderQuestion();
  });
});
window.goBack = function () {
  if (backState === "quiz") {
    // first click → categories
    quizBox.style.display = "none";
    resultBox.style.display = "none";
    quizStart.style.display = "block";

    backState = "categories";
  } else {
    // second click → home page
    window.location.href = "index.html";
  }
};