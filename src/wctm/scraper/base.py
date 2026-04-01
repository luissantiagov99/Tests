"""Abstract base class for ticket scrapers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from wctm.models import Match, TicketStatus


class BaseScraper(ABC):
    """Interface for FIFA ticket portal scrapers."""

    @abstractmethod
    async def check_ticket_availability(self, match: Match) -> TicketStatus:
        """Check if tickets are available for a specific match."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Clean up any resources (browser sessions, etc.)."""
        ...
