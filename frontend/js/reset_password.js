import { API_BASE } from "./api.js";

const params = new URLSearchParams(location.search);
const emailFromUrl = params.get("email") || "";

const emailEl = document.getElementById("email");
const otpEl = document.getElementById("otp");
const newPwEl = document.getElementById("newPw");
const confirmPwEl = document.getElementById("confirmPw");
const msgEl = document.getElementById("msg");
const btn = document.getElementById("resetBtn");

emailEl.value = emailFromUrl;

btn.onclick = async () => {
  msgEl.textContent = "";

  const email = emailEl.value.trim();
  const otp = otpEl.value.trim();
  const new_password = newPwEl.value.trim();
  const confirm_password = confirmPwEl.value.trim();

  if (!email || !otp || !new_password || !confirm_password) {
    msgEl.textContent = "Fill all fields";
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/auth/reset-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, otp, new_password, confirm_password })
    });

    const data = await res.json();

    if (!res.ok) {
      msgEl.textContent = data.detail || "Failed";
      return;
    }

    msgEl.textContent = "Password reset success. Redirecting to login...";
    setTimeout(() => {
      location.href = "login.html";
    }, 900);
  } catch (e) {
    msgEl.textContent = "Network error";
  }
};