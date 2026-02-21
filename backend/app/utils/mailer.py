import os
import requests

RESEND_URL = "https://api.resend.com/emails"

def send_email(to_email: str, subject: str, body_text: str):
    api_key = os.getenv("RESEND_API_KEY")
    from_addr = os.getenv("RESEND_FROM", "HealthBot AI <onboarding@resend.dev>")

    if not api_key:
        raise RuntimeError("RESEND_API_KEY not set")

    payload = {
        "from": from_addr,
        "to": [to_email],
        "subject": subject,
        "text": body_text,
    }

    response = requests.post(
        RESEND_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=20,
    )

    if response.status_code not in (200, 201):
        raise RuntimeError(f"Resend error {response.status_code}: {response.text}")