import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings


def send_otp_email(to_email: str, otp: str) -> None:
    """Send OTP password reset email via SMTP."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"KRYVON — Your password reset code: {otp}"
    msg["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.SMTP_USER}>"
    msg["To"] = to_email

    html = f"""
    <div style="font-family: -apple-system, sans-serif; max-width: 480px; margin: 0 auto; background: #0A0A0A; color: #fff; padding: 40px; border-radius: 16px;">
        <h1 style="background: linear-gradient(135deg, #00D4FF, #7A5CFF); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 32px; margin-bottom: 8px;">KRYVON</h1>
        <p style="color: rgba(255,255,255,0.6); margin-bottom: 32px;">Password Reset</p>

        <p style="color: rgba(255,255,255,0.9);">Your one-time reset code is:</p>

        <div style="background: rgba(0,212,255,0.1); border: 1px solid rgba(0,212,255,0.3); border-radius: 12px; padding: 24px; text-align: center; margin: 24px 0;">
            <span style="font-size: 40px; font-weight: bold; letter-spacing: 12px; color: #00D4FF;">{otp}</span>
        </div>

        <p style="color: rgba(255,255,255,0.5); font-size: 14px;">This code expires in <strong>10 minutes</strong>. If you didn't request this, ignore this email.</p>
    </div>
    """

    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_USER, to_email, msg.as_string())
