"""Command-line interface for the World Cup Ticket Monitor."""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from wctm.config import AppConfig, load_config, save_config, DEFAULT_CONFIG_PATH
from wctm.matches import (
    ALL_MATCHES,
    MATCHES_BY_ID,
    get_matches_by_city,
    get_matches_by_group,
    get_matches_by_team,
    get_matches_by_venue,
)
from wctm.models import Match
from wctm.state import StateDB


def _get_table():
    """Try to import rich Table, fall back to simple formatting."""
    try:
        from rich.console import Console
        from rich.table import Table

        return Console, Table
    except ImportError:
        return None, None


def _print_matches(matches: list[Match], db: StateDB | None = None) -> None:
    """Display matches as a formatted table."""
    Console, Table = _get_table()

    if Console and Table:
        console = Console()
        table = Table(title="FIFA World Cup 2026 Matches", show_lines=False)
        table.add_column("ID", style="cyan", no_wrap=True)
        table.add_column("Round", style="magenta")
        table.add_column("Home", style="bold white")
        table.add_column("Away", style="bold white")
        table.add_column("Venue", style="green")
        table.add_column("City", style="green")
        table.add_column("Date", style="yellow")
        if db:
            table.add_column("Watched", style="red", justify="center")

        for m in matches:
            row = [
                m.match_id,
                m.group_or_round,
                m.home_team,
                m.away_team,
                m.venue,
                m.city,
                m.kickoff_str,
            ]
            if db:
                row.append("*" if db.is_watched(m.match_id) else "")
            table.add_row(*row)

        console.print(table)
    else:
        # Fallback plain text
        header = f"{'ID':<10} {'Round':<15} {'Home':<12} {'Away':<12} {'Venue':<30} {'City':<20} {'Date':<16}"
        if db:
            header += " W"
        print(header)
        print("-" * len(header))
        for m in matches:
            line = f"{m.match_id:<10} {m.group_or_round:<15} {m.home_team:<12} {m.away_team:<12} {m.venue:<30} {m.city:<20} {m.kickoff_str:<16}"
            if db:
                line += " *" if db.is_watched(m.match_id) else ""
            print(line)


def cmd_list_matches(args: argparse.Namespace, config: AppConfig) -> None:
    """List available matches with optional filters."""
    db = StateDB(config.db_path)
    matches = ALL_MATCHES

    if args.group:
        matches = get_matches_by_group(args.group)
    elif args.city:
        matches = get_matches_by_city(args.city)
    elif args.team:
        matches = get_matches_by_team(args.team)
    elif args.venue:
        matches = get_matches_by_venue(args.venue)
    elif args.round:
        matches = get_matches_by_group(args.round)

    if not matches:
        print("No matches found with the given filter.")
        return

    print(f"\nFound {len(matches)} match(es):\n")
    _print_matches(matches, db)
    db.close()


def cmd_watch(args: argparse.Namespace, config: AppConfig) -> None:
    """Add matches to the watch list."""
    db = StateDB(config.db_path)
    added = 0

    for match_id in args.match_ids:
        match_id_upper = match_id.upper()
        if match_id_upper not in MATCHES_BY_ID:
            print(f"  Unknown match ID: {match_id_upper}")
            continue
        match = MATCHES_BY_ID[match_id_upper]
        db.add_watch(match_id_upper, notify_email=True, notify_desktop=True)
        print(f"  + Watching: {match.label} ({match.group_or_round}, {match.kickoff_str})")
        added += 1

    print(f"\n{added} match(es) added to watch list.")
    db.close()


def cmd_unwatch(args: argparse.Namespace, config: AppConfig) -> None:
    """Remove a match from the watch list."""
    db = StateDB(config.db_path)
    match_id = args.match_id.upper()

    if db.remove_watch(match_id):
        match = MATCHES_BY_ID.get(match_id)
        label = match.label if match else match_id
        print(f"  Removed {label} from watch list.")
    else:
        print(f"  Match {match_id} was not in the watch list.")
    db.close()


def cmd_status(args: argparse.Namespace, config: AppConfig) -> None:
    """Show current watch list and last-known ticket status."""
    db = StateDB(config.db_path)
    watches = db.get_watches()

    if not watches:
        print("No matches being watched. Use 'wctm watch <match_id>' to start monitoring.")
        db.close()
        return

    Console, Table = _get_table()

    if Console and Table:
        console = Console()
        table = Table(title="Watched Matches - Ticket Status")
        table.add_column("ID", style="cyan")
        table.add_column("Match", style="bold white")
        table.add_column("Round", style="magenta")
        table.add_column("Date", style="yellow")
        table.add_column("Venue", style="green")
        table.add_column("Ticket Status", style="bold")
        table.add_column("Last Checked")

        for watch in watches:
            match = MATCHES_BY_ID.get(watch.match_id)
            last_status = db.get_last_ticket_status(watch.match_id)

            if match is None:
                continue

            if last_status:
                status_text = "[green]AVAILABLE[/green]" if last_status.available else "[red]Not available[/red]"
                checked = last_status.checked_at.strftime("%Y-%m-%d %H:%M")
            else:
                status_text = "[dim]Not checked yet[/dim]"
                checked = "-"

            table.add_row(
                watch.match_id,
                match.label,
                match.group_or_round,
                match.kickoff_str,
                f"{match.venue}, {match.city}",
                status_text,
                checked,
            )

        console.print(table)
    else:
        print(f"\nWatching {len(watches)} match(es):\n")
        for watch in watches:
            match = MATCHES_BY_ID.get(watch.match_id)
            last_status = db.get_last_ticket_status(watch.match_id)
            if match is None:
                continue
            status = last_status.summary if last_status else "Not checked yet"
            print(f"  [{watch.match_id}] {match.label} | {match.group_or_round} | {match.kickoff_str} | {status}")

    db.close()


def cmd_check(args: argparse.Namespace, config: AppConfig) -> None:
    """Run a one-shot ticket availability check."""
    from wctm.notifier.desktop import DesktopNotifier
    from wctm.notifier.email import EmailNotifier
    from wctm.scheduler import TicketMonitor
    from wctm.scraper.browser import BrowserScraper

    db = StateDB(config.db_path)
    scraper = BrowserScraper(config.scraper)

    notifiers = []
    if config.notifications.desktop.enabled:
        notifiers.append(DesktopNotifier(enabled=True))
    if config.notifications.email.enabled:
        notifiers.append(EmailNotifier(config.notifications.email))

    monitor = TicketMonitor(config, scraper, notifiers, db)

    print("Running one-shot ticket check...\n")
    results = asyncio.run(monitor.check_all_watched())

    if not results:
        print("No matches being watched. Use 'wctm watch <match_id>' first.")
    else:
        for match_id, status in results.items():
            match = MATCHES_BY_ID.get(match_id)
            label = match.label if match else match_id
            icon = "✓" if status.available else "✗"
            print(f"  {icon} {label}: {status.summary}")

    asyncio.run(scraper.close())
    db.close()


def cmd_monitor(args: argparse.Namespace, config: AppConfig) -> None:
    """Start continuous monitoring."""
    from wctm.notifier.desktop import DesktopNotifier
    from wctm.notifier.email import EmailNotifier
    from wctm.scheduler import TicketMonitor
    from wctm.scraper.browser import BrowserScraper

    db = StateDB(config.db_path)
    scraper = BrowserScraper(config.scraper)

    notifiers = []
    if config.notifications.desktop.enabled:
        notifiers.append(DesktopNotifier(enabled=True))
    if config.notifications.email.enabled:
        notifiers.append(EmailNotifier(config.notifications.email))

    monitor = TicketMonitor(config, scraper, notifiers, db)

    print("Starting World Cup Ticket Monitor...")
    print(f"Checking every {config.polling.interval_minutes} minutes")
    print("Press Ctrl+C to stop.\n")

    try:
        asyncio.run(monitor.run())
    except KeyboardInterrupt:
        pass
    finally:
        db.close()


def cmd_setup(args: argparse.Namespace, config: AppConfig) -> None:
    """Interactive first-time setup."""
    print("World Cup Ticket Monitor - Setup\n")

    # Polling
    interval = input(f"Polling interval in minutes [{config.polling.interval_minutes}]: ").strip()
    if interval:
        config.polling.interval_minutes = max(5, int(interval))

    # Desktop notifications
    desktop = input(f"Enable desktop notifications? [Y/n]: ").strip().lower()
    config.notifications.desktop.enabled = desktop != "n"

    # Email notifications
    email = input("Enable email notifications? [y/N]: ").strip().lower()
    config.notifications.email.enabled = email == "y"

    if config.notifications.email.enabled:
        config.notifications.email.host = input(f"SMTP host [{config.notifications.email.host}]: ").strip() or config.notifications.email.host
        port = input(f"SMTP port [{config.notifications.email.port}]: ").strip()
        if port:
            config.notifications.email.port = int(port)
        config.notifications.email.user = input("SMTP username (email): ").strip()
        config.notifications.email.recipient = input(f"Recipient email [{config.notifications.email.user}]: ").strip() or config.notifications.email.user
        print("Set the WCTM_SMTP_PASSWORD environment variable for your email password.")

    # Browser settings
    headless = input("Run browser in headless mode? [Y/n]: ").strip().lower()
    config.scraper.headless = headless != "n"

    save_config(config)
    print(f"\nConfiguration saved to {DEFAULT_CONFIG_PATH}")


def cmd_web(args: argparse.Namespace, config: AppConfig) -> None:
    """Launch the web dashboard."""
    from wctm.web.app import create_app

    app = create_app(config)
    print(f"\n  World Cup Ticket Monitor - Web Dashboard")
    print(f"  Open http://localhost:{args.port} in your browser\n")
    app.run(host=args.host, port=args.port, debug=args.debug)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="wctm",
        description="World Cup 2026 Ticket Monitor - Get notified when FIFA releases tickets",
    )
    parser.add_argument(
        "--config", "-c", type=str, default=None, help="Path to config file"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # list-matches
    p_list = subparsers.add_parser("list-matches", aliases=["ls"], help="List World Cup 2026 matches")
    p_list.add_argument("--group", "-g", type=str, help="Filter by group (e.g., 'A', 'Group B')")
    p_list.add_argument("--city", type=str, help="Filter by host city")
    p_list.add_argument("--team", "-t", type=str, help="Filter by team name")
    p_list.add_argument("--venue", type=str, help="Filter by venue name")
    p_list.add_argument("--round", "-r", type=str, help="Filter by round (e.g., 'Quarter', 'Final')")
    p_list.set_defaults(func=cmd_list_matches)

    # watch
    p_watch = subparsers.add_parser("watch", help="Add match(es) to your watch list")
    p_watch.add_argument("match_ids", nargs="+", help="Match ID(s) to watch (e.g., M01 M07 FINAL)")
    p_watch.set_defaults(func=cmd_watch)

    # unwatch
    p_unwatch = subparsers.add_parser("unwatch", help="Remove a match from your watch list")
    p_unwatch.add_argument("match_id", help="Match ID to remove")
    p_unwatch.set_defaults(func=cmd_unwatch)

    # status
    p_status = subparsers.add_parser("status", help="Show watched matches and ticket status")
    p_status.set_defaults(func=cmd_status)

    # check
    p_check = subparsers.add_parser("check", help="Run a one-shot ticket check now")
    p_check.set_defaults(func=cmd_check)

    # monitor
    p_monitor = subparsers.add_parser("monitor", help="Start continuous ticket monitoring")
    p_monitor.set_defaults(func=cmd_monitor)

    # setup
    p_setup = subparsers.add_parser("setup", help="Interactive first-time setup")
    p_setup.set_defaults(func=cmd_setup)

    # web
    p_web = subparsers.add_parser("web", help="Launch the web dashboard")
    p_web.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    p_web.add_argument("--port", "-p", type=int, default=5000, help="Port (default: 5000)")
    p_web.add_argument("--debug", action="store_true", help="Enable debug mode")
    p_web.set_defaults(func=cmd_web)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # Load config
    config_path = None
    if args.config:
        from pathlib import Path

        config_path = Path(args.config)
    config = load_config(config_path)

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    args.func(args, config)
