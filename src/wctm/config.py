"""Configuration loading and management."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml


DEFAULT_CONFIG_DIR = Path.home() / ".config" / "wctm"
DEFAULT_CONFIG_PATH = DEFAULT_CONFIG_DIR / "config.yaml"


@dataclass
class SmtpConfig:
    enabled: bool = False
    host: str = "smtp.gmail.com"
    port: int = 587
    user: str = ""
    password: str = ""
    recipient: str = ""


@dataclass
class DesktopConfig:
    enabled: bool = True


@dataclass
class NotificationConfig:
    email: SmtpConfig = field(default_factory=SmtpConfig)
    desktop: DesktopConfig = field(default_factory=DesktopConfig)


@dataclass
class ScraperConfig:
    type: str = "browser"  # "browser" or "api"
    headless: bool = True
    timeout_seconds: int = 30


@dataclass
class PollingConfig:
    interval_minutes: int = 10
    jitter_seconds: int = 30


@dataclass
class AppConfig:
    polling: PollingConfig = field(default_factory=PollingConfig)
    scraper: ScraperConfig = field(default_factory=ScraperConfig)
    notifications: NotificationConfig = field(default_factory=NotificationConfig)
    db_path: str = str(DEFAULT_CONFIG_DIR / "wctm.db")


def load_config(path: Path | None = None) -> AppConfig:
    """Load configuration from YAML file, falling back to defaults."""
    config_path = path or DEFAULT_CONFIG_PATH

    if not config_path.exists():
        return AppConfig()

    with open(config_path) as f:
        raw = yaml.safe_load(f) or {}

    config = AppConfig()

    if "polling" in raw:
        p = raw["polling"]
        config.polling.interval_minutes = p.get("interval_minutes", 10)
        config.polling.jitter_seconds = p.get("jitter_seconds", 30)

    if "scraper" in raw:
        s = raw["scraper"]
        config.scraper.type = s.get("type", "browser")
        config.scraper.headless = s.get("headless", True)
        config.scraper.timeout_seconds = s.get("timeout_seconds", 30)

    if "notifications" in raw:
        n = raw["notifications"]
        if "email" in n:
            e = n["email"]
            config.notifications.email = SmtpConfig(
                enabled=e.get("enabled", False),
                host=e.get("smtp_host", "smtp.gmail.com"),
                port=e.get("smtp_port", 587),
                user=e.get("smtp_user", ""),
                password=e.get("smtp_password", os.environ.get("WCTM_SMTP_PASSWORD", "")),
                recipient=e.get("recipient", ""),
            )
        if "desktop" in n:
            config.notifications.desktop.enabled = n["desktop"].get("enabled", True)

    if "db_path" in raw:
        config.db_path = raw["db_path"]

    return config


def save_config(config: AppConfig, path: Path | None = None) -> None:
    """Save configuration to YAML file."""
    config_path = path or DEFAULT_CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "polling": {
            "interval_minutes": config.polling.interval_minutes,
            "jitter_seconds": config.polling.jitter_seconds,
        },
        "scraper": {
            "type": config.scraper.type,
            "headless": config.scraper.headless,
            "timeout_seconds": config.scraper.timeout_seconds,
        },
        "notifications": {
            "email": {
                "enabled": config.notifications.email.enabled,
                "smtp_host": config.notifications.email.host,
                "smtp_port": config.notifications.email.port,
                "smtp_user": config.notifications.email.user,
                "recipient": config.notifications.email.recipient,
            },
            "desktop": {
                "enabled": config.notifications.desktop.enabled,
            },
        },
        "db_path": config.db_path,
    }

    with open(config_path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
