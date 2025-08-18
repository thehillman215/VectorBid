# enhanced_bid_layers_system.py
"""
Enhanced 50-Layer Bidding System for VectorBid
Integrates comprehensive PBS command generation with layered strategy management
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime

# Import our enhanced PBS generator
from enhanced_pbs_generator import (
    EnhancedPBSGenerator,
    PBSCommand,
    CommandType,
    Priority,
)


@dataclass
class BidLayer:
    """Represents a single bid layer with multiple filters"""

    layer_number: int
    name: str
    description: str
    priority: Priority
    commands: List[PBSCommand] = field(default_factory=list)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def add_command(self, command: PBSCommand):
        """Add a PBS command to this layer"""
        command.layer_number = self.layer_number
        self.commands.append(command)

    def get_pbs_output(self) -> List[str]:
        """Get PBS command strings for this layer"""
        return [cmd.to_pbs_string() for cmd in self.commands if self.is_active]

    def to_dict(self) -> Dict[str, Any]:
        """Convert layer to dictionary for storage/API"""
        return {
            "layer_number": self.layer_number,
            "name": self.name,
            "description": self.description,
            "priority": self.priority.name,
            "is_active": self.is_active,
            "commands": [
                {
                    "command_type": cmd.command_type.value,
                    "subject": cmd.subject,
                    "condition": cmd.condition,
                    "value": cmd.value,
                    "explanation": cmd.explanation,
                }
                for cmd in self.commands
            ],
            "created_at": self.created_at.isoformat(),
        }


class Enhanced50LayerSystem:
    """
    Complete 50-layer bidding system that manages strategic bid construction
    """

    def __init__(self, user_id: str = None):
        self.user_id = user_id
        self.layers: List[BidLayer] = []
        self.max_layers = 50
        self.pbs_generator = EnhancedPBSGenerator()
        self.pilot_profile = {}

        # Pre-defined layer templates for common strategies
        self.layer_templates = {
            "critical_constraints": {
                "name": "Critical Constraints",
                "description": "Must-have requirements that cannot be compromised",
                "priority": Priority.CRITICAL,
                "examples": [
                    "AVOID RESERVE",
                    "OFF specific dates",
                    "Base requirements",
                ],
            },
            "weekend_strategy": {
                "name": "Weekend Strategy",
                "description": "Weekend work preferences",
                "priority": Priority.HIGH,
                "examples": ["Weekend avoidance", "Weekend preferences"],
            },
            "timing_preferences": {
                "name": "Timing Preferences",
                "description": "Departure times, red-eye avoidance, commuter needs",
                "priority": Priority.HIGH,
                "examples": ["No early starts", "Commuter timing", "Red-eye avoidance"],
            },
            "trip_characteristics": {
                "name": "Trip Characteristics",
                "description": "Duration, destinations, aircraft preferences",
                "priority": Priority.MEDIUM,
                "examples": ["Short trips", "International routes", "Aircraft types"],
            },
            "quality_of_life": {
                "name": "Quality of Life",
                "description": "Work-life balance optimizations",
                "priority": Priority.MEDIUM,
                "examples": [
                    "Max days off",
                    "Layover preferences",
                    "Credit optimization",
                ],
            },
            "tie_breakers": {
                "name": "Tie Breakers",
                "description": "Final preferences for close decisions",
                "priority": Priority.LOW,
                "examples": [
                    "Specific destinations",
                    "Crew preferences",
                    "Equipment comfort",
                ],
            },
        }

    def set_pilot_profile(self, profile: Dict[str, Any]):
        """Set pilot profile for personalized layer generation"""
        self.pilot_profile = profile
        self.pbs_generator.set_pilot_profile(profile)

    def generate_layers_from_preferences(self, preferences: str) -> int:
        """
        Generate bid layers from natural language preferences
        Returns number of layers created
        """
        # Clear existing layers
        self.layers = []

        # Generate PBS commands from preferences
        commands = self.pbs_generator.parse_natural_language(preferences)

        if not commands:
            # Generate default strategy if no preferences
            commands = self._generate_default_strategy()

        # Group commands by layer number and create layers
        layers_by_number = {}
        for cmd in commands:
            if cmd.layer_number not in layers_by_number:
                layers_by_number[cmd.layer_number] = []
            layers_by_number[cmd.layer_number].append(cmd)

        # Create BidLayer objects
        for layer_num in sorted(layers_by_number.keys()):
            layer_commands = layers_by_number[layer_num]

            # Determine layer name based on command types and priority
            layer_name = self._determine_layer_name(layer_commands)
            layer_description = self._generate_layer_description(layer_commands)

            layer = BidLayer(
                layer_number=layer_num,
                name=layer_name,
                description=layer_description,
                priority=layer_commands[0].priority,  # Use first command's priority
                commands=layer_commands,
            )

            self.layers.append(layer)

        return len(self.layers)

    def add_custom_layer(
        self,
        name: str,
        description: str,
        priority: Priority,
        commands: List[Dict[str, str]],
    ) -> bool:
        """
        Add a custom layer with user-defined commands
        """
        if len(self.layers) >= self.max_layers:
            return False

        layer_number = len(self.layers) + 1
        layer = BidLayer(
            layer_number=layer_number,
            name=name,
            description=description,
            priority=priority,
        )

        # Convert command dictionaries to PBSCommand objects
        for cmd_dict in commands:
            try:
                command = PBSCommand(
                    command_type=CommandType(cmd_dict["command_type"]),
                    subject=cmd_dict["subject"],
                    condition=cmd_dict["condition"],
                    value=cmd_dict["value"],
                    priority=priority,
                    explanation=cmd_dict.get("explanation", ""),
                    layer_number=layer_number,
                )
                layer.add_command(command)
            except (KeyError, ValueError) as e:
                continue  # Skip invalid commands

        if layer.commands:  # Only add if it has valid commands
            self.layers.append(layer)
            return True

        return False

    def modify_layer(self, layer_number: int, **kwargs) -> bool:
        """Modify an existing layer"""
        layer = self.get_layer(layer_number)
        if not layer:
            return False

        if "name" in kwargs:
            layer.name = kwargs["name"]
        if "description" in kwargs:
            layer.description = kwargs["description"]
        if "is_active" in kwargs:
            layer.is_active = kwargs["is_active"]
        if "priority" in kwargs:
            layer.priority = kwargs["priority"]
            # Update all commands in the layer
            for cmd in layer.commands:
                cmd.priority = kwargs["priority"]

        return True

    def delete_layer(self, layer_number: int) -> bool:
        """Delete a layer and renumber subsequent layers"""
        layer_index = next(
            (
                i
                for i, layer in enumerate(self.layers)
                if layer.layer_number == layer_number
            ),
            None,
        )

        if layer_index is None:
            return False

        # Remove the layer
        self.layers.pop(layer_index)

        # Renumber subsequent layers
        for i in range(layer_index, len(self.layers)):
            self.layers[i].layer_number = i + 1
            for cmd in self.layers[i].commands:
                cmd.layer_number = i + 1

        return True

    def reorder_layers(self, new_order: List[int]) -> bool:
        """Reorder layers based on new priority order"""
        if len(new_order) != len(self.layers):
            return False

        try:
            # Create new order
            reordered_layers = []
            for new_position, old_layer_number in enumerate(new_order, 1):
                old_layer = self.get_layer(old_layer_number)
                if old_layer:
                    old_layer.layer_number = new_position
                    for cmd in old_layer.commands:
                        cmd.layer_number = new_position
                    reordered_layers.append(old_layer)

            self.layers = reordered_layers
            return True
        except:
            return False

    def get_layer(self, layer_number: int) -> Optional[BidLayer]:
        """Get a specific layer by number"""
        return next(
            (layer for layer in self.layers if layer.layer_number == layer_number), None
        )

    def get_active_layers(self) -> List[BidLayer]:
        """Get only active layers"""
        return [layer for layer in self.layers if layer.is_active]

    def generate_final_pbs_output(self, include_explanations: bool = False) -> str:
        """Generate final PBS output for copy-paste into airline system"""
        active_layers = self.get_active_layers()

        if not active_layers:
            return "No active layers found. Please create bid layers first."

        output_lines = [
            f"VectorBid 50-Layer PBS Strategy",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Active Layers: {len(active_layers)} of {len(self.layers)}",
            "=" * 50,
            "",
        ]

        for layer in active_layers:
            # Layer header
            output_lines.append(f"LAYER {layer.layer_number:2d}: {layer.name}")
            if include_explanations:
                output_lines.append(f"# {layer.description}")

            # PBS commands for this layer
            for cmd in layer.commands:
                output_lines.append(f"  {cmd.to_pbs_string()}")
                if include_explanations:
                    output_lines.append(f"    # {cmd.explanation}")

            output_lines.append("")  # Blank line between layers

        # Add summary and instructions
        output_lines.extend(
            [
                "=" * 50,
                "SUMMARY:",
                f"Total Commands: {sum(len(layer.commands) for layer in active_layers)}",
                f"Priority Breakdown:",
            ]
        )

        # Count commands by priority
        priority_counts = {}
        for layer in active_layers:
            for cmd in layer.commands:
                priority_counts[cmd.priority.name] = (
                    priority_counts.get(cmd.priority.name, 0) + 1
                )

        for priority, count in priority_counts.items():
            output_lines.append(f"  {priority}: {count} commands")

        output_lines.extend(
            [
                "",
                "USAGE INSTRUCTIONS:",
                "1. Copy the commands above (Layer by Layer)",
                "2. Log into your airline's PBS system",
                "3. Enter commands in layer order (1, 2, 3...)",
                "4. Review and adjust based on current bid packets",
                "5. Submit your bid before deadline",
                "",
                "⚠️  IMPORTANT: Always review commands against actual",
                "   trip data before submitting your bid!",
            ]
        )

        return "\n".join(output_lines)

    def export_strategy(self) -> Dict[str, Any]:
        """Export complete strategy for saving/sharing"""
        return {
            "user_id": self.user_id,
            "created_at": datetime.now().isoformat(),
            "pilot_profile": self.pilot_profile,
            "total_layers": len(self.layers),
            "active_layers": len(self.get_active_layers()),
            "layers": [layer.to_dict() for layer in self.layers],
        }

    def import_strategy(self, strategy_data: Dict[str, Any]) -> bool:
        """Import a saved strategy"""
        try:
            self.layers = []

            for layer_data in strategy_data.get("layers", []):
                # Recreate commands
                commands = []
                for cmd_data in layer_data.get("commands", []):
                    command = PBSCommand(
                        command_type=CommandType(cmd_data["command_type"]),
                        subject=cmd_data["subject"],
                        condition=cmd_data["condition"],
                        value=cmd_data["value"],
                        priority=Priority[layer_data["priority"]],
                        explanation=cmd_data["explanation"],
                        layer_number=layer_data["layer_number"],
                    )
                    commands.append(command)

                # Recreate layer
                layer = BidLayer(
                    layer_number=layer_data["layer_number"],
                    name=layer_data["name"],
                    description=layer_data["description"],
                    priority=Priority[layer_data["priority"]],
                    commands=commands,
                    is_active=layer_data["is_active"],
                )

                self.layers.append(layer)

            return True
        except (KeyError, ValueError):
            return False

    def get_layer_statistics(self) -> Dict[str, Any]:
        """Get statistics about the current layer configuration"""
        active_layers = self.get_active_layers()

        # Command type breakdown
        command_types = {}
        priorities = {}

        for layer in active_layers:
            for cmd in layer.commands:
                cmd_type = cmd.command_type.value
                priority = cmd.priority.name

                command_types[cmd_type] = command_types.get(cmd_type, 0) + 1
                priorities[priority] = priorities.get(priority, 0) + 1

        return {
            "total_layers": len(self.layers),
            "active_layers": len(active_layers),
            "total_commands": sum(len(layer.commands) for layer in active_layers),
            "command_types": command_types,
            "priority_distribution": priorities,
            "layers_by_priority": {
                priority.name: len([l for l in active_layers if l.priority == priority])
                for priority in Priority
            },
        }

    def validate_strategy(self) -> List[str]:
        """Validate the current strategy for potential issues"""
        issues = []

        # Check for empty strategy
        if not self.layers:
            issues.append("No layers defined")
            return issues

        active_layers = self.get_active_layers()
        if not active_layers:
            issues.append("No active layers")
            return issues

        # Check for conflicting commands
        avoid_commands = []
        prefer_commands = []

        for layer in active_layers:
            for cmd in layer.commands:
                if cmd.command_type == CommandType.AVOID:
                    avoid_commands.append(cmd)
                elif cmd.command_type == CommandType.PREFER:
                    prefer_commands.append(cmd)

        # Check for direct conflicts (avoiding and preferring the same thing)
        for avoid_cmd in avoid_commands:
            for prefer_cmd in prefer_commands:
                if (
                    avoid_cmd.subject == prefer_cmd.subject
                    and avoid_cmd.condition == prefer_cmd.condition
                    and avoid_cmd.value == prefer_cmd.value
                ):
                    issues.append(
                        f"Conflict: Layer {avoid_cmd.layer_number} avoids "
                        f"what Layer {prefer_cmd.layer_number} prefers"
                    )

        # Check for too many critical constraints
        critical_layers = [l for l in active_layers if l.priority == Priority.CRITICAL]
        if len(critical_layers) > 5:
            issues.append(
                f"Too many critical constraints ({len(critical_layers)}). "
                "Consider reducing to 3-5 most important."
            )

        # Check layer distribution
        if len(active_layers) < 5:
            issues.append("Very few layers - consider adding more preferences")
        elif len(active_layers) > 40:
            issues.append("Many layers - consider consolidating similar preferences")

        return issues

    def _determine_layer_name(self, commands: List[PBSCommand]) -> str:
        """Determine appropriate name for a layer based on its commands"""
        if not commands:
            return "Empty Layer"

        # Check command types and subjects to categorize
        subjects = set(cmd.subject for cmd in commands)
        command_types = set(cmd.command_type for cmd in commands)

        if "RESERVE" in " ".join(cmd.value for cmd in commands):
            return "Reserve Preferences"
        elif any("WEEKEND" in cmd.value for cmd in commands):
            return "Weekend Strategy"
        elif any("TIME" in cmd.condition for cmd in commands):
            return "Timing Preferences"
        elif any("DESTINATION" in cmd.condition for cmd in commands):
            return "Route Preferences"
        elif any("AIRCRAFT" in cmd.condition for cmd in commands):
            return "Equipment Preferences"
        elif any("DUTY_DAYS" in cmd.condition for cmd in commands):
            return "Trip Length"
        elif any("LAYOVER" in cmd.condition for cmd in commands):
            return "Layover Strategy"
        elif commands[0].priority == Priority.CRITICAL:
            return "Critical Constraints"
        elif CommandType.AVOID in command_types:
            return "Avoidance Rules"
        elif CommandType.PREFER in command_types:
            return "Preferences"
        else:
            return f"Layer {commands[0].layer_number}"

    def _generate_layer_description(self, commands: List[PBSCommand]) -> str:
        """Generate description for a layer based on its commands"""
        if not commands:
            return "No commands defined"

        # Use the first command's explanation as base, or generate from commands
        if commands[0].explanation:
            return commands[0].explanation

        # Generate description based on command patterns
        cmd_summaries = []
        for cmd in commands[:3]:  # Max 3 for brevity
            cmd_summaries.append(f"{cmd.command_type.value} {cmd.subject}")

        return f"Contains {len(commands)} command(s): " + ", ".join(cmd_summaries)

    def _generate_default_strategy(self) -> List[PBSCommand]:
        """Generate a default strategy when no preferences are provided"""
        return self.pbs_generator._generate_default_commands()


# Integration with existing VectorBid routes
def integrate_with_vectorbid():
    """
    Example of how to integrate this with existing VectorBid routes
    """

    # This would replace the simple natural_language_to_pbs_filters function

    def enhanced_preference_processing(
        preferences: str, user_id: str = None, pilot_profile: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Enhanced replacement for natural_language_to_pbs_filters
        Returns comprehensive PBS strategy instead of simple command list
        """

        # Create 50-layer system
        bid_system = Enhanced50LayerSystem(user_id=user_id)

        # Set pilot profile if available
        if pilot_profile:
            bid_system.set_pilot_profile(pilot_profile)

        # Generate layers from preferences
        num_layers = bid_system.generate_layers_from_preferences(preferences)

        # Generate outputs
        pbs_output = bid_system.generate_final_pbs_output(include_explanations=True)
        simple_commands = []

        # Extract simple commands for backward compatibility
        for layer in bid_system.get_active_layers():
            for cmd in layer.commands:
                simple_commands.append(cmd.to_pbs_string())

        # Get strategy statistics
        stats = bid_system.get_layer_statistics()

        # Validate strategy
        issues = bid_system.validate_strategy()

        return {
            "layers": num_layers,
            "commands": simple_commands,  # For backward compatibility
            "pbs_output": pbs_output,
            "strategy_data": bid_system.export_strategy(),
            "statistics": stats,
            "validation_issues": issues,
            "bid_system": bid_system,  # For further manipulation
        }

    return enhanced_preference_processing


# Usage Example
if __name__ == "__main__":
    # Example usage of the enhanced 50-layer system
    system = Enhanced50LayerSystem(user_id="pilot_123")

    # Set pilot profile
    profile = {
        "airline": "United",
        "base": "IAH",
        "fleet": ["737", "757"],
        "seniority": 1234,
        "is_commuter": True,
        "home_airport": "DEN",
    }
    system.set_pilot_profile(profile)

    # Generate strategy from preferences
    preferences = """
    I'm a commuter living in Denver. I need weekends off and no early departures.
    I prefer short trips, hate red-eyes, and need to be home for my anniversary on the 15th.
    I want to avoid reserve duty and maximize my days off.
    International routes are okay but I prefer domestic.
    """

    num_layers = system.generate_layers_from_preferences(preferences)

    print(f"Generated {num_layers} layers")
    print("\nStrategy Statistics:")
    stats = system.get_layer_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\nValidation Issues:")
    issues = system.validate_strategy()
    for issue in issues:
        print(f"  - {issue}")

    print("\nFinal PBS Output:")
    print(system.generate_final_pbs_output(include_explanations=False))
