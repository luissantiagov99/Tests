"""Abstract base class for notification channels."""

from __future__ import annotations

from abc import ABC, abstractmethod

from wctm.models import Match, TicketStatus


class BaseNotifier(ABC):
    """Interface for notification channels."""

    @abstractmethod
    def send(self, match: Match, status: TicketStatus) -> bool:
        """Send a notification about ticket availability. Returns True on success."""
        ...

    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Unique name for this notification channel (e.g., 'email', 'desktop')."""
        ...
