"""Desktop notification support (cross-platform)."""

from __future__ import annotations

import logging
import subprocess
import sys

from wctm.models import Match, TicketStatus
from wctm.notifier.base import BaseNotifier

logger = logging.getLogger(__name__)


class DesktopNotifier(BaseNotifier):
    """Sends desktop notifications using plyer or system-native commands."""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled

    @property
    def channel_name(self) -> str:
        return "desktop"

    def send(self, match: Match, status: TicketStatus) -> bool:
        if not self.enabled:
            return False

        title = "⚽ World Cup 2026 - Tickets Available!"
        message = (
            f"{match.label}\n"
            f"{match.group_or_round} | {match.venue}, {match.city}\n"
            f"{match.kickoff_str}\n"
            f"{status.summary}"
        )

        # Try plyer first (cross-platform)
        if self._try_plyer(title, message):
            return True

        # Fallback to system-native commands
        if self._try_native(title, message):
            return True

        logger.warning("No desktop notification method available")
        return False

    def _try_plyer(self, title: str, message: str) -> bool:
        try:
            from plyer import notification

            notification.notify(
                title=title,
                message=message,
                app_name="WCTM",
                timeout=15,
            )
            logger.info("Desktop notification sent via plyer")
            return True
        except Exception as e:
            logger.debug("plyer notification failed: %s", e)
            return False

    def _try_native(self, title: str, message: str) -> bool:
        try:
            if sys.platform == "linux":
                subprocess.run(
                    ["notify-send", title, message, "--app-name=WCTM", "-u", "critical"],
                    check=True,
                    timeout=5,
                )
                return True
            elif sys.platform == "darwin":
                script = f'display notification "{message}" with title "{title}"'
                subprocess.run(
                    ["osascript", "-e", script],
                    check=True,
                    timeout=5,
                )
                return True
        except Exception as e:
            logger.debug("Native notification failed: %s", e)
        return False
