"""Rule pack loader service for loading and caching YAML rule packs."""

import logging
from datetime import date
from pathlib import Path
from typing import Optional

import yaml

from app.rules_engine.models import HardRule, RulePack, SoftRule

logger = logging.getLogger(__name__)


class RulePackLoader:
    """Load and cache rule packs from YAML files."""

    def __init__(self, rule_packs_dir: Optional[Path] = None):
        """Initialize the rule pack loader.
        
        Args:
            rule_packs_dir: Directory containing rule pack YAML files.
                          Defaults to project root/rule_packs
        """
        if rule_packs_dir is None:
            # Default to rule_packs directory in project root
            self.rule_packs_dir = Path(__file__).parent.parent.parent / "rule_packs"
        else:
            self.rule_packs_dir = rule_packs_dir
        
        self._cache: dict[str, RulePack] = {}

    def load_rule_pack(self, airline: str, month: str) -> RulePack:
        """Load rule pack for airline and month.
        
        Args:
            airline: Airline code (e.g., 'UAL')
            month: Month in format YYYY.MM (e.g., '2025.09')
            
        Returns:
            Loaded and converted RulePack object
            
        Raises:
            FileNotFoundError: If rule pack file doesn't exist
            yaml.YAMLError: If YAML parsing fails
            ValueError: If YAML structure is invalid
        """
        cache_key = f"{airline}/{month}"
        if cache_key in self._cache:
            logger.debug(f"Returning cached rule pack for {cache_key}")
            return self._cache[cache_key]

        yaml_path = self.rule_packs_dir / airline / f"{month}.yml"
        if not yaml_path.exists():
            raise FileNotFoundError(f"Rule pack not found: {yaml_path}")

        logger.info(f"Loading rule pack from {yaml_path}")
        
        try:
            with open(yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Failed to parse YAML file {yaml_path}: {e}") from e

        if not isinstance(data, dict):
            raise ValueError(f"Invalid YAML structure in {yaml_path}: expected dict, got {type(data)}")

        # Convert YAML format to RulePack model
        rule_pack = self._convert_yaml_to_rulepack(data, airline, month)
        self._cache[cache_key] = rule_pack
        
        logger.info(f"Successfully loaded rule pack {cache_key} with {len(rule_pack.hard_rules)} hard rules")
        return rule_pack

    def _convert_yaml_to_rulepack(self, yaml_data: dict, airline: str, month: str) -> RulePack:
        """Convert YAML rule pack to Pydantic model.
        
        Args:
            yaml_data: Parsed YAML data
            airline: Airline code for the rule pack
            month: Month for the rule pack
            
        Returns:
            Converted RulePack object
        """
        # Extract basic metadata
        version = yaml_data.get('version', month)
        rules_list = yaml_data.get('rules', [])
        
        hard_rules = []
        soft_rules = []
        
        # Process rules based on severity
        for rule_data in rules_list:
            rule_id = rule_data.get('id', '')
            description = rule_data.get('desc', '')
            severity = rule_data.get('severity', 'hard')
            evaluate = rule_data.get('evaluate', 'True')
            
            if severity == 'hard':
                hard_rule = HardRule(
                    name=rule_id,
                    description=description,
                    check=evaluate,
                    severity="error"
                )
                hard_rules.append(hard_rule)
            elif severity == 'soft':
                # For soft rules, we need a weight (default to 1.0 if not specified)
                weight = rule_data.get('weight', 1.0)
                soft_rule = SoftRule(
                    name=rule_id,
                    description=description,
                    weight=weight,
                    score=evaluate  # Use evaluate expression as score expression
                )
                soft_rules.append(soft_rule)
        
        # Parse month to determine effective dates
        try:
            # Convert month format from "2025.09" to date
            year, month_num = month.split('.')
            effective_start = date(int(year), int(month_num), 1)
            # End date is the last day of the month
            if int(month_num) == 12:
                effective_end = date(int(year) + 1, 1, 1)
            else:
                effective_end = date(int(year), int(month_num) + 1, 1)
        except (ValueError, IndexError):
            # Fallback if month format is unexpected
            effective_start = date.today().replace(day=1)
            effective_end = None
        
        return RulePack(
            version=version,
            airline=airline,
            contract_period=month,
            effective_start=effective_start,
            effective_end=effective_end,
            hard_rules=hard_rules,
            soft_rules=soft_rules,
            derived_rules=[],  # Not used in current YAML format
            metadata={
                'source_file': str(self.rule_packs_dir / airline / f"{month}.yml"),
                'loaded_at': date.today().isoformat()
            }
        )

    def list_available_rule_packs(self) -> list[dict[str, str]]:
        """List all available rule packs.
        
        Returns:
            List of dictionaries with 'airline' and 'month' keys
        """
        available = []
        
        if not self.rule_packs_dir.exists():
            return available
        
        for airline_dir in self.rule_packs_dir.iterdir():
            if not airline_dir.is_dir():
                continue
                
            airline = airline_dir.name
            for rule_file in airline_dir.glob("*.yml"):
                month = rule_file.stem  # Remove .yml extension
                available.append({
                    'airline': airline,
                    'month': month,
                    'path': str(rule_file)
                })
        
        return sorted(available, key=lambda x: (x['airline'], x['month']))

    def clear_cache(self) -> None:
        """Clear the rule pack cache."""
        self._cache.clear()
        logger.info("Rule pack cache cleared")


# Global instance for use throughout the application
rule_pack_loader = RulePackLoader()
