"""Playwright-based scraper for the FIFA ticket portal.

Uses a real browser to bypass JavaScript-based protections and render the
ticket portal dynamically. On first run, the user may need to complete a
CAPTCHA manually (in headed mode).
"""

from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime

from wctm.config import ScraperConfig
from wctm.models import Match, TicketStatus
from wctm.scraper.base import BaseScraper

logger = logging.getLogger(__name__)

FIFA_TICKET_URL = "https://www.fifa.com/fifaplus/en/tournaments/mens/worldcup/26/tickets"


class BrowserScraper(BaseScraper):
    """Scraper that uses Playwright to render the FIFA ticket portal."""

    def __init__(self, config: ScraperConfig) -> None:
        self.config = config
        self._browser = None
        self._context = None
        self._playwright = None

    async def _ensure_browser(self) -> None:
        """Launch browser if not already running."""
        if self._browser is not None:
            return

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            raise RuntimeError(
                "Playwright is required for browser scraping.\n"
                "Install it with: pip install playwright && playwright install chromium"
            )

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.config.headless,
        )
        self._context = await self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
        )
        logger.info("Browser launched (headless=%s)", self.config.headless)

    async def check_ticket_availability(self, match: Match) -> TicketStatus:
        """Navigate to the FIFA ticket page and check availability for a match."""
        await self._ensure_browser()

        page = await self._context.new_page()
        try:
            # Add a small random delay to look more human
            await asyncio.sleep(random.uniform(1.5, 4.0))

            target_url = match.fifa_url or FIFA_TICKET_URL
            logger.info("Checking tickets for %s at %s", match.label, target_url)

            await page.goto(target_url, wait_until="domcontentloaded", timeout=self.config.timeout_seconds * 1000)

            # Wait for the main content to load
            await page.wait_for_timeout(3000)

            # Look for ticket-related elements on the page
            # These selectors target FIFA's ticket portal structure
            available = False
            categories: list[str] = []
            price_range: str | None = None
            ticket_url: str | None = None

            # Strategy 1: Look for "Buy Tickets" or "Get Tickets" buttons
            buy_buttons = await page.query_selector_all(
                'a[href*="ticket"], button:has-text("ticket"), '
                'a:has-text("Buy"), a:has-text("Get Tickets"), '
                '[data-testid*="ticket"], .ticket-cta'
            )

            if buy_buttons:
                available = True
                for btn in buy_buttons:
                    text = (await btn.inner_text()).strip()
                    if text:
                        categories.append(text)
                    href = await btn.get_attribute("href")
                    if href and "ticket" in href.lower():
                        ticket_url = href

            # Strategy 2: Look for "Sold Out" or "Coming Soon" indicators
            sold_out = await page.query_selector_all(
                ':has-text("Sold Out"), :has-text("Coming Soon"), '
                ':has-text("Not Available"), :has-text("Unavailable")'
            )
            if sold_out and not buy_buttons:
                available = False

            # Strategy 3: Look for price information
            price_elements = await page.query_selector_all(
                '[class*="price"], [data-testid*="price"], '
                ':has-text("USD"), :has-text("$")'
            )
            for el in price_elements[:3]:
                text = (await el.inner_text()).strip()
                if "$" in text or "USD" in text:
                    price_range = text
                    break

            return TicketStatus(
                match_id=match.match_id,
                available=available,
                categories=categories,
                price_range=price_range,
                checked_at=datetime.now(),
                ticket_url=ticket_url,
            )

        except Exception as e:
            logger.error("Error checking tickets for %s: %s", match.match_id, e)
            return TicketStatus(
                match_id=match.match_id,
                available=False,
                checked_at=datetime.now(),
            )
        finally:
            await page.close()

    async def close(self) -> None:
        """Shut down the browser."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._browser = None
        self._context = None
        self._playwright = None
        logger.info("Browser closed")
