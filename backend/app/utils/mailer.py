import os
import requests

RESEND_URL = "https://api.resend.com/emails"

def send_email(to_email: str, subject: str, body_text: str):
    api_key = os.getenv("RESEND_API_KEY")
    # ✅ keep this as ONLY email, not "Name <email>"
    from_email = os.getenv("RESEND_FROM", "onboarding@resend.dev")

    if not api_key:
        raise RuntimeError("RESEND_API_KEY not set")

    to_email = (to_email or "").strip()
    if not to_email:
        raise RuntimeError("send_email(): to_email is empty")

    payload = {
        # ✅ Resend requires from in "Name <email>" format (we build it here)
        "from": f"HealthBot AI <{from_email}>",
        "to": [to_email],          # ✅ MUST be list
        "subject": subject,
        "text": body_text,
    }

    r = requests.post(
        RESEND_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=20,
    )

    if r.status_code not in (200, 201):
        raise RuntimeError(f"Resend error {r.status_code}: {r.text}")

    return r.json()