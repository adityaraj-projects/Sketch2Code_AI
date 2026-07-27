import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings


def send_email(to: str, subject: str, html_body: str) -> None:
    """
    Single choke point for all outgoing email. Swapping providers
    (SendGrid, SES, Postmark) in Phase 2+ only means editing this file.
    """
    if settings.EMAIL_BACKEND == "console":
        print("\n----- EMAIL (console backend) -----")
        print(f"To: {to}")
        print(f"Subject: {subject}")
        print(html_body)
        print("------------------------------------\n")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_SENDER
    msg["To"] = to
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.EMAIL_SENDER, [to], msg.as_string())


def send_verification_email(to: str, token: str) -> None:
    link = f"{settings.FRONTEND_ORIGIN}/verify-email?token={token}"
    send_email(
        to,
        "Verify your Sketch2Code AI account",
        f"""<p>Welcome to Sketch2Code AI 👋</p>
        <p>Click below to verify your email:</p>
        <p><a href="{link}">{link}</a></p>
        <p>This link expires in 24 hours.</p>""",
    )


def send_password_reset_email(to: str, token: str) -> None:
    link = f"{settings.FRONTEND_ORIGIN}/reset-password?token={token}"
    send_email(
        to,
        "Reset your Sketch2Code AI password",
        f"""<p>We received a request to reset your password.</p>
        <p><a href="{link}">{link}</a></p>
        <p>If this wasn't you, ignore this email. Link expires in 30 minutes.</p>""",
    )
