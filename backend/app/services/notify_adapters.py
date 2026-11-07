"""Push / email adapters (M8+). Interfaces are real; providers plug in via env.

- PushAdapter: sends to device tokens (FCM when FCM_SERVER_KEY set, else logs-only).
- EmailAdapter: SMTP when MAIL_HOST set, else logs-only.

Never claim delivery without provider confirmation. Notifications are already
persisted in-app; these adapters are best-effort mirrors.
"""
import os

class PushAdapter:
    def send(self, token: str, title: str, body: str) -> dict:
        key = os.getenv("FCM_SERVER_KEY", "")
        if not token:
            return {"sent": False, "reason": "no token"}
        if not key:
            return {"sent": False, "reason": "FCM not configured (log-only)"}
        import httpx
        r = httpx.post(
            "https://fcm.googleapis.com/fcm/send",
            headers={"Authorization": f"key={key}", "Content-Type": "application/json"},
            json={"to": token, "notification": {"title": title, "body": body}},
            timeout=10,
        )
        return {"sent": r.status_code == 200, "status": r.status_code}


class EmailAdapter:
    def send(self, to: str, subject: str, body: str) -> dict:
        host = os.getenv("MAIL_HOST", "")
        if not host:
            return {"sent": False, "reason": "SMTP not configured (log-only)"}
        import smtplib
        from email.message import EmailMessage
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = os.getenv("MAIL_FROM", "noreply@sixto.example.com")
        msg["To"] = to
        msg.set_content(body)
        with smtplib.SMTP(host, int(os.getenv("MAIL_PORT", "587"))) as s:
            s.starttls()
            s.login(os.getenv("MAIL_USER", ""), os.getenv("MAIL_PASS", ""))
            s.send_message(msg)
        return {"sent": True}
