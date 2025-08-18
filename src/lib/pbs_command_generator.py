"""
PBS Command Generator for VectorBid
Production-grade implementation with LLM and pattern matching capabilities

Author: VectorBid Engineering
Version: 2.0.0
License: Proprietary
"""

import hashlib
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# CONFIGURATION
# ============================================


class Config:
    """Centralized configuration management"""

    # Feature flags
    USE_LLM: bool = os.environ.get("USE_LLM", "true").lower() == "true"
    USE_CACHE: bool = os.environ.get("USE_CACHE", "true").lower() == "true"

    # API Configuration
    OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_TIMEOUT: int = 30

    # Rate limiting
    MAX_REQUESTS_PER_MINUTE: int = 60
    MAX_TOKENS: int = 1500

    # Cache settings
    CACHE_TTL_SECONDS: int = 3600  # 1 hour
    MAX_CACHE_SIZE: int = 128

    # Quality thresholds
    MIN_QUALITY_SCORE: int = 60
    TARGET_COMMANDS: int = 8


# ============================================
# DATA MODELS
# ============================================


class CommandCategory(Enum):
    """PBS command categories"""

    WEEKENDS = "weekends"
    TIME_OF_DAY = "time_of_day"
    TRIP_LENGTH = "trip_length"
    LOCATIONS = "locations"
    EQUIPMENT = "equipment"
    COMMUTE = "commute"
    PAY = "pay"
    SPECIFIC_DATES = "specific_dates"
    GENERAL = "general"
    DEFAULT = "default"


@dataclass
class PBSCommand:
    """Individual PBS command with metadata"""

    command: str
    explanation: str
    priority: int
    category: CommandCategory
    confidence: float = 0.9

    def to_dict(self) -> dict:
        return {
            "command": self.command,
            "explanation": self.explanation,
            "priority": self.priority,
            "category": self.category.value,
            "confidence": self.confidence,
        }


@dataclass
class GenerationResult:
    """Complete result from PBS generation"""

    commands: list[PBSCommand]
    formatted: str
    stats: dict
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    generation_time_ms: int = 0

    def to_dict(self) -> dict:
        return {
            "commands": [cmd.to_dict() for cmd in self.commands],
            "formatted": self.formatted,
            "stats": self.stats,
            "errors": self.errors,
            "warnings": self.warnings,
            "generation_time_ms": self.generation_time_ms,
        }


@dataclass
class PilotProfile:
    """Structured pilot profile data"""

    base: str | None = None
    seniority: int | None = None
    fleet: list[str] | None = None
    flying_style: str | None = None
    commuter: bool = False

    @classmethod
    def from_dict(cls, data: dict | None) -> "PilotProfile":
        if not data:
            return cls()

        # Parse seniority
        seniority = data.get("seniority")
        if isinstance(seniority, str):
            seniority = int(re.sub(r"\D", "", seniority) or "50")
        elif not isinstance(seniority, int):
            seniority = 50

        # Parse fleet
        fleet_data = data.get("fleet")
        fleet = None
        if fleet_data:
            if isinstance(fleet_data, list):
                fleet = [str(f) for f in fleet_data if f is not None]
            else:
                fleet = [str(fleet_data)]

        return cls(
            base=data.get("base"),
            seniority=seniority,
            fleet=fleet,
            flying_style=data.get("flying_style"),
            commuter=data.get("commuter", False),
        )


# ============================================
# RATE LIMITING
# ============================================


class RateLimiter:
    """Simple in-memory rate limiter"""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: list[float] = []

    def allow_request(self) -> bool:
        """Check if request is allowed under rate limit"""
        now = time.time()
        # Remove old requests outside window
        self.requests = [r for r in self.requests if r > now - self.window_seconds]

        if len(self.requests) < self.max_requests:
            self.requests.append(now)
            return True
        return False

    def time_until_next_request(self) -> float:
        """Time in seconds until next request is allowed"""
        if len(self.requests) < self.max_requests:
            return 0
        oldest = min(self.requests)
        return max(0, self.window_seconds - (time.time() - oldest))


# ============================================
# CACHE IMPLEMENTATION
# ============================================


class CommandCache:
    """LRU cache for PBS commands with TTL"""

    def __init__(self, max_size: int = 128, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, tuple[GenerationResult, float]] = {}

    def _generate_key(self, preferences: str, profile: PilotProfile) -> str:
        """Generate cache key from inputs"""
        profile_str = json.dumps(profile.__dict__, sort_keys=True)
        combined = f"{preferences}:{profile_str}"
        return hashlib.md5(combined.encode()).hexdigest()

    def get(self, preferences: str, profile: PilotProfile) -> GenerationResult | None:
        """Retrieve from cache if valid"""
        if not Config.USE_CACHE:
            return None

        key = self._generate_key(preferences, profile)
        if key in self._cache:
            result, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl_seconds:
                logger.info("Cache hit for preferences")
                return result
            else:
                del self._cache[key]
        return None

    def set(self, preferences: str, profile: PilotProfile, result: GenerationResult):
        """Store in cache"""
        if not Config.USE_CACHE:
            return

        key = self._generate_key(preferences, profile)

        # Enforce max size (simple LRU)
        if len(self._cache) >= self.max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]

        self._cache[key] = (result, time.time())


# ============================================
# LLM INTEGRATION
# ============================================


class LLMGenerator:
    """OpenAI-based PBS command generation"""

    def __init__(self):
        self.client = None
        self.rate_limiter = RateLimiter(Config.MAX_REQUESTS_PER_MINUTE)
        self._initialize_client()

    def _initialize_client(self):
        """Initialize OpenAI client if available"""
        if not Config.USE_LLM or not Config.OPENAI_API_KEY:
            logger.info("LLM generation disabled or no API key")
            return

        try:
            from openai import OpenAI

            self.client = OpenAI(
                api_key=Config.OPENAI_API_KEY, timeout=Config.OPENAI_TIMEOUT
            )
            logger.info("OpenAI client initialized successfully")
        except ImportError:
            logger.warning("OpenAI library not installed. Run: pip install openai")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")

    def generate(
        self, preferences: str, profile: PilotProfile
    ) -> list[PBSCommand] | None:
        """Generate PBS commands using LLM"""

        if not self.client:
            return None

        # Rate limiting
        if not self.rate_limiter.allow_request():
            wait_time = self.rate_limiter.time_until_next_request()
            logger.warning(f"Rate limited. Wait {wait_time:.1f}s")
            return None

        try:
            prompt = self._build_prompt(preferences, profile)

            response = self.client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=Config.MAX_TOKENS,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from LLM")

            result = json.loads(content)
            return self._parse_llm_response(result)

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return None

    def _get_system_prompt(self) -> str:
        """Expert system prompt for PBS generation"""
        return """You are an elite PBS (Preferential Bidding System) specialist with 20+ years of experience optimizing airline pilot schedules.

Your expertise includes:
- Deep knowledge of PBS 2.0 syntax and best practices
- Understanding of airline operations, union contracts, and FAA regulations
- Ability to balance competing priorities (pay vs time off, commute vs efficiency)
- Knowledge of common pilot preferences and lifestyle needs

Generate PBS commands following these rules:
1. Use valid PBS 2.0 syntax with proper operators and conditions
2. Order commands by priority (1=highest, 10=lowest)
3. Maximum 12 commands (pilots rarely use more)
4. Include explanations for each command
5. Identify and resolve conflicts between preferences
6. Consider seniority limitations

Return JSON with this structure:
{
    "commands": [
        {
            "command": "AVOID TRIPS IF DUTY_PERIOD OVERLAPS SAT OR SUN",
            "explanation": "Protects weekends for family time",
            "priority": 1,
            "category": "weekends",
            "confidence": 0.95
        }
    ],
    "strategy": "Overall bidding strategy explanation",
    "conflicts": ["List of identified conflicts"],
    "suggestions": ["Additional suggestions for the pilot"]
}

Categories: weekends, time_of_day, trip_length, locations, equipment, commute, pay, specific_dates, general"""

    def _build_prompt(self, preferences: str, profile: PilotProfile) -> str:
        """Build contextualized prompt"""

        context_parts = ["PILOT PROFILE:"]

        if profile.base:
            context_parts.append(f"- Base: {profile.base}")

        if profile.seniority:
            if profile.seniority < 30:
                context_parts.append(
                    f"- Seniority: {profile.seniority}% (Junior - expect limited options)"
                )
            elif profile.seniority < 70:
                context_parts.append(
                    f"- Seniority: {profile.seniority}% (Mid-level - moderate flexibility)"
                )
            else:
                context_parts.append(
                    f"- Seniority: {profile.seniority}% (Senior - wide selection available)"
                )

        if profile.fleet:
            context_parts.append(f"- Aircraft: {', '.join(profile.fleet)}")

        if profile.commuter:
            context_parts.append("- Commuter (needs commutable trips)")

        if profile.flying_style:
            context_parts.append(f"- Style preference: {profile.flying_style}")

        context = "\n".join(context_parts)

        return f"""Generate PBS commands for this pilot's preferences:

PREFERENCES: {preferences}

{context}

Create realistic, actionable PBS commands that:
1. Directly address the stated preferences
2. Consider unstated but related needs
3. Account for seniority limitations
4. Optimize for both quality of life and efficiency
5. Are specific to this pilot's situation"""

    def _parse_llm_response(self, response: dict) -> list[PBSCommand]:
        """Parse LLM response into PBSCommand objects"""
        commands = []

        for cmd_data in response.get("commands", []):
            try:
                category = CommandCategory(cmd_data.get("category", "general"))
            except ValueError:
                category = CommandCategory.GENERAL

            command = PBSCommand(
                command=cmd_data.get("command", ""),
                explanation=cmd_data.get("explanation", ""),
                priority=cmd_data.get("priority", 5),
                category=category,
                confidence=cmd_data.get("confidence", 0.8),
            )
            commands.append(command)

        return commands


# ============================================
# PATTERN MATCHING ENGINE
# ============================================


class PatternMatcher:
    """Advanced pattern matching for PBS command generation"""

    # Pattern definitions: (keywords, command, explanation, priority, category)
    PATTERNS = {
        "weekends": [
            (
                ["weekends off", "no weekends", "avoid weekends"],
                "AVOID TRIPS IF DUTY_PERIOD OVERLAPS SAT OR SUN",
                "Keep weekends free",
                1,
                CommandCategory.WEEKENDS,
            ),
            (
                ["saturday off", "no saturday"],
                "AVOID TRIPS IF DUTY_PERIOD OVERLAPS SAT",
                "Keep Saturdays free",
                1,
                CommandCategory.WEEKENDS,
            ),
            (
                ["sunday off", "no sunday"],
                "AVOID TRIPS IF DUTY_PERIOD OVERLAPS SUN",
                "Keep Sundays free",
                1,
                CommandCategory.WEEKENDS,
            ),
        ],
        "time_of_day": [
            (
                ["no early", "avoid early", "late start"],
                "AVOID TRIPS IF DEPARTURE_TIME < 0800",
                "Avoid early morning departures",
                2,
                CommandCategory.TIME_OF_DAY,
            ),
            (
                ["early departure", "morning flight"],
                "PREFER TRIPS IF DEPARTURE_TIME BETWEEN 0600 AND 1000",
                "Prefer morning departures",
                3,
                CommandCategory.TIME_OF_DAY,
            ),
            (
                ["no late", "avoid late"],
                "AVOID TRIPS IF ARRIVAL_TIME > 2200",
                "Avoid late arrivals",
                3,
                CommandCategory.TIME_OF_DAY,
            ),
            (
                ["no redeye", "avoid redeye", "no red-eye"],
                "AVOID TRIPS IF DEPARTURE_TIME BETWEEN 2200 AND 0559",
                "Avoid red-eye flights",
                2,
                CommandCategory.TIME_OF_DAY,
            ),
        ],
        "trip_length": [
            (
                ["short trip", "day trip", "1 day", "turns"],
                "PREFER TRIPS IF DUTY_DAYS <= 2",
                "Prefer shorter trips",
                4,
                CommandCategory.TRIP_LENGTH,
            ),
            (
                ["long trip", "4 day", "four day"],
                "PREFER TRIPS IF DUTY_DAYS >= 4",
                "Prefer longer trips",
                4,
                CommandCategory.TRIP_LENGTH,
            ),
        ],
        "pay": [
            (
                ["high pay", "max pay", "maximize pay", "high credit"],
                "SORT BY CREDIT_HOURS DESCENDING",
                "Maximize pay",
                2,
                CommandCategory.PAY,
            ),
            (
                ["efficient", "productive"],
                "PREFER TRIPS IF CREDIT_RATIO > 1.2",
                "Prefer efficient trips",
                3,
                CommandCategory.PAY,
            ),
        ],
        "international": [
            (
                ["international", "overseas", "europe", "asia"],
                "PREFER TRIPS IF INTERNATIONAL = TRUE",
                "Prefer international flights",
                3,
                CommandCategory.LOCATIONS,
            ),
            (
                ["domestic only", "no international"],
                "AVOID TRIPS IF INTERNATIONAL = TRUE",
                "Avoid international flights",
                3,
                CommandCategory.LOCATIONS,
            ),
        ],
        "commute": [
            (
                ["commute", "commutable", "drive to"],
                "PREFER TRIPS IF DEPARTURE_TIME >= 1000",
                "Allow commute time",
                2,
                CommandCategory.COMMUTE,
            ),
        ],
        "holidays": [
            (
                ["christmas", "xmas"],
                "AVOID TRIPS IF DATE_RANGE INCLUDES 24DEC-26DEC",
                "Christmas off",
                1,
                CommandCategory.SPECIFIC_DATES,
            ),
            (
                ["thanksgiving"],
                "AVOID TRIPS IF DATE_RANGE INCLUDES 4TH_THU_NOV",
                "Thanksgiving off",
                1,
                CommandCategory.SPECIFIC_DATES,
            ),
            (
                ["new year"],
                "AVOID TRIPS IF DATE_RANGE INCLUDES 31DEC-01JAN",
                "New Year off",
                1,
                CommandCategory.SPECIFIC_DATES,
            ),
        ],
    }

    def generate(self, preferences: str, profile: PilotProfile) -> list[PBSCommand]:
        """Generate commands using pattern matching"""

        commands = []
        text_lower = preferences.lower()

        # Check all patterns
        for category_patterns in self.PATTERNS.values():
            for keywords, command, explanation, priority, category in category_patterns:
                if any(keyword in text_lower for keyword in keywords):
                    commands.append(
                        PBSCommand(
                            command=command,
                            explanation=explanation,
                            priority=priority,
                            category=category,
                            confidence=0.7,
                        )
                    )

        # Add profile-based commands
        commands.extend(self._generate_profile_commands(profile))

        # Add default if no commands
        if not commands:
            commands.append(
                PBSCommand(
                    command="PREFER TRIPS IF QUALITY_OF_LIFE = HIGH",
                    explanation="Default quality of life preference",
                    priority=10,
                    category=CommandCategory.DEFAULT,
                    confidence=0.5,
                )
            )

        # Remove duplicates and sort
        seen = set()
        unique_commands = []
        for cmd in sorted(commands, key=lambda x: x.priority):
            if cmd.command not in seen:
                seen.add(cmd.command)
                unique_commands.append(cmd)

        return unique_commands[: Config.TARGET_COMMANDS]

    def _generate_profile_commands(self, profile: PilotProfile) -> list[PBSCommand]:
        """Generate commands from pilot profile"""
        commands = []

        if profile.base:
            # Extract airport code if in format "City (ABC)"
            match = re.search(r"\(([A-Z]{3})\)", profile.base)
            if match:
                code = match.group(1)
                commands.append(
                    PBSCommand(
                        command=f"PREFER TRIPS IF BASE = {code}",
                        explanation="Home base preference",
                        priority=7,
                        category=CommandCategory.LOCATIONS,
                        confidence=0.9,
                    )
                )

        if profile.fleet:
            for aircraft in profile.fleet[:2]:  # Limit to 2 aircraft
                commands.append(
                    PBSCommand(
                        command=f"PREFER TRIPS IF EQUIPMENT = {aircraft}",
                        explanation=f"Qualified on {aircraft}",
                        priority=8,
                        category=CommandCategory.EQUIPMENT,
                        confidence=0.9,
                    )
                )

        if profile.commuter:
            commands.append(
                PBSCommand(
                    command="PREFER TRIPS IF DUTY_DAYS >= 3",
                    explanation="Minimize commute frequency",
                    priority=3,
                    category=CommandCategory.COMMUTE,
                    confidence=0.8,
                )
            )

        return commands


# ============================================
# MAIN GENERATOR CLASS
# ============================================


class PBSCommandGenerator:
    """Main PBS command generator with multiple strategies"""

    def __init__(self):
        self.llm_generator = LLMGenerator()
        self.pattern_matcher = PatternMatcher()
        self.cache = CommandCache(Config.MAX_CACHE_SIZE, Config.CACHE_TTL_SECONDS)
        logger.info("PBS Command Generator initialized")

    def generate(
        self, preferences_text: str, pilot_profile: dict | None = None
    ) -> dict:
        """
        Generate PBS commands from preferences

        Args:
            preferences_text: Natural language preferences
            pilot_profile: Optional pilot profile dictionary

        Returns:
            Dictionary with commands and metadata
        """

        start_time = time.time()

        # Validate input
        if not preferences_text or not preferences_text.strip():
            return self._default_response()

        # Parse profile
        profile = PilotProfile.from_dict(pilot_profile)

        # Check cache
        cached_result = self.cache.get(preferences_text, profile)
        if cached_result:
            return cached_result.to_dict()

        # Try LLM generation first
        commands = None
        generation_method = "unknown"

        if Config.USE_LLM:
            logger.info("Attempting LLM generation")
            commands = self.llm_generator.generate(preferences_text, profile)
            if commands:
                generation_method = "llm"
                logger.info(f"LLM generated {len(commands)} commands")

        # Fallback to pattern matching
        if not commands:
            logger.info("Using pattern matching")
            commands = self.pattern_matcher.generate(preferences_text, profile)
            generation_method = "pattern_matching"
            logger.info(f"Pattern matching generated {len(commands)} commands")

        # Build result
        result = self._build_result(
            commands,
            preferences_text,
            generation_method,
            int((time.time() - start_time) * 1000),
        )

        # Cache result
        self.cache.set(preferences_text, profile, result)

        return result.to_dict()

    def _build_result(
        self,
        commands: list[PBSCommand],
        preferences_text: str,
        method: str,
        time_ms: int,
    ) -> GenerationResult:
        """Build complete generation result"""

        # Format commands as text
        formatted = self._format_commands(commands, preferences_text, method)

        # Calculate statistics
        stats = self._calculate_stats(commands, method)

        # Check for warnings
        warnings = self._check_warnings(commands)

        return GenerationResult(
            commands=commands,
            formatted=formatted,
            stats=stats,
            errors=[],
            warnings=warnings,
            generation_time_ms=time_ms,
        )

    def _format_commands(
        self, commands: list[PBSCommand], preferences_text: str, method: str
    ) -> str:
        """Format commands as readable text"""

        quality = "HIGH" if method == "llm" else "GOOD"

        lines = [
            "# VectorBid PBS Commands",
            f"# Generated from: {preferences_text[:60]}...",
            f"# Method: {method.upper()} | Quality: {quality}",
            f"# Generated: {datetime.now().isoformat()}",
            "",
        ]

        for cmd in commands:
            confidence = f"[{cmd.confidence:.0%}]" if method == "llm" else ""
            lines.append(f"{cmd.command}  # {cmd.explanation} {confidence}")

        return "\n".join(lines)

    def _calculate_stats(self, commands: list[PBSCommand], method: str) -> dict:
        """Calculate generation statistics"""

        categories = {cmd.category for cmd in commands}
        avg_confidence = (
            sum(cmd.confidence for cmd in commands) / len(commands) if commands else 0
        )

        # Quality score calculation
        base_score = 70 if method == "llm" else 50
        command_bonus = min(30, len(commands) * 3)
        confidence_bonus = avg_confidence * 20
        quality_score = min(100, base_score + command_bonus + confidence_bonus)

        return {
            "total_commands": len(commands),
            "categories": len(categories),
            "category_list": [cat.value for cat in categories],
            "avg_confidence": round(avg_confidence, 2),
            "quality_score": round(quality_score),
            "generation_method": method,
            "has_conflicts": self._detect_conflicts(commands),
            "preference_coverage": min(100, len(commands) * 12),
        }

    def _detect_conflicts(self, commands: list[PBSCommand]) -> bool:
        """Detect potential conflicts in commands"""

        # Check for weekend avoidance + long trips
        has_weekend_avoid = any(
            "SAT OR SUN" in cmd.command
            for cmd in commands
            if cmd.category == CommandCategory.WEEKENDS
        )
        has_long_trips = any("DUTY_DAYS >= 4" in cmd.command for cmd in commands)

        if has_weekend_avoid and has_long_trips:
            return True

        # Check for early departure + late arrival
        has_no_early = any("DEPARTURE_TIME < " in cmd.command for cmd in commands)
        has_no_late = any("ARRIVAL_TIME >" in cmd.command for cmd in commands)

        if has_no_early and has_no_late:
            return True

        return False

    def _check_warnings(self, commands: list[PBSCommand]) -> list[str]:
        """Generate warnings about command set"""

        warnings = []

        if len(commands) > 10:
            warnings.append("Large number of commands may reduce bid success")

        if self._detect_conflicts(commands):
            warnings.append("Potential conflicts detected between preferences")

        high_priority_count = sum(1 for cmd in commands if cmd.priority <= 2)
        if high_priority_count > 4:
            warnings.append("Many high-priority items may be difficult to satisfy")

        return warnings

    def _default_response(self) -> dict:
        """Default response for empty input"""

        default_command = PBSCommand(
            command="PREFER TRIPS IF QUALITY_OF_LIFE = HIGH",
            explanation="Default preference",
            priority=10,
            category=CommandCategory.DEFAULT,
            confidence=0.5,
        )

        result = GenerationResult(
            commands=[default_command],
            formatted="# VectorBid PBS Commands\n# No preferences specified\n\nPREFER TRIPS IF QUALITY_OF_LIFE = HIGH  # Default preference",
            stats={
                "total_commands": 1,
                "categories": 1,
                "category_list": ["default"],
                "avg_confidence": 0.5,
                "quality_score": 50,
                "generation_method": "default",
                "has_conflicts": False,
                "preference_coverage": 50,
            },
        )

        return result.to_dict()


# ============================================
# PUBLIC API
# ============================================

# Singleton instance
_generator_instance: PBSCommandGenerator | None = None


def generate_pbs_commands(
    preferences_text: str, pilot_profile: dict | None = None
) -> dict:
    """
    Generate PBS commands from natural language preferences

    This is the main entry point that maintains backward compatibility
    with the existing application interface.

    Args:
        preferences_text: Natural language description of preferences
        pilot_profile: Optional pilot profile with base, seniority, fleet, etc.

    Returns:
        Dictionary containing:
            - commands: List of PBS command objects
            - formatted: Formatted text version
            - stats: Generation statistics
            - errors: Any errors encountered
            - warnings: Any warnings about the commands
    """

    global _generator_instance

    # Initialize singleton on first use
    if _generator_instance is None:
        _generator_instance = PBSCommandGenerator()

    try:
        return _generator_instance.generate(preferences_text, pilot_profile)
    except Exception as e:
        logger.error(f"Fatal error in PBS generation: {e}")
        # Return safe fallback
        return {
            "commands": [
                {
                    "command": "PREFER TRIPS IF QUALITY_OF_LIFE = HIGH",
                    "explanation": "Error occurred - using default",
                    "priority": 10,
                    "category": "default",
                }
            ],
            "formatted": "# Error in generation - using defaults\nPREFER TRIPS IF QUALITY_OF_LIFE = HIGH",
            "errors": [str(e)],
            "stats": {
                "total_commands": 1,
                "categories": 1,
                "quality_score": 0,
                "generation_method": "error_fallback",
            },
        }


# ============================================
# TESTING & VALIDATION
# ============================================

if __name__ == "__main__":
    """Comprehensive testing suite"""

    test_cases = [
        {
            "preferences": "I want weekends off and no early morning departures. Prefer high-credit trips.",
            "profile": {
                "base": "Denver (DEN)",
                "seniority": 65,
                "fleet": ["737", "757"],
            },
        },
        {
            "preferences": "Maximize pay, I'll fly anything including redeyes. International preferred.",
            "profile": {
                "base": "San Francisco (SFO)",
                "seniority": 85,
                "fleet": ["777"],
            },
        },
        {
            "preferences": "Short trips only, I commute from Vegas to Denver",
            "profile": {
                "base": "Denver (DEN)",
                "seniority": 45,
                "fleet": ["737"],
                "commuter": True,
            },
        },
        {
            "preferences": "Christmas and Thanksgiving off, avoid weekends when possible",
            "profile": {
                "base": "Chicago (ORD)",
                "seniority": 70,
                "fleet": ["320", "321"],
            },
        },
    ]

    print("=" * 80)
    print("PBS COMMAND GENERATOR - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print("Configuration:")
    print(f"  LLM Enabled: {Config.USE_LLM}")
    print(f"  Model: {Config.OPENAI_MODEL}")
    print(f"  Caching: {Config.USE_CACHE}")
    print("=" * 80)

    for i, test in enumerate(test_cases, 1):
        print(f"\n[TEST {i}]")
        print(f"Preferences: {test['preferences']}")
        print(f"Profile: {test['profile']}")
        print("-" * 40)

        result = generate_pbs_commands(test["preferences"], test["profile"])

        print(f"Generated {result['stats']['total_commands']} commands:")
        for cmd in result["commands"]:
            print(f"  [{cmd['priority']}] {cmd['command']}")
            print(f"      → {cmd['explanation']}")

        print("\nStatistics:")
        print(f"  Method: {result['stats']['generation_method']}")
        print(f"  Quality: {result['stats']['quality_score']}/100")
        print(f"  Categories: {', '.join(result['stats'].get('category_list', []))}")
        print(f"  Time: {result.get('generation_time_ms', 0)}ms")

        if result.get("warnings"):
            print(f"  ⚠️ Warnings: {', '.join(result['warnings'])}")

    print("\n" + "=" * 80)
    print("TEST SUITE COMPLETE")
    print("=" * 80)
