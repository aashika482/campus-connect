# Sending email (sign-up and login codes). Uses SMTP when SMTP_HOST is set, e.g. the college's
# Microsoft 365 mailbox. Without it (local development), the message is printed in the server's
# log and kept in DEV_OUTBOX (the tests read codes from there).

import asyncio
import logging
import smtplib
from email.message import EmailMessage

from app.core.config import settings

log = logging.getLogger("campulse.mail")
DEV_OUTBOX: list[dict] = []   # newest last; only used without SMTP


def _send_smtp(msg: EmailMessage) -> None:
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as smtp:
        smtp.starttls()
        if settings.SMTP_USER:
            smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(msg)


async def send_mail(to: str, subject: str, body: str) -> None:
    if not settings.SMTP_HOST:
        DEV_OUTBOX.append({"to": to, "subject": subject, "body": body})
        del DEV_OUTBOX[:-50]
        log.warning("No SMTP_HOST set, so this email was not sent:\n  To: %s\n  %s\n  %s", to, subject, body)
        return
    msg = EmailMessage()
    msg["From"] = settings.MAIL_FROM or settings.SMTP_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    await asyncio.to_thread(_send_smtp, msg)   # smtplib blocks; keep the event loop free
