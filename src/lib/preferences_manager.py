"""
Enhanced Preferences Manager for VectorBid
Handles advanced user preference management, learning, and optimization
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
from src.lib.services.db import get_profile, save_profile
from src.lib.personas import PILOT_PERSONAS


class PreferencesManager:
    """Manages pilot preferences with learning and optimization capabilities"""

    def __init__(self):
        self.preference_weights = {
            "time_of_day": 1.0,
            "trip_length": 1.0,
            "destinations": 0.8,
            "weekends": 1.2,
            "layovers": 0.9,
            "aircraft_type": 0.7,
            "credit_hours": 0.8,
        }

    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user preferences including learned patterns"""
        profile = get_profile(user_id)

        preferences = {
            "persona": profile.get("persona"),
            "custom_preferences": profile.get("custom_preferences"),
            "learned_patterns": self._get_learned_patterns(user_id),
            "preference_history": self._get_preference_history(user_id),
            "optimization_suggestions": self._get_optimization_suggestions(profile),
        }

        return preferences

    def update_preferences(self, user_id: str, updates: Dict[str, Any]) -> bool:
        """Update user preferences with learning integration"""
        try:
            profile = get_profile(user_id)

            # Track preference changes for learning
            self._track_preference_change(user_id, updates)

            # Update core preferences
            if "persona" in updates:
                profile["persona"] = updates["persona"]
                # Clear custom preferences if persona selected
                if updates["persona"] != "custom":
                    profile["custom_preferences"] = None

            if "custom_preferences" in updates:
                profile["custom_preferences"] = updates["custom_preferences"]
                # Clear persona if custom preferences set
                if updates["custom_preferences"]:
                    profile["persona"] = None

            # Add advanced preference fields
            for key in [
                "time_preferences",
                "route_preferences",
                "aircraft_preferences",
                "layover_preferences",
                "credit_preferences",
            ]:
                if key in updates:
                    profile[key] = updates[key]

            # Update timestamp
            profile["last_preferences_update"] = datetime.now().isoformat()

            save_profile(user_id, profile)
            return True

        except Exception as e:
            print(f"Error updating preferences: {e}")
            return False

    def learn_from_selections(
        self, user_id: str, selected_trips: List[Dict], rejected_trips: List[Dict]
    ) -> Dict[str, Any]:
        """Learn from user trip selections to improve recommendations"""
        patterns = {
            "preferred_departure_times": [],
            "preferred_destinations": [],
            "preferred_trip_lengths": [],
            "preferred_aircraft": [],
            "layover_preferences": {},
        }

        # Analyze selected trips
        for trip in selected_trips:
            if "departure_time" in trip:
                patterns["preferred_departure_times"].append(trip["departure_time"])
            if "destinations" in trip:
                patterns["preferred_destinations"].extend(trip["destinations"])
            if "duration_days" in trip:
                patterns["preferred_trip_lengths"].append(trip["duration_days"])
            if "aircraft" in trip:
                patterns["preferred_aircraft"].append(trip["aircraft"])

        # Store learned patterns
        profile = get_profile(user_id)
        profile["learned_patterns"] = patterns
        profile["learning_updated"] = datetime.now().isoformat()
        save_profile(user_id, profile)

        return patterns

    def get_smart_suggestions(self, user_id: str) -> List[Dict[str, Any]]:
        """Generate smart preference suggestions based on profile and industry data"""
        profile = get_profile(user_id)
        suggestions = []

        # Base suggestions on airline and position
        airline = profile.get("airline", "").lower()
        seat = profile.get("seat", "").lower()
        base = profile.get("base", "")

        # Airline-specific suggestions
        if "united" in airline:
            suggestions.extend(
                [
                    {
                        "type": "route_preference",
                        "title": "Consider International Routes",
                        "description": "United has extensive international network with good layovers",
                        "impact": "high",
                        "icon": "fas fa-globe",
                    },
                    {
                        "type": "aircraft_preference",
                        "title": "Wide-body Preferences",
                        "description": "United operates 777, 787, and A350 for international routes",
                        "impact": "medium",
                        "icon": "fas fa-plane",
                    },
                ]
            )

        # Position-specific suggestions
        if "captain" in seat:
            suggestions.append(
                {
                    "type": "scheduling",
                    "title": "Captain Scheduling Flexibility",
                    "description": "Higher seniority may allow weekend avoidance and better trips",
                    "impact": "high",
                    "icon": "fas fa-star",
                }
            )
        elif "first officer" in seat:
            suggestions.append(
                {
                    "type": "scheduling",
                    "title": "Build Time Efficiently",
                    "description": "Consider longer trips for faster upgrade progression",
                    "impact": "medium",
                    "icon": "fas fa-chart-line",
                }
            )

        # Base-specific suggestions
        if base:
            suggestions.append(
                {
                    "type": "commuting",
                    "title": f"Optimize for {base} Base",
                    "description": f"Consider commuting times and local traffic patterns for {base}",
                    "impact": "medium",
                    "icon": "fas fa-map-marker-alt",
                }
            )

        # Seasonal suggestions
        current_month = datetime.now().month
        if current_month in [11, 12, 1]:  # Holiday season
            suggestions.append(
                {
                    "type": "seasonal",
                    "title": "Holiday Season Preferences",
                    "description": "Consider holiday premium pay and family time balance",
                    "impact": "high",
                    "icon": "fas fa-calendar-alt",
                }
            )

        return suggestions

    def generate_preference_report(self, user_id: str) -> Dict[str, Any]:
        """Generate comprehensive preference analysis report"""
        profile = get_profile(user_id)
        preferences = self.get_user_preferences(user_id)

        report = {
            "user_profile": {
                "airline": profile.get("airline"),
                "base": profile.get("base"),
                "seat": profile.get("seat"),
                "seniority": profile.get("seniority"),
            },
            "current_preferences": {
                "persona": profile.get("persona"),
                "style": PILOT_PERSONAS.get(profile.get("persona") or "", {}).get(
                    "name", "Custom"
                ),
                "custom_notes": profile.get("custom_preferences"),
            },
            "optimization_score": self._calculate_optimization_score(profile),
            "suggestions": self.get_smart_suggestions(user_id),
            "learning_data": preferences.get("learned_patterns", {}),
            "last_updated": profile.get("last_preferences_update"),
            "completeness": self._calculate_completeness(profile),
        }

        return report

    def _get_learned_patterns(self, user_id: str) -> Dict[str, Any]:
        """Retrieve learned preference patterns"""
        profile = get_profile(user_id)
        return profile.get("learned_patterns", {})

    def _get_preference_history(self, user_id: str) -> List[Dict]:
        """Get history of preference changes"""
        profile = get_profile(user_id)
        return profile.get("preference_history", [])

    def _track_preference_change(self, user_id: str, changes: Dict[str, Any]):
        """Track preference changes for learning"""
        profile = get_profile(user_id)
        history = profile.get("preference_history", [])

        history.append(
            {
                "timestamp": datetime.now().isoformat(),
                "changes": changes,
                "source": "user_update",
            }
        )

        # Keep only last 50 changes
        if len(history) > 50:
            history = history[-50:]

        profile["preference_history"] = history
        save_profile(user_id, profile)

    def _get_optimization_suggestions(self, profile: Dict[str, Any]) -> List[str]:
        """Generate optimization suggestions based on profile completeness"""
        suggestions = []

        if not profile.get("persona") and not profile.get("custom_preferences"):
            suggestions.append(
                "Complete your preference profile for better PBS commands"
            )

        if not profile.get("seniority"):
            suggestions.append(
                "Add your seniority information for more accurate predictions"
            )

        if not profile.get("fleet"):
            suggestions.append("Specify your aircraft preferences for targeted trips")

        return suggestions

    def _calculate_optimization_score(self, profile: Dict[str, Any]) -> float:
        """Calculate how optimized the user's preferences are (0-100)"""
        score = 0
        max_score = 100

        # Basic profile completeness (40 points)
        if profile.get("airline"):
            score += 10
        if profile.get("base"):
            score += 10
        if profile.get("seat"):
            score += 10
        if profile.get("seniority"):
            score += 10

        # Preference completeness (40 points)
        if profile.get("persona") or profile.get("custom_preferences"):
            score += 20
        if profile.get("fleet"):
            score += 10
        if profile.get("learned_patterns"):
            score += 10

        # Activity and learning (20 points)
        if profile.get("preference_history"):
            score += 10
        if profile.get("last_preferences_update"):
            score += 10

        return min(score, max_score)

    def _calculate_completeness(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate profile completeness breakdown"""
        required_fields = ["airline", "base", "seat", "seniority"]
        preference_fields = ["persona", "custom_preferences"]

        required_complete = sum(1 for field in required_fields if profile.get(field))
        preference_complete = sum(
            1 for field in preference_fields if profile.get(field)
        )

        return {
            "required": f"{required_complete}/{len(required_fields)}",
            "preferences": f"{min(preference_complete, 1)}/1",
            "overall_percentage": int(
                (
                    (required_complete + min(preference_complete, 1))
                    / (len(required_fields) + 1)
                )
                * 100
            ),
        }


# Create global instance
preferences_manager = PreferencesManager()
