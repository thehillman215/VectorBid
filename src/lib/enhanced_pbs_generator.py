# enhanced_pbs_generator.py
"""
Comprehensive PBS 2.0 Command Generator for VectorBid
Handles complete PBS syntax based on airline industry research
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class CommandType(Enum):
    AVOID = "AVOID"
    PREFER = "PREFER"
    AWARD = "AWARD"
    OFF = "OFF"


class Priority(Enum):
    CRITICAL = 1  # Must-have constraints
    HIGH = 2  # Strong preferences
    MEDIUM = 3  # Moderate preferences
    LOW = 4  # Tie-breakers
    FALLBACK = 5  # Last resort


@dataclass
class PBSCommand:
    """Represents a single PBS command with metadata"""

    command_type: CommandType
    subject: str
    condition: str
    value: str
    priority: Priority
    explanation: str
    layer_number: int = 0

    def to_pbs_string(self) -> str:
        """Convert to PBS command string"""
        if self.command_type == CommandType.OFF:
            return f"OFF {self.value}"
        else:
            return f"{self.command_type.value} {self.subject} {self.condition} {self.value}"


class EnhancedPBSGenerator:
    """
    Advanced PBS command generator that understands complete PBS 2.0 syntax
    and generates layered bidding strategies from natural language
    """

    def __init__(self):
        self.commands: List[PBSCommand] = []
        self.pilot_profile = {}

        # Aircraft mapping for United Airlines
        self.united_aircraft = {
            "narrowbody": ["737", "757", "A319", "A320"],
            "widebody": ["767", "777", "787", "A350"],
            "737": "737",
            "boeing": ["737", "757", "767", "777", "787"],
            "airbus": ["A319", "A320", "A350"],
        }

        # Common airport codes pilots reference
        self.airport_codes = {
            "west_coast": ["LAX", "SFO", "SEA", "PDX", "SAN"],
            "east_coast": ["JFK", "LGA", "EWR", "BOS", "DCA"],
            "hub": ["ORD", "DEN", "IAH", "EWR", "SFO", "LAX"],
            "avoid_common": ["LGA", "EWR", "JFK", "LAX"],  # Often congested
        }

        # Time patterns (24-hour format)
        self.time_patterns = {
            "early_morning": (500, 800),
            "morning": (800, 1200),
            "afternoon": (1200, 1700),
            "evening": (1700, 2200),
            "red_eye": (2200, 559),
            "commutable_start": 1000,  # 10:00 AM or later
            "commutable_end": 2000,  # 8:00 PM or earlier
        }

    def set_pilot_profile(self, profile: Dict[str, Any]):
        """Set pilot profile for personalized command generation"""
        self.pilot_profile = profile

    def parse_natural_language(self, preferences: str) -> List[PBSCommand]:
        """
        Parse natural language preferences into PBS commands
        This is the main entry point that replaces natural_language_to_pbs_filters()
        """
        self.commands = []
        text = preferences.lower().strip()

        if not text:
            return self._generate_default_commands()

        # Process different types of preferences
        self._process_weekend_preferences(text)
        self._process_time_preferences(text)
        self._process_trip_length_preferences(text)
        self._process_destination_preferences(text)
        self._process_aircraft_preferences(text)
        self._process_layover_preferences(text)
        self._process_commute_preferences(text)
        self._process_credit_preferences(text)
        self._process_reserve_preferences(text)
        self._process_specific_dates(text)
        self._process_work_life_balance(text)

        # Sort commands by priority and assign layer numbers
        self._assign_layers()

        return self.commands

    def _process_weekend_preferences(self, text: str):
        """Process weekend-related preferences"""
        weekend_avoid_patterns = [
            r"no weekend|avoid weekend|weekends? off",
            r"never work weekend|no saturday|no sunday",
            r"weekend free|need weekends off",
        ]

        weekend_prefer_patterns = [
            r"prefer weekend|like weekend|weekend work",
            r"work saturday|work sunday",
        ]

        for pattern in weekend_avoid_patterns:
            if re.search(pattern, text):
                self.commands.append(
                    PBSCommand(
                        command_type=CommandType.AVOID,
                        subject="TRIPS",
                        condition="IF DUTY_PERIOD OVERLAPS",
                        value="WEEKEND",
                        priority=Priority.HIGH,
                        explanation="Avoids working on weekends for better work-life balance",
                        layer_number=2,
                    )
                )
                break

        for pattern in weekend_prefer_patterns:
            if re.search(pattern, text):
                self.commands.append(
                    PBSCommand(
                        command_type=CommandType.PREFER,
                        subject="TRIPS",
                        condition="IF DUTY_PERIOD OVERLAPS",
                        value="WEEKEND",
                        priority=Priority.MEDIUM,
                        explanation="Prefers trips that include weekend work for higher pay",
                        layer_number=15,
                    )
                )
                break

    def _process_time_preferences(self, text: str):
        """Process time-related preferences"""
        # Early morning avoidance
        early_patterns = [
            r"no early|avoid early|hate early|no morning|late start",
            r"not before (\d{1,2}):?(\d{2})?",
            r"after (\d{1,2}):?(\d{2})?",
        ]

        for pattern in early_patterns:
            match = re.search(pattern, text)
            if match:
                if "not before" in match.group() or "after" in match.group():
                    # Extract time if specified
                    time_match = re.search(r"(\d{1,2}):?(\d{2})?", match.group())
                    if time_match:
                        hour = int(time_match.group(1))
                        minute = int(time_match.group(2) or 0)
                        time_val = f"{hour:02d}{minute:02d}"
                    else:
                        time_val = "1000"  # Default 10:00 AM

                    self.commands.append(
                        PBSCommand(
                            command_type=CommandType.PREFER,
                            subject="TRIPS",
                            condition="STARTING AFTER",
                            value=time_val,
                            priority=Priority.HIGH,
                            explanation=f"Prefers trips starting after {time_val[:2]}:{time_val[2:]} for better commute",
                            layer_number=3,
                        )
                    )
                else:
                    self.commands.append(
                        PBSCommand(
                            command_type=CommandType.AVOID,
                            subject="TRIPS",
                            condition="STARTING BEFORE",
                            value="0800",
                            priority=Priority.HIGH,
                            explanation="Avoids early morning departures",
                            layer_number=3,
                        )
                    )
                break

        # Red-eye avoidance
        redeye_patterns = [
            r"no red.?eye|avoid red.?eye|hate red.?eye",
            r"no overnight|no late night|no midnight",
        ]

        for pattern in redeye_patterns:
            if re.search(pattern, text):
                self.commands.append(
                    PBSCommand(
                        command_type=CommandType.AVOID,
                        subject="TRIPS",
                        condition="IF DEPARTURE_TIME BETWEEN",
                        value="2200 AND 0559",
                        priority=Priority.HIGH,
                        explanation="Avoids red-eye flights for better rest",
                        layer_number=4,
                    )
                )
                break

    def _process_trip_length_preferences(self, text: str):
        """Process trip duration preferences"""
        short_trip_patterns = [
            r"short trip|day trip|quick trip|1.day|one.day",
            r"home every night|home daily|no overnight",
        ]

        long_trip_patterns = [
            r"long trip|extended trip|4.day|5.day|week.long",
            r"efficient trip|maximize credit",
        ]

        for pattern in short_trip_patterns:
            if re.search(pattern, text):
                self.commands.append(
                    PBSCommand(
                        command_type=CommandType.PREFER,
                        subject="TRIPS",
                        condition="WITH DUTY_DAYS",
                        value="<= 2",
                        priority=Priority.MEDIUM,
                        explanation="Prefers shorter trips for more time at home",
                        layer_number=10,
                    )
                )
                break

        for pattern in long_trip_patterns:
            if re.search(pattern, text):
                self.commands.append(
                    PBSCommand(
                        command_type=CommandType.PREFER,
                        subject="TRIPS",
                        condition="WITH DUTY_DAYS",
                        value=">= 4",
                        priority=Priority.MEDIUM,
                        explanation="Prefers longer trips for efficiency and higher credit",
                        layer_number=12,
                    )
                )
                break

    def _process_destination_preferences(self, text: str):
        """Process destination and route preferences"""
        # International preferences
        intl_avoid_patterns = [
            r"no international|avoid international|domestic only",
            r"no intl|no overseas|no transoceanic",
        ]

        intl_prefer_patterns = [
            r"international|overseas|europe|asia|transoceanic",
            r"long haul|wide.?body routes",
        ]

        for pattern in intl_avoid_patterns:
            if re.search(pattern, text):
                self.commands.append(
                    PBSCommand(
                        command_type=CommandType.AVOID,
                        subject="TRIPS",
                        condition="WITH DESTINATION",
                        value="INTERNATIONAL",
                        priority=Priority.HIGH,
                        explanation="Avoids international flights",
                        layer_number=5,
                    )
                )
                break

        for pattern in intl_prefer_patterns:
            if re.search(pattern, text):
                self.commands.append(
                    PBSCommand(
                        command_type=CommandType.PREFER,
                        subject="TRIPS",
                        condition="WITH DESTINATION",
                        value="INTERNATIONAL",
                        priority=Priority.MEDIUM,
                        explanation="Prefers international routes for variety and pay premiums",
                        layer_number=13,
                    )
                )
                break

        # Specific destination mentions
        for dest_group, airports in self.airport_codes.items():
            if dest_group in text:
                if "avoid" in text or "no" in text:
                    airport_list = ",".join(airports)
                    self.commands.append(
                        PBSCommand(
                            command_type=CommandType.AVOID,
                            subject="TRIPS",
                            condition="IF DESTINATION IN",
                            value=f"({airport_list})",
                            priority=Priority.MEDIUM,
                            explanation=f"Avoids {dest_group} destinations",
                            layer_number=8,
                        )
                    )
                else:
                    airport_list = ",".join(airports)
                    self.commands.append(
                        PBSCommand(
                            command_type=CommandType.PREFER,
                            subject="TRIPS",
                            condition="IF DESTINATION IN",
                            value=f"({airport_list})",
                            priority=Priority.LOW,
                            explanation=f"Prefers {dest_group} destinations",
                            layer_number=20,
                        )
                    )

    def _process_aircraft_preferences(self, text: str):
        """Process aircraft type preferences"""
        for aircraft_group, types in self.united_aircraft.items():
            if aircraft_group in text:
                if isinstance(types, list):
                    aircraft_list = ",".join(types)
                    value = f"({aircraft_list})"
                else:
                    value = types

                if "avoid" in text or "no" in text:
                    self.commands.append(
                        PBSCommand(
                            command_type=CommandType.AVOID,
                            subject="TRIPS",
                            condition=(
                                "IF AIRCRAFT IN"
                                if isinstance(types, list)
                                else "IF AIRCRAFT ="
                            ),
                            value=value,
                            priority=Priority.MEDIUM,
                            explanation=f"Avoids {aircraft_group} aircraft",
                            layer_number=9,
                        )
                    )
                else:
                    self.commands.append(
                        PBSCommand(
                            command_type=CommandType.PREFER,
                            subject="TRIPS",
                            condition=(
                                "IF AIRCRAFT IN"
                                if isinstance(types, list)
                                else "IF AIRCRAFT ="
                            ),
                            value=value,
                            priority=Priority.LOW,
                            explanation=f"Prefers {aircraft_group} aircraft",
                            layer_number=18,
                        )
                    )

    def _process_layover_preferences(self, text: str):
        """Process layover duration and location preferences"""
        # Layover duration
        short_layover_patterns = [
            r"short layover|quick turn|no long layover",
            r"tight connection|efficient routing",
        ]

        long_layover_patterns = [
            r"long layover|extended layover|good rest",
            r"12.hour|overnight layover",
        ]

        for pattern in short_layover_patterns:
            if re.search(pattern, text):
                self.commands.append(
                    PBSCommand(
                        command_type=CommandType.PREFER,
                        subject="TRIPS",
                        condition="IF LAYOVER",
                        value="<= 12:00",
                        priority=Priority.LOW,
                        explanation="Prefers shorter layovers for efficiency",
                        layer_number=22,
                    )
                )
                break

        for pattern in long_layover_patterns:
            if re.search(pattern, text):
                self.commands.append(
                    PBSCommand(
                        command_type=CommandType.PREFER,
                        subject="TRIPS",
                        condition="IF LAYOVER",
                        value=">= 12:00",
                        priority=Priority.LOW,
                        explanation="Prefers longer layovers for proper rest",
                        layer_number=21,
                    )
                )
                break

    def _process_commute_preferences(self, text: str):
        """Process commuter-friendly preferences"""
        commute_patterns = [
            r"commut|easy commute|commuter friendly",
            r"live in (\w+)|commute from (\w+)|home (\w+)",
        ]

        for pattern in commute_patterns:
            if re.search(pattern, text):
                # Add commuter-friendly timing
                self.commands.append(
                    PBSCommand(
                        command_type=CommandType.PREFER,
                        subject="TRIPS",
                        condition="STARTING AFTER",
                        value="1000 ON MON,TUE,WED,THU,FRI",
                        priority=Priority.HIGH,
                        explanation="Prefers late starts on weekdays for commuter accessibility",
                        layer_number=6,
                    )
                )

                self.commands.append(
                    PBSCommand(
                        command_type=CommandType.PREFER,
                        subject="TRIPS",
                        condition="ENDING BEFORE",
                        value="2000",
                        priority=Priority.HIGH,
                        explanation="Prefers trips ending early enough for same-day commute home",
                        layer_number=7,
                    )
                )
                break

    def _process_credit_preferences(self, text: str):
        """Process credit hours and pay preferences"""
        high_credit_patterns = [
            r"high credit|max credit|maximize pay|money maker",
            r"75.hour|80.hour|high value",
        ]

        for pattern in high_credit_patterns:
            if re.search(pattern, text):
                self.commands.append(
                    PBSCommand(
                        command_type=CommandType.PREFER,
                        subject="TRIPS",
                        condition="WITH CREDIT_TIME",
                        value=">= 75",
                        priority=Priority.MEDIUM,
                        explanation="Prefers high-credit trips for maximum pay efficiency",
                        layer_number=14,
                    )
                )
                break

    def _process_reserve_preferences(self, text: str):
        """Process reserve duty preferences"""
        reserve_avoid_patterns = [
            r"avoid reserve|no reserve|hate reserve|any line",
            r"reserve avoider|line holder",
        ]

        for pattern in reserve_avoid_patterns:
            if re.search(pattern, text):
                self.commands.append(
                    PBSCommand(
                        command_type=CommandType.PREFER,
                        subject="LINE",
                        condition="OVER",
                        value="RESERVE",
                        priority=Priority.CRITICAL,
                        explanation="Strongly prefers any line over reserve duty",
                        layer_number=1,
                    )
                )
                break

    def _process_specific_dates(self, text: str):
        """Process specific date requests"""
        # Pattern for dates like "15th", "January 15", "15"
        date_patterns = [
            r"home for .*(\d{1,2})(st|nd|rd|th)?",
            r"need (\w+) (\d{1,2})",
            r"important on (\d{1,2})",
            r"birthday.*(\d{1,2})",
            r"anniversary.*(\d{1,2})",
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    date_num = re.search(r"(\d{1,2})", match.group()).group(1)
                    self.commands.append(
                        PBSCommand(
                            command_type=CommandType.AVOID,
                            subject="TRIPS",
                            condition="ON DATE",
                            value=f"({date_num})",
                            priority=Priority.CRITICAL,
                            explanation=f"Must be home on the {date_num}th for personal commitment",
                            layer_number=1,
                        )
                    )
                except:
                    pass  # Skip if can't parse date

    def _process_work_life_balance(self, text: str):
        """Process general work-life balance preferences"""
        qol_patterns = [
            r"quality of life|work.life balance|family time",
            r"family first|time at home|max days off",
        ]

        for pattern in qol_patterns:
            if re.search(pattern, text):
                self.commands.append(
                    PBSCommand(
                        command_type=CommandType.PREFER,
                        subject="TRIPS",
                        condition="WITH",
                        value="MAX_DAYS_OFF",
                        priority=Priority.MEDIUM,
                        explanation="Optimizes schedule for maximum days off and family time",
                        layer_number=11,
                    )
                )
                break

    def _generate_default_commands(self) -> List[PBSCommand]:
        """Generate sensible default commands when no preferences given"""
        defaults = [
            PBSCommand(
                command_type=CommandType.PREFER,
                subject="LINE",
                condition="OVER",
                value="RESERVE",
                priority=Priority.HIGH,
                explanation="Default: Prefers line flying over reserve",
                layer_number=1,
            ),
            PBSCommand(
                command_type=CommandType.PREFER,
                subject="TRIPS",
                condition="WITH",
                value="MAX_DAYS_OFF",
                priority=Priority.MEDIUM,
                explanation="Default: Seeks work-life balance",
                layer_number=10,
            ),
            PBSCommand(
                command_type=CommandType.AVOID,
                subject="TRIPS",
                condition="IF DEPARTURE_TIME BETWEEN",
                value="2200 AND 0559",
                priority=Priority.MEDIUM,
                explanation="Default: Avoids red-eye flights",
                layer_number=5,
            ),
        ]
        return defaults

    def _assign_layers(self):
        """Assign layer numbers based on priority and command type"""
        # Sort by priority first, then by command type (AVOID first, then PREFER, then AWARD)
        self.commands.sort(
            key=lambda cmd: (
                cmd.priority.value,
                (
                    0
                    if cmd.command_type == CommandType.AVOID
                    else 1
                    if cmd.command_type == CommandType.PREFER
                    else 2
                ),
            )
        )

        # Assign layer numbers
        for i, cmd in enumerate(self.commands, 1):
            cmd.layer_number = min(i, 50)  # Cap at 50 layers

    def generate_pbs_output(self, include_explanations: bool = True) -> str:
        """Generate final PBS output string"""
        if not self.commands:
            return "No PBS commands generated. Please provide preferences."

        output_lines = [
            "VectorBid Generated PBS Commands",
            "=" * 40,
            f"Total Layers: {len(self.commands)}",
            "",
        ]

        for cmd in self.commands:
            layer_header = f"Layer {cmd.layer_number:2d} ({cmd.priority.name}):"
            pbs_command = f"  {cmd.to_pbs_string()}"

            output_lines.append(layer_header)
            output_lines.append(pbs_command)

            if include_explanations:
                explanation = f"  # {cmd.explanation}"
                output_lines.append(explanation)

            output_lines.append("")  # Blank line between commands

        # Add usage instructions
        output_lines.extend(
            [
                "=" * 40,
                "USAGE INSTRUCTIONS:",
                "1. Copy the commands above (without # comments)",
                "2. Log into your airline's PBS system",
                "3. Paste commands in order of layer numbers",
                "4. Adjust as needed for your specific situation",
                "5. Submit your bid",
                "",
                "Note: Commands are ordered by priority with most",
                "critical constraints first, followed by preferences.",
            ]
        )

        return "\n".join(output_lines)

    def get_commands_by_layer(self) -> Dict[int, List[PBSCommand]]:
        """Return commands organized by layer number"""
        layers = {}
        for cmd in self.commands:
            if cmd.layer_number not in layers:
                layers[cmd.layer_number] = []
            layers[cmd.layer_number].append(cmd)
        return layers

    def validate_commands(self) -> List[str]:
        """Validate PBS commands for syntax errors"""
        errors = []
        for cmd in self.commands:
            # Basic validation - can be expanded
            if not cmd.subject or not cmd.condition or not cmd.value:
                errors.append(f"Layer {cmd.layer_number}: Incomplete command structure")
        return errors


# Usage Example:
if __name__ == "__main__":
    generator = EnhancedPBSGenerator()

    # Test with sample preferences
    test_preferences = """
    I want weekends off and no early morning departures. 
    I'm a commuter living in Denver, so I need trips that start after 10 AM. 
    I prefer short trips, no red-eyes, and I need to be home for my daughter's birthday on the 15th.
    I want to avoid reserve at all costs.
    """

    commands = generator.parse_natural_language(test_preferences)
    pbs_output = generator.generate_pbs_output()

    print(pbs_output)
    print(
        f"\nGenerated {len(commands)} PBS commands across {max([cmd.layer_number for cmd in commands])} layers"
    )
