"""Email notification via SMTP."""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from wctm.config import SmtpConfig
from wctm.models import Match, TicketStatus
from wctm.notifier.base import BaseNotifier

logger = logging.getLogger(__name__)


class EmailNotifier(BaseNotifier):
    """Sends ticket alerts via SMTP email."""

    def __init__(self, config: SmtpConfig) -> None:
        self.config = config

    @property
    def channel_name(self) -> str:
        return "email"

    def send(self, match: Match, status: TicketStatus) -> bool:
        if not self.config.enabled:
            logger.debug("Email notifications disabled, skipping")
            return False

        if not self.config.user or not self.config.recipient:
            logger.warning("Email not configured (missing user or recipient)")
            return False

        subject = f"⚽ Tickets Available! {match.label} - FIFA World Cup 2026"

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: #326295; color: white; padding: 20px; text-align: center;">
                <h1>FIFA World Cup 2026</h1>
                <h2>Ticket Alert</h2>
            </div>
            <div style="padding: 20px;">
                <h3>{match.label}</h3>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr><td style="padding: 8px; font-weight: bold;">Round:</td><td>{match.group_or_round}</td></tr>
                    <tr><td style="padding: 8px; font-weight: bold;">Venue:</td><td>{match.venue}, {match.city}</td></tr>
                    <tr><td style="padding: 8px; font-weight: bold;">Date:</td><td>{match.kickoff_str}</td></tr>
                    <tr><td style="padding: 8px; font-weight: bold;">Status:</td><td style="color: green; font-weight: bold;">{status.summary}</td></tr>
                </table>
                {"<p><a href='" + status.ticket_url + "' style='background: #326295; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; margin-top: 16px;'>Buy Tickets Now</a></p>" if status.ticket_url else ""}
                <p style="color: #666; font-size: 12px; margin-top: 24px;">
                    Checked at: {status.checked_at.strftime("%Y-%m-%d %H:%M:%S")}<br>
                    Sent by World Cup Ticket Monitor (wctm)
                </p>
            </div>
        </body>
        </html>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.config.user
        msg["To"] = self.config.recipient

        text_body = (
            f"Tickets available for {match.label}!\n"
            f"Round: {match.group_or_round}\n"
            f"Venue: {match.venue}, {match.city}\n"
            f"Date: {match.kickoff_str}\n"
            f"Status: {status.summary}\n"
            f"{'Link: ' + status.ticket_url if status.ticket_url else ''}\n"
        )
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        try:
            with smtplib.SMTP(self.config.host, self.config.port) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.config.user, self.config.password)
                server.send_message(msg)
            logger.info("Email sent to %s for match %s", self.config.recipient, match.match_id)
            return True
        except Exception as e:
            logger.error("Failed to send email: %s", e)
            return False
