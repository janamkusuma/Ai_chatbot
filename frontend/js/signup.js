const BASE_URL = "http://127.0.0.1:8000";

export async function signup() {
  const full_name = document.getElementById("full_name").value.trim();
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value.trim();
  const confirm_password = document.getElementById("confirm_password").value.trim();
  const err = document.getElementById("err");

  err.textContent = "";

  if (!full_name || !email || !password || !confirm_password) {
    err.textContent = "All fields required!";
    return;
  }

  if (password !== confirm_password) {
    err.textContent = "Passwords do not match!";
    return;
  }

  try {
    const res = await fetch(`${BASE_URL}/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ full_name, email, password, confirm_password }),
    });

    const data = await res.json();

    if (!res.ok) {
      err.textContent = data.detail || "Signup failed!";
      return;
    }

    alert("Account created! Please login.");
    window.location.href = "login.html";
  } catch (e) {
    err.textContent = "Server error. Try again.";
  }
}

window.signup = signup;

window.googleLogin = function googleLogin() {
  window.location.href = `${BASE_URL}/auth/google/login`;
};
// ---- show/hide password (signup) ----
const toggleSignupPw = document.getElementById("toggleSignupPw");
if (toggleSignupPw) {
  toggleSignupPw.addEventListener("click", () => {
    const pw = document.getElementById("password");
    if (!pw) return;
    pw.type = pw.type === "password" ? "text" : "password";
    toggleSignupPw.textContent = pw.type === "password" ? "👁️" : "🙈";
  });
}

const toggleSignupConfirmPw = document.getElementById("toggleSignupConfirmPw");
if (toggleSignupConfirmPw) {
  toggleSignupConfirmPw.addEventListener("click", () => {
    const pw = document.getElementById("confirm_password");
    if (!pw) return;
    pw.type = pw.type === "password" ? "text" : "password";
    toggleSignupConfirmPw.textContent = pw.type === "password" ? "👁️" : "🙈";
  });
}
