"""
Enhanced PBS System with Conflict Resolution
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import re


@dataclass
class ConflictResolution:
    """Represents a conflict with resolution options"""

    description: str
    option_a: Dict
    option_b: Dict
    recommendation: str


def generate_advanced_pbs_strategy(
    preferences_text: str, pilot_profile: Dict = None
) -> Dict:
    """Generate PBS strategy with conflict detection"""

    commands = []
    conflicts = []
    text_lower = preferences_text.lower()

    # Check for conflicting preferences
    conflict_pairs = []

    # Weekend conflict check
    wants_weekends_off = any(
        phrase in text_lower for phrase in ["weekends off", "no weekends"]
    )
    wants_weekend_work = any(
        phrase in text_lower
        for phrase in ["prefer weekends", "weekend flying", "weekend pay"]
    )

    if wants_weekends_off and wants_weekend_work:
        conflict_pairs.append(
            {
                "description": "You want both weekends off AND weekend work",
                "option_a": {
                    "command": "AVOID TRIPS IF DUTY_PERIOD OVERLAPS SAT OR SUN",
                    "explanation": "Keep weekends free for personal time",
                },
                "option_b": {
                    "command": "PREFER TRIPS IF DUTY_PERIOD OVERLAPS SAT OR SUN",
                    "explanation": "Work weekends for extra pay",
                },
                "recommendation": "Choose based on your current priority: family time or extra income",
            }
        )

    # Trip length conflict
    wants_short = "short trip" in text_lower or "day trip" in text_lower
    wants_long = "long trip" in text_lower or "multi-day" in text_lower

    if wants_short and wants_long:
        conflict_pairs.append(
            {
                "description": "You want both short AND long trips",
                "option_a": {
                    "command": "PREFER TRIPS IF DUTY_DAYS <= 2",
                    "explanation": "Prefer shorter trips for more days at home",
                },
                "option_b": {
                    "command": "PREFER TRIPS IF DUTY_DAYS >= 4",
                    "explanation": "Prefer longer trips for commute efficiency",
                },
                "recommendation": "Consider your commuting situation and family needs",
            }
        )

    # Generate base commands (without conflicts)
    base_commands = []

    # Time preferences (no conflicts usually)
    if "no early" in text_lower or "avoid early" in text_lower:
        base_commands.append(
            {
                "command": "AVOID TRIPS IF DEPARTURE_TIME < 0800",
                "explanation": "Avoid early morning departures",
                "priority": 3,
            }
        )

    if "no late" in text_lower or "avoid late" in text_lower:
        base_commands.append(
            {
                "command": "AVOID TRIPS IF ARRIVAL_TIME > 2200",
                "explanation": "Avoid late night arrivals",
                "priority": 3,
            }
        )

    # Add resolved preferences (pick option A by default for now)
    for conflict in conflict_pairs:
        conflicts.append(
            ConflictResolution(
                description=conflict["description"],
                option_a=conflict["option_a"],
                option_b=conflict["option_b"],
                recommendation=conflict["recommendation"],
            )
        )
        # Add option A by default
        base_commands.append(conflict["option_a"])

    # Add non-conflicting preferences
    if not wants_weekends_off and not wants_weekend_work:
        if "weekend" in text_lower:
            base_commands.append(
                {
                    "command": "AVOID TRIPS IF DUTY_PERIOD OVERLAPS SAT OR SUN",
                    "explanation": "Avoid weekend work",
                    "priority": 2,
                }
            )

    if not wants_short and not wants_long:
        if "short" in text_lower:
            base_commands.append(
                {
                    "command": "PREFER TRIPS IF DUTY_DAYS <= 2",
                    "explanation": "Prefer shorter trips",
                    "priority": 4,
                }
            )

    # Red-eye preferences
    if "no redeye" in text_lower or "no red-eye" in text_lower:
        base_commands.append(
            {
                "command": "AVOID TRIPS IF DEPARTURE_TIME BETWEEN 2200 AND 0559",
                "explanation": "Avoid red-eye flights",
                "priority": 5,
            }
        )

    # Location preferences
    if "denver" in text_lower:
        base_commands.append(
            {
                "command": "PREFER TRIPS IF LAYOVER_STATION = DEN",
                "explanation": "Prefer Denver layovers",
                "priority": 6,
            }
        )

    # Commute preferences
    if "commut" in text_lower:
        base_commands.append(
            {
                "command": "PREFER TRIPS IF DEPARTURE_TIME >= 1000",
                "explanation": "Allow commute time",
                "priority": 3,
            }
        )

    return {
        "commands": base_commands,
        "conflicts": conflicts,
        "statistics": {
            "total_filters": len(base_commands),
            "conflicts_found": len(conflicts),
            "layers_used": 1,
        },
        "validation": {"valid_syntax": True, "within_limits": len(base_commands) <= 20},
    }
