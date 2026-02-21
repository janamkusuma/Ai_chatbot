const BASE_URL = "https://ai-chatbot-0r5n.onrender.com"; // optional if you call api later

function getToken() {
  return localStorage.getItem("token") || localStorage.getItem("access_token");
}

function base64UrlDecode(str) {
  str = str.replace(/-/g, "+").replace(/_/g, "/");
  const pad = str.length % 4;
  if (pad) str += "=".repeat(4 - pad);
  return decodeURIComponent(
    atob(str)
      .split("")
      .map(c => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
      .join("")
  );
}

function getUserFromToken(token) {
  try {
    const payload = token.split(".")[1];
    const json = JSON.parse(base64UrlDecode(payload));
    return {
      full_name: json.full_name || "User",
      email: json.email || "",
      role: json.role || "USER",
    };
  } catch {
    return null;
  }
}

function showAuthUI(user) {
  const profileWrap = document.getElementById("profileWrap");
  const authActions = document.getElementById("authActions");
  const adminLink = document.getElementById("adminLink");

  if (!profileWrap || !authActions) return;

  if (!user) {
    profileWrap.style.display = "none";
    authActions.style.display = "flex";
    if (adminLink) adminLink.style.display = "none";
    return;
  }

  authActions.style.display = "none";
  profileWrap.style.display = "inline-block";

  const dropName = document.getElementById("dropName");
  const dropEmail = document.getElementById("dropEmail");
  if (dropName) dropName.textContent = user.full_name;
  if (dropEmail) dropEmail.textContent = user.email;

  if (adminLink) adminLink.style.display = user.role === "ADMIN" ? "inline" : "none";
}

function initDropdown() {
  const profileBtn = document.getElementById("profileBtn");
  const dropdown = document.getElementById("dropdown");
  if (!profileBtn || !dropdown) return;

  profileBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    dropdown.style.display = dropdown.style.display === "block" ? "none" : "block";
  });

  document.addEventListener("click", () => {
    dropdown.style.display = "none";
  });
}

function requireLogin() {
  const token = getToken();
  if (!token) {
    window.location.href = "/frontend/login.html";
    return false;
  }

  const user = getUserFromToken(token);
  if (!user) {
    localStorage.removeItem("token");
    localStorage.removeItem("access_token");
    window.location.href = "/frontend/login.html";
    return false;
  }

  return true;
}

// Buttons
document.getElementById("btnSignIn")?.addEventListener("click", () => {
  window.location.href = "/frontend/login.html";
});

document.getElementById("btnSignUp")?.addEventListener("click", () => {
  window.location.href = "/frontend/signup.html";
});

document.getElementById("logoutBtn")?.addEventListener("click", () => {
  localStorage.removeItem("token");
  localStorage.removeItem("access_token");
  window.location.href = "/frontend/login.html";
});

document.getElementById("startChatBtn")?.addEventListener("click", () => {
  if (requireLogin()) window.location.href = "/frontend/chatbot.html";
});

document.getElementById("ctaChatBtn")?.addEventListener("click", () => {
  if (requireLogin()) window.location.href = "/frontend/chatbot.html";
});

// On load
const token = getToken();
const user = token ? getUserFromToken(token) : null;

showAuthUI(user);
initDropdown();