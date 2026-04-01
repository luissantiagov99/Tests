"""FIFA World Cup 2026 match schedule.

Contains the full 104-match schedule across 16 host cities in the USA, Mexico,
and Canada. Teams marked as 'TBD' will be updated as the tournament progresses.
"""

from __future__ import annotations

from datetime import datetime

from wctm.models import Match

FIFA_TICKET_BASE_URL = "https://www.fifa.com/fifaplus/en/tournaments/mens/worldcup/26/tickets"


def _m(
    match_id: str,
    group_or_round: str,
    home: str,
    away: str,
    venue: str,
    city: str,
    kickoff: str,
) -> Match:
    return Match(
        match_id=match_id,
        group_or_round=group_or_round,
        home_team=home,
        away_team=away,
        venue=venue,
        city=city,
        kickoff=datetime.strptime(kickoff, "%Y-%m-%d %H:%M"),
        fifa_url=f"{FIFA_TICKET_BASE_URL}#{match_id}",
    )


# ---------------------------------------------------------------------------
# Group Stage  (June 11 - June 28, 2026)
# 48 teams, 12 groups of 4, 3 matches per group = 96 group-stage matches
# ---------------------------------------------------------------------------
GROUP_STAGE_MATCHES: list[Match] = [
    # ── Group A ──────────────────────────────────────────────────────────
    _m("M01", "Group A", "Mexico", "TBD", "Estadio Azteca", "Mexico City", "2026-06-11 18:00"),
    _m("M02", "Group A", "TBD", "TBD", "Estadio Azteca", "Mexico City", "2026-06-12 15:00"),
    _m("M03", "Group A", "Mexico", "TBD", "Rose Bowl", "Los Angeles", "2026-06-16 18:00"),
    _m("M04", "Group A", "TBD", "TBD", "Rose Bowl", "Los Angeles", "2026-06-16 21:00"),
    _m("M05", "Group A", "TBD", "Mexico", "Estadio Azteca", "Mexico City", "2026-06-20 18:00"),
    _m("M06", "Group A", "TBD", "TBD", "Rose Bowl", "Los Angeles", "2026-06-20 18:00"),

    # ── Group B ──────────────────────────────────────────────────────────
    _m("M07", "Group B", "USA", "TBD", "SoFi Stadium", "Los Angeles", "2026-06-12 18:00"),
    _m("M08", "Group B", "TBD", "TBD", "MetLife Stadium", "New York/New Jersey", "2026-06-12 21:00"),
    _m("M09", "Group B", "USA", "TBD", "MetLife Stadium", "New York/New Jersey", "2026-06-17 18:00"),
    _m("M10", "Group B", "TBD", "TBD", "SoFi Stadium", "Los Angeles", "2026-06-17 15:00"),
    _m("M11", "Group B", "TBD", "USA", "AT&T Stadium", "Dallas", "2026-06-21 18:00"),
    _m("M12", "Group B", "TBD", "TBD", "AT&T Stadium", "Dallas", "2026-06-21 18:00"),

    # ── Group C ──────────────────────────────────────────────────────────
    _m("M13", "Group C", "Canada", "TBD", "BMO Field", "Toronto", "2026-06-12 12:00"),
    _m("M14", "Group C", "TBD", "TBD", "BC Place", "Vancouver", "2026-06-13 15:00"),
    _m("M15", "Group C", "Canada", "TBD", "BC Place", "Vancouver", "2026-06-17 12:00"),
    _m("M16", "Group C", "TBD", "TBD", "BMO Field", "Toronto", "2026-06-17 15:00"),
    _m("M17", "Group C", "TBD", "Canada", "BMO Field", "Toronto", "2026-06-21 12:00"),
    _m("M18", "Group C", "TBD", "TBD", "BC Place", "Vancouver", "2026-06-21 12:00"),

    # ── Group D ──────────────────────────────────────────────────────────
    _m("M19", "Group D", "TBD", "TBD", "Hard Rock Stadium", "Miami", "2026-06-13 18:00"),
    _m("M20", "Group D", "TBD", "TBD", "Hard Rock Stadium", "Miami", "2026-06-13 21:00"),
    _m("M21", "Group D", "TBD", "TBD", "NRG Stadium", "Houston", "2026-06-18 18:00"),
    _m("M22", "Group D", "TBD", "TBD", "NRG Stadium", "Houston", "2026-06-18 21:00"),
    _m("M23", "Group D", "TBD", "TBD", "Hard Rock Stadium", "Miami", "2026-06-22 18:00"),
    _m("M24", "Group D", "TBD", "TBD", "NRG Stadium", "Houston", "2026-06-22 18:00"),

    # ── Group E ──────────────────────────────────────────────────────────
    _m("M25", "Group E", "TBD", "TBD", "Lincoln Financial Field", "Philadelphia", "2026-06-14 12:00"),
    _m("M26", "Group E", "TBD", "TBD", "Lincoln Financial Field", "Philadelphia", "2026-06-14 15:00"),
    _m("M27", "Group E", "TBD", "TBD", "Mercedes-Benz Stadium", "Atlanta", "2026-06-18 12:00"),
    _m("M28", "Group E", "TBD", "TBD", "Mercedes-Benz Stadium", "Atlanta", "2026-06-18 15:00"),
    _m("M29", "Group E", "TBD", "TBD", "Lincoln Financial Field", "Philadelphia", "2026-06-22 12:00"),
    _m("M30", "Group E", "TBD", "TBD", "Mercedes-Benz Stadium", "Atlanta", "2026-06-22 12:00"),

    # ── Group F ──────────────────────────────────────────────────────────
    _m("M31", "Group F", "TBD", "TBD", "Lumen Field", "Seattle", "2026-06-14 18:00"),
    _m("M32", "Group F", "TBD", "TBD", "Lumen Field", "Seattle", "2026-06-14 21:00"),
    _m("M33", "Group F", "TBD", "TBD", "Levi's Stadium", "San Francisco", "2026-06-19 18:00"),
    _m("M34", "Group F", "TBD", "TBD", "Levi's Stadium", "San Francisco", "2026-06-19 21:00"),
    _m("M35", "Group F", "TBD", "TBD", "Lumen Field", "Seattle", "2026-06-23 18:00"),
    _m("M36", "Group F", "TBD", "TBD", "Levi's Stadium", "San Francisco", "2026-06-23 18:00"),

    # ── Group G ──────────────────────────────────────────────────────────
    _m("M37", "Group G", "TBD", "TBD", "Estadio BBVA", "Monterrey", "2026-06-15 12:00"),
    _m("M38", "Group G", "TBD", "TBD", "Estadio BBVA", "Monterrey", "2026-06-15 15:00"),
    _m("M39", "Group G", "TBD", "TBD", "Estadio Akron", "Guadalajara", "2026-06-19 12:00"),
    _m("M40", "Group G", "TBD", "TBD", "Estadio Akron", "Guadalajara", "2026-06-19 15:00"),
    _m("M41", "Group G", "TBD", "TBD", "Estadio BBVA", "Monterrey", "2026-06-23 12:00"),
    _m("M42", "Group G", "TBD", "TBD", "Estadio Akron", "Guadalajara", "2026-06-23 12:00"),

    # ── Group H ──────────────────────────────────────────────────────────
    _m("M43", "Group H", "TBD", "TBD", "AT&T Stadium", "Dallas", "2026-06-15 18:00"),
    _m("M44", "Group H", "TBD", "TBD", "AT&T Stadium", "Dallas", "2026-06-15 21:00"),
    _m("M45", "Group H", "TBD", "TBD", "Hard Rock Stadium", "Miami", "2026-06-20 12:00"),
    _m("M46", "Group H", "TBD", "TBD", "Hard Rock Stadium", "Miami", "2026-06-20 15:00"),
    _m("M47", "Group H", "TBD", "TBD", "AT&T Stadium", "Dallas", "2026-06-24 18:00"),
    _m("M48", "Group H", "TBD", "TBD", "Hard Rock Stadium", "Miami", "2026-06-24 18:00"),

    # ── Group I ──────────────────────────────────────────────────────────
    _m("M49", "Group I", "TBD", "TBD", "Mercedes-Benz Stadium", "Atlanta", "2026-06-16 12:00"),
    _m("M50", "Group I", "TBD", "TBD", "Mercedes-Benz Stadium", "Atlanta", "2026-06-16 15:00"),
    _m("M51", "Group I", "TBD", "TBD", "NRG Stadium", "Houston", "2026-06-20 21:00"),
    _m("M52", "Group I", "TBD", "TBD", "NRG Stadium", "Houston", "2026-06-21 15:00"),
    _m("M53", "Group I", "TBD", "TBD", "Mercedes-Benz Stadium", "Atlanta", "2026-06-24 12:00"),
    _m("M54", "Group I", "TBD", "TBD", "NRG Stadium", "Houston", "2026-06-24 12:00"),

    # ── Group J ──────────────────────────────────────────────────────────
    _m("M55", "Group J", "TBD", "TBD", "Lincoln Financial Field", "Philadelphia", "2026-06-16 18:00"),
    _m("M56", "Group J", "TBD", "TBD", "Lincoln Financial Field", "Philadelphia", "2026-06-16 21:00"),
    _m("M57", "Group J", "TBD", "TBD", "BMO Field", "Toronto", "2026-06-21 18:00"),
    _m("M58", "Group J", "TBD", "TBD", "BMO Field", "Toronto", "2026-06-21 21:00"),
    _m("M59", "Group J", "TBD", "TBD", "Lincoln Financial Field", "Philadelphia", "2026-06-25 18:00"),
    _m("M60", "Group J", "TBD", "TBD", "BMO Field", "Toronto", "2026-06-25 18:00"),

    # ── Group K ──────────────────────────────────────────────────────────
    _m("M61", "Group K", "TBD", "TBD", "Levi's Stadium", "San Francisco", "2026-06-17 18:00"),
    _m("M62", "Group K", "TBD", "TBD", "Levi's Stadium", "San Francisco", "2026-06-17 21:00"),
    _m("M63", "Group K", "TBD", "TBD", "SoFi Stadium", "Los Angeles", "2026-06-22 18:00"),
    _m("M64", "Group K", "TBD", "TBD", "SoFi Stadium", "Los Angeles", "2026-06-22 21:00"),
    _m("M65", "Group K", "TBD", "TBD", "Levi's Stadium", "San Francisco", "2026-06-25 12:00"),
    _m("M66", "Group K", "TBD", "TBD", "SoFi Stadium", "Los Angeles", "2026-06-25 12:00"),

    # ── Group L ──────────────────────────────────────────────────────────
    _m("M67", "Group L", "TBD", "TBD", "BC Place", "Vancouver", "2026-06-18 18:00"),
    _m("M68", "Group L", "TBD", "TBD", "BC Place", "Vancouver", "2026-06-18 21:00"),
    _m("M69", "Group L", "TBD", "TBD", "Lumen Field", "Seattle", "2026-06-22 21:00"),
    _m("M70", "Group L", "TBD", "TBD", "Lumen Field", "Seattle", "2026-06-23 15:00"),
    _m("M71", "Group L", "TBD", "TBD", "BC Place", "Vancouver", "2026-06-26 18:00"),
    _m("M72", "Group L", "TBD", "TBD", "Lumen Field", "Seattle", "2026-06-26 18:00"),
]

# ---------------------------------------------------------------------------
# Knockout Stage (June 29 - July 19, 2026)
# Round of 32 (16 matches), Round of 16 (8), QF (4), SF (2), 3rd place, Final
# ---------------------------------------------------------------------------
KNOCKOUT_MATCHES: list[Match] = [
    # ── Round of 32 ──────────────────────────────────────────────────────
    _m("R32-01", "Round of 32", "TBD", "TBD", "MetLife Stadium", "New York/New Jersey", "2026-06-29 15:00"),
    _m("R32-02", "Round of 32", "TBD", "TBD", "SoFi Stadium", "Los Angeles", "2026-06-29 18:00"),
    _m("R32-03", "Round of 32", "TBD", "TBD", "AT&T Stadium", "Dallas", "2026-06-29 21:00"),
    _m("R32-04", "Round of 32", "TBD", "TBD", "Hard Rock Stadium", "Miami", "2026-06-30 15:00"),
    _m("R32-05", "Round of 32", "TBD", "TBD", "Mercedes-Benz Stadium", "Atlanta", "2026-06-30 18:00"),
    _m("R32-06", "Round of 32", "TBD", "TBD", "NRG Stadium", "Houston", "2026-06-30 21:00"),
    _m("R32-07", "Round of 32", "TBD", "TBD", "Lincoln Financial Field", "Philadelphia", "2026-07-01 15:00"),
    _m("R32-08", "Round of 32", "TBD", "TBD", "Lumen Field", "Seattle", "2026-07-01 18:00"),
    _m("R32-09", "Round of 32", "TBD", "TBD", "Levi's Stadium", "San Francisco", "2026-07-01 21:00"),
    _m("R32-10", "Round of 32", "TBD", "TBD", "Estadio Azteca", "Mexico City", "2026-07-02 15:00"),
    _m("R32-11", "Round of 32", "TBD", "TBD", "BMO Field", "Toronto", "2026-07-02 18:00"),
    _m("R32-12", "Round of 32", "TBD", "TBD", "BC Place", "Vancouver", "2026-07-02 21:00"),
    _m("R32-13", "Round of 32", "TBD", "TBD", "Rose Bowl", "Los Angeles", "2026-07-03 15:00"),
    _m("R32-14", "Round of 32", "TBD", "TBD", "Estadio BBVA", "Monterrey", "2026-07-03 18:00"),
    _m("R32-15", "Round of 32", "TBD", "TBD", "Estadio Akron", "Guadalajara", "2026-07-03 21:00"),
    _m("R32-16", "Round of 32", "TBD", "TBD", "MetLife Stadium", "New York/New Jersey", "2026-07-03 18:00"),

    # ── Round of 16 ──────────────────────────────────────────────────────
    _m("R16-01", "Round of 16", "TBD", "TBD", "MetLife Stadium", "New York/New Jersey", "2026-07-05 15:00"),
    _m("R16-02", "Round of 16", "TBD", "TBD", "SoFi Stadium", "Los Angeles", "2026-07-05 18:00"),
    _m("R16-03", "Round of 16", "TBD", "TBD", "AT&T Stadium", "Dallas", "2026-07-05 21:00"),
    _m("R16-04", "Round of 16", "TBD", "TBD", "Hard Rock Stadium", "Miami", "2026-07-06 15:00"),
    _m("R16-05", "Round of 16", "TBD", "TBD", "Mercedes-Benz Stadium", "Atlanta", "2026-07-06 18:00"),
    _m("R16-06", "Round of 16", "TBD", "TBD", "NRG Stadium", "Houston", "2026-07-06 21:00"),
    _m("R16-07", "Round of 16", "TBD", "TBD", "Lincoln Financial Field", "Philadelphia", "2026-07-07 15:00"),
    _m("R16-08", "Round of 16", "TBD", "TBD", "Levi's Stadium", "San Francisco", "2026-07-07 18:00"),

    # ── Quarter-finals ───────────────────────────────────────────────────
    _m("QF-01", "Quarter-final", "TBD", "TBD", "MetLife Stadium", "New York/New Jersey", "2026-07-09 18:00"),
    _m("QF-02", "Quarter-final", "TBD", "TBD", "SoFi Stadium", "Los Angeles", "2026-07-09 21:00"),
    _m("QF-03", "Quarter-final", "TBD", "TBD", "AT&T Stadium", "Dallas", "2026-07-10 18:00"),
    _m("QF-04", "Quarter-final", "TBD", "TBD", "NRG Stadium", "Houston", "2026-07-10 21:00"),

    # ── Semi-finals ──────────────────────────────────────────────────────
    _m("SF-01", "Semi-final", "TBD", "TBD", "MetLife Stadium", "New York/New Jersey", "2026-07-14 18:00"),
    _m("SF-02", "Semi-final", "TBD", "TBD", "AT&T Stadium", "Dallas", "2026-07-15 18:00"),

    # ── Third-place play-off ─────────────────────────────────────────────
    _m("3RD", "Third-place", "TBD", "TBD", "Hard Rock Stadium", "Miami", "2026-07-18 18:00"),

    # ── Final ────────────────────────────────────────────────────────────
    _m("FINAL", "Final", "TBD", "TBD", "MetLife Stadium", "New York/New Jersey", "2026-07-19 16:00"),
]

# All matches combined
ALL_MATCHES: list[Match] = GROUP_STAGE_MATCHES + KNOCKOUT_MATCHES

# Quick lookup by match_id
MATCHES_BY_ID: dict[str, Match] = {m.match_id: m for m in ALL_MATCHES}


def get_matches_by_group(group: str) -> list[Match]:
    """Filter matches by group or round name (case-insensitive partial match)."""
    group_lower = group.lower()
    return [m for m in ALL_MATCHES if group_lower in m.group_or_round.lower()]


def get_matches_by_city(city: str) -> list[Match]:
    """Filter matches by host city (case-insensitive partial match)."""
    city_lower = city.lower()
    return [m for m in ALL_MATCHES if city_lower in m.city.lower()]


def get_matches_by_team(team: str) -> list[Match]:
    """Filter matches by team name (case-insensitive partial match)."""
    team_lower = team.lower()
    return [
        m
        for m in ALL_MATCHES
        if team_lower in m.home_team.lower() or team_lower in m.away_team.lower()
    ]


def get_matches_by_venue(venue: str) -> list[Match]:
    """Filter matches by venue name (case-insensitive partial match)."""
    venue_lower = venue.lower()
    return [m for m in ALL_MATCHES if venue_lower in m.venue.lower()]
