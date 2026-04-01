"""Data models for the World Cup Ticket Monitor."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Match:
    """Represents a FIFA World Cup 2026 match."""

    match_id: str
    group_or_round: str  # "Group A", "Round of 32", "Quarter-final", "Final", etc.
    home_team: str
    away_team: str
    venue: str
    city: str
    kickoff: datetime
    fifa_url: str = ""

    @property
    def label(self) -> str:
        return f"{self.home_team} vs {self.away_team}"

    @property
    def kickoff_str(self) -> str:
        return self.kickoff.strftime("%Y-%m-%d %H:%M")


@dataclass
class TicketStatus:
    """Ticket availability status for a specific match."""

    match_id: str
    available: bool
    categories: list[str] = field(default_factory=list)
    price_range: str | None = None
    checked_at: datetime = field(default_factory=datetime.now)
    ticket_url: str | None = None

    @property
    def summary(self) -> str:
        if not self.available:
            return "No tickets available"
        cats = ", ".join(self.categories) if self.categories else "Unknown categories"
        price = f" ({self.price_range})" if self.price_range else ""
        return f"Tickets available: {cats}{price}"


@dataclass
class UserWatch:
    """A match the user is monitoring for ticket availability."""

    match_id: str
    added_at: datetime = field(default_factory=datetime.now)
    last_notified: datetime | None = None
    notify_email: bool = True
    notify_desktop: bool = True
