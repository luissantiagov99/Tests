"""Monitoring scheduler - periodically checks ticket availability."""

from __future__ import annotations

import asyncio
import logging
import random
import signal
from datetime import datetime

from wctm.config import AppConfig
from wctm.matches import MATCHES_BY_ID
from wctm.models import Match, TicketStatus
from wctm.notifier.base import BaseNotifier
from wctm.scraper.base import BaseScraper
from wctm.state import StateDB

logger = logging.getLogger(__name__)


class TicketMonitor:
    """Orchestrates periodic ticket checks and notifications."""

    def __init__(
        self,
        config: AppConfig,
        scraper: BaseScraper,
        notifiers: list[BaseNotifier],
        db: StateDB,
    ) -> None:
        self.config = config
        self.scraper = scraper
        self.notifiers = notifiers
        self.db = db
        self._running = False

    async def check_match(self, match: Match) -> TicketStatus:
        """Check a single match and process notifications if tickets are newly available."""
        previous = self.db.get_last_ticket_status(match.match_id)
        current = await self.scraper.check_ticket_availability(match)

        # Save the check result
        self.db.save_ticket_check(current)

        # Notify if tickets just became available (were not available before)
        if current.available and (previous is None or not previous.available):
            logger.info("NEW tickets available for %s!", match.label)
            await self._notify(match, current)
        elif current.available:
            logger.debug("Tickets still available for %s (already notified)", match.label)
        else:
            logger.debug("No tickets for %s yet", match.label)

        return current

    async def _notify(self, match: Match, status: TicketStatus) -> None:
        """Send notifications through all configured channels."""
        for notifier in self.notifiers:
            channel = notifier.channel_name
            if self.db.was_notified_recently(match.match_id, channel, within_minutes=60):
                logger.debug("Skipping %s notification for %s (sent recently)", channel, match.match_id)
                continue
            try:
                success = notifier.send(match, status)
                if success:
                    self.db.record_notification(match.match_id, channel)
                    self.db.update_last_notified(match.match_id)
            except Exception as e:
                logger.error("Failed to send %s notification: %s", channel, e)

    async def check_all_watched(self) -> dict[str, TicketStatus]:
        """Run a single check cycle for all watched matches."""
        watches = self.db.get_watches()
        if not watches:
            logger.info("No matches being watched")
            return {}

        results: dict[str, TicketStatus] = {}
        for watch in watches:
            match = MATCHES_BY_ID.get(watch.match_id)
            if match is None:
                logger.warning("Unknown match ID in watch list: %s", watch.match_id)
                continue
            results[watch.match_id] = await self.check_match(match)

        return results

    async def run(self) -> None:
        """Start the continuous monitoring loop."""
        self._running = True

        # Handle shutdown signals
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self._stop)

        logger.info(
            "Monitor started. Checking every %d minutes (±%ds jitter)",
            self.config.polling.interval_minutes,
            self.config.polling.jitter_seconds,
        )

        while self._running:
            try:
                cycle_start = datetime.now()
                results = await self.check_all_watched()

                available_count = sum(1 for s in results.values() if s.available)
                logger.info(
                    "Check cycle complete: %d/%d matches have tickets available",
                    available_count,
                    len(results),
                )

            except Exception as e:
                logger.error("Error during check cycle: %s", e)

            # Wait for the next cycle with jitter
            interval = self.config.polling.interval_minutes * 60
            jitter = random.uniform(0, self.config.polling.jitter_seconds)
            wait_time = interval + jitter

            logger.debug("Next check in %.0f seconds", wait_time)

            try:
                await asyncio.sleep(wait_time)
            except asyncio.CancelledError:
                break

        await self.scraper.close()
        logger.info("Monitor stopped")

    def _stop(self) -> None:
        """Signal handler to stop the monitor gracefully."""
        logger.info("Shutdown signal received, stopping...")
        self._running = False
