import { API_BASE } from "./api.js";

const emailEl = document.getElementById("email");
const msgEl = document.getElementById("msg");
const btn = document.getElementById("sendBtn");

btn.onclick = async () => {
  msgEl.textContent = "";
  const email = emailEl.value.trim();

  if (!email) {
    msgEl.textContent = "Enter email";
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/auth/forgot-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email })
    });

    const data = await res.json();

    if (!res.ok) {
      msgEl.textContent = data.detail || "Failed";
      return;
    }

    msgEl.textContent = "OTP sent (if account exists). Check email.";
    setTimeout(() => {
      location.href = `reset_password.html?email=${encodeURIComponent(email)}`;
    }, 800);
  } catch (e) {
    msgEl.textContent = "Network error";
  }
};