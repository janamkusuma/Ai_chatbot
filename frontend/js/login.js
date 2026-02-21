const BASE_URL = "http://127.0.0.1:8000";

// ✅ If google callback sends token in URL, store and go home
(function handleGoogleToken() {
  const url = new URL(window.location.href);
  const token = url.searchParams.get("token");
  const error = url.searchParams.get("error");

  if (error) {
    const err = document.getElementById("err");
    if (err) err.textContent = "Google login failed. Try again.";
  }

  if (token) {
    localStorage.setItem("token", token);
    // clean url
    window.history.replaceState({}, document.title, "login.html");
    window.location.href = "index.html";
  }
})();

export async function login() {
  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value.trim();
  const err = document.getElementById("err");

  err.textContent = "";

  if (!email || !password) {
    err.textContent = "All fields required!";
    return;
  }

  try {
    const res = await fetch(`${BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const data = await res.json();

    if (!res.ok) {
      err.textContent = data.detail || "Login failed!";
      return;
    }

    localStorage.setItem("token", data.access_token);

    // ✅ Always open index.html
    window.location.href = "index.html";

  } catch (e) {
    err.textContent = "Server error. Try again.";
  }
}



window.login = login;

window.googleLogin = function googleLogin() {
  window.location.href = `${BASE_URL}/auth/google/login`;
};
// ---- show/hide password (login) ----
const toggleLoginPw = document.getElementById("toggleLoginPw");
if (toggleLoginPw) {
  toggleLoginPw.addEventListener("click", () => {
    const pw = document.getElementById("password");
    if (!pw) return;
    pw.type = pw.type === "password" ? "text" : "password";
    toggleLoginPw.textContent = pw.type === "password" ? "👁️" : "🙈";
  });
}
