"""Flask web application for the World Cup Ticket Monitor."""

from __future__ import annotations

import asyncio
import logging
import os
import threading
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for

from wctm.config import AppConfig, load_config, save_config, DEFAULT_CONFIG_PATH
from wctm.matches import (
    ALL_MATCHES,
    MATCHES_BY_ID,
    get_matches_by_city,
    get_matches_by_group,
    get_matches_by_team,
)
from wctm.state import StateDB

logger = logging.getLogger(__name__)

# ── Global monitor state ─────────────────────────────────────────────────
_monitor_thread: threading.Thread | None = None
_monitor_stop_event = threading.Event()


def create_app(config: AppConfig | None = None) -> Flask:
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static"),
    )
    app.secret_key = os.environ.get("WCTM_SECRET_KEY", "wctm-dev-key-change-in-prod")

    if config is None:
        config = load_config()

    app.config["WCTM_CONFIG"] = config

    def get_db() -> StateDB:
        return StateDB(app.config["WCTM_CONFIG"].db_path)

    # ── Helpers ───────────────────────────────────────────────────────

    def _get_watched_match_info(db: StateDB):
        watches = db.get_watches()
        result = []
        for w in watches:
            match = MATCHES_BY_ID.get(w.match_id)
            if match is None:
                continue
            status = db.get_last_ticket_status(w.match_id)
            result.append({"match": match, "status": status, "watch": w})
        return result

    # ── Routes ────────────────────────────────────────────────────────

    @app.route("/")
    def dashboard():
        db = get_db()
        watched_info = _get_watched_match_info(db)
        available_count = sum(1 for w in watched_info if w["status"] and w["status"].available)
        cfg = app.config["WCTM_CONFIG"]
        db.close()

        return render_template(
            "dashboard.html",
            active_page="dashboard",
            total_matches=len(ALL_MATCHES),
            watched_count=len(watched_info),
            available_count=available_count,
            monitor_running=_monitor_thread is not None and _monitor_thread.is_alive(),
            interval=cfg.polling.interval_minutes,
            watched_matches=watched_info,
        )

    @app.route("/matches")
    def matches_page():
        db = get_db()
        watches = db.get_watches()
        watched_ids = {w.match_id for w in watches}
        db.close()

        # Filters
        filter_group = request.args.get("group", "")
        filter_city = request.args.get("city", "")
        filter_team = request.args.get("team", "")

        matches = ALL_MATCHES
        if filter_group:
            matches = get_matches_by_group(filter_group)
        if filter_city:
            matches = [m for m in matches if filter_city.lower() in m.city.lower()]
        if filter_team:
            matches = [
                m for m in matches
                if filter_team.lower() in m.home_team.lower()
                or filter_team.lower() in m.away_team.lower()
            ]

        # Unique groups and cities for filter dropdowns
        groups = sorted(set(m.group_or_round for m in ALL_MATCHES))
        cities = sorted(set(m.city for m in ALL_MATCHES))

        return render_template(
            "matches.html",
            active_page="matches",
            matches=matches,
            watched_ids=watched_ids,
            groups=groups,
            cities=cities,
            filter_group=filter_group,
            filter_city=filter_city,
            filter_team=filter_team,
        )

    @app.route("/watched")
    def watched_page():
        db = get_db()
        watched_info = _get_watched_match_info(db)
        db.close()

        return render_template(
            "watched.html",
            active_page="watched",
            watched_matches=watched_info,
        )

    @app.route("/settings")
    def settings_page():
        cfg = app.config["WCTM_CONFIG"]
        return render_template(
            "settings.html",
            active_page="settings",
            config=cfg,
        )

    @app.route("/settings/save", methods=["POST"])
    def save_settings():
        cfg = app.config["WCTM_CONFIG"]

        # Polling
        cfg.polling.interval_minutes = max(5, int(request.form.get("interval_minutes", 10)))
        cfg.polling.jitter_seconds = int(request.form.get("jitter_seconds", 30))

        # Scraper
        cfg.scraper.type = request.form.get("scraper_type", "browser")
        cfg.scraper.headless = "headless" in request.form
        cfg.scraper.timeout_seconds = int(request.form.get("timeout_seconds", 30))

        # Desktop
        cfg.notifications.desktop.enabled = "desktop_enabled" in request.form

        # Email
        cfg.notifications.email.enabled = "email_enabled" in request.form
        cfg.notifications.email.host = request.form.get("smtp_host", "smtp.gmail.com")
        cfg.notifications.email.port = int(request.form.get("smtp_port", 587))
        cfg.notifications.email.user = request.form.get("smtp_user", "")
        cfg.notifications.email.recipient = request.form.get("recipient", "")

        password = request.form.get("smtp_password", "")
        if password:
            cfg.notifications.email.password = password

        save_config(cfg)
        app.config["WCTM_CONFIG"] = cfg

        flash("Settings saved successfully!", "success")
        return redirect(url_for("settings_page"))

    @app.route("/watch/<match_id>", methods=["POST"])
    def watch_match(match_id):
        match_id = match_id.upper()
        if match_id not in MATCHES_BY_ID:
            flash(f"Unknown match ID: {match_id}", "error")
            return redirect(request.referrer or url_for("matches_page"))

        db = get_db()
        db.add_watch(match_id)
        db.close()

        match = MATCHES_BY_ID[match_id]
        flash(f"Now watching: {match.label} ({match.group_or_round})", "success")
        return redirect(request.referrer or url_for("matches_page"))

    @app.route("/unwatch/<match_id>", methods=["POST"])
    def unwatch_match(match_id):
        match_id = match_id.upper()
        db = get_db()
        removed = db.remove_watch(match_id)
        db.close()

        if removed:
            match = MATCHES_BY_ID.get(match_id)
            label = match.label if match else match_id
            flash(f"Stopped watching: {label}", "info")
        else:
            flash(f"Match {match_id} was not in your watch list", "error")

        return redirect(request.referrer or url_for("dashboard"))

    @app.route("/monitor/start", methods=["POST"])
    def monitor_start():
        global _monitor_thread, _monitor_stop_event

        if _monitor_thread and _monitor_thread.is_alive():
            flash("Monitor is already running", "info")
            return redirect(url_for("dashboard"))

        _monitor_stop_event.clear()
        _monitor_thread = threading.Thread(
            target=_run_monitor_loop,
            args=(app.config["WCTM_CONFIG"], _monitor_stop_event),
            daemon=True,
        )
        _monitor_thread.start()
        flash("Monitor started!", "success")
        return redirect(url_for("dashboard"))

    @app.route("/monitor/stop", methods=["POST"])
    def monitor_stop():
        global _monitor_thread
        _monitor_stop_event.set()
        flash("Monitor stopped", "info")
        return redirect(url_for("dashboard"))

    @app.route("/check", methods=["POST"])
    def check_now():
        cfg = app.config["WCTM_CONFIG"]
        thread = threading.Thread(target=_run_single_check, args=(cfg,), daemon=True)
        thread.start()
        flash("Ticket check started! Results will appear shortly.", "info")
        return redirect(request.referrer or url_for("dashboard"))

    return app


# ── Background monitor ───────────────────────────────────────────────────

def _run_monitor_loop(config: AppConfig, stop_event: threading.Event) -> None:
    """Run the ticket monitor in a background thread."""
    import time
    import random

    logger.info("Background monitor started")

    while not stop_event.is_set():
        _run_single_check(config)

        interval = config.polling.interval_minutes * 60
        jitter = random.uniform(0, config.polling.jitter_seconds)
        wait_time = interval + jitter

        # Wait in small increments so we can respond to stop events
        elapsed = 0.0
        while elapsed < wait_time and not stop_event.is_set():
            time.sleep(min(2.0, wait_time - elapsed))
            elapsed += 2.0

    logger.info("Background monitor stopped")


def _run_single_check(config: AppConfig) -> None:
    """Run a single check cycle for all watched matches."""
    from wctm.notifier.desktop import DesktopNotifier
    from wctm.notifier.email import EmailNotifier
    from wctm.scheduler import TicketMonitor
    from wctm.scraper.browser import BrowserScraper

    db = StateDB(config.db_path)

    watches = db.get_watches()
    if not watches:
        db.close()
        return

    scraper = BrowserScraper(config.scraper)
    notifiers = []
    if config.notifications.desktop.enabled:
        notifiers.append(DesktopNotifier(enabled=True))
    if config.notifications.email.enabled:
        notifiers.append(EmailNotifier(config.notifications.email))

    monitor = TicketMonitor(config, scraper, notifiers, db)

    loop = asyncio.new_event_loop()
    try:
        results = loop.run_until_complete(monitor.check_all_watched())
        available = sum(1 for s in results.values() if s.available)
        logger.info("Check complete: %d/%d have tickets", available, len(results))
    except Exception as e:
        logger.error("Check failed: %s", e)
    finally:
        loop.run_until_complete(scraper.close())
        loop.close()
        db.close()


def run_web(host: str = "0.0.0.0", port: int = 5000, debug: bool = False) -> None:
    """Start the web server."""
    config = load_config()
    app = create_app(config)
    app.run(host=host, port=port, debug=debug)
