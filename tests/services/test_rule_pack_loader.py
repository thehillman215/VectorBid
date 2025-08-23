"""Unit tests for rule pack loader service."""

import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from app.rules_engine.models import HardRule, RulePack, SoftRule
from app.services.rule_pack_loader import RulePackLoader


class TestRulePackLoader:
    """Test cases for RulePackLoader."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.loader = RulePackLoader(rule_packs_dir=self.temp_dir)

    def teardown_method(self):
        """Clean up test fixtures."""
        # Clean up temporary directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_rule_pack_file(self, airline: str, month: str, rules: list) -> Path:
        """Create a test rule pack YAML file."""
        airline_dir = self.temp_dir / airline
        airline_dir.mkdir(exist_ok=True)
        
        rule_pack_file = airline_dir / f"{month}.yml"
        
        data = {
            'version': month,
            'airline': airline,
            'id': f"{airline}-{month}",
            'rules': rules
        }
        
        with open(rule_pack_file, 'w') as f:
            yaml.dump(data, f)
        
        return rule_pack_file

    def test_load_ual_rule_pack_success(self):
        """Test successful loading of UAL rule pack."""
        rules = [
            {
                'id': 'MIN_DAYS_OFF',
                'desc': 'Minimum 8 days off per month',
                'severity': 'hard',
                'evaluate': "context.get('days_off', 0) >= 8"
            },
            {
                'id': 'MAX_DUTY_HOURS',
                'desc': 'Maximum duty hours per trip',
                'severity': 'hard',
                'evaluate': "trip.get('duty_hours', 0) <= 12"
            }
        ]
        
        self.create_test_rule_pack_file('UAL', '2025.09', rules)
        
        pack = self.loader.load_rule_pack('UAL', '2025.09')
        
        assert isinstance(pack, RulePack)
        assert pack.airline == 'UAL'
        assert pack.contract_period == '2025.09'
        assert len(pack.hard_rules) == 2
        assert len(pack.soft_rules) == 0
        
        # Check specific rules
        rule_names = [rule.name for rule in pack.hard_rules]
        assert 'MIN_DAYS_OFF' in rule_names
        assert 'MAX_DUTY_HOURS' in rule_names

    def test_load_rule_pack_with_soft_rules(self):
        """Test loading rule pack with both hard and soft rules."""
        rules = [
            {
                'id': 'MIN_DAYS_OFF',
                'desc': 'Minimum 8 days off per month',
                'severity': 'hard',
                'evaluate': "context.get('days_off', 0) >= 8"
            },
            {
                'id': 'LAYOVER_PREFERENCE',
                'desc': 'Prefer longer layovers',
                'severity': 'soft',
                'weight': 1.5,
                'evaluate': "trip.get('layover_hours', 0)"
            }
        ]
        
        self.create_test_rule_pack_file('UAL', '2025.09', rules)
        
        pack = self.loader.load_rule_pack('UAL', '2025.09')
        
        assert len(pack.hard_rules) == 1
        assert len(pack.soft_rules) == 1
        
        soft_rule = pack.soft_rules[0]
        assert soft_rule.name == 'LAYOVER_PREFERENCE'
        assert soft_rule.weight == 1.5

    def test_load_rule_pack_not_found(self):
        """Test loading non-existent rule pack."""
        with pytest.raises(FileNotFoundError, match="Rule pack not found"):
            self.loader.load_rule_pack('FAKE', '2025.01')

    def test_load_rule_pack_invalid_yaml(self):
        """Test loading rule pack with invalid YAML."""
        airline_dir = self.temp_dir / 'UAL'
        airline_dir.mkdir()
        
        invalid_yaml_file = airline_dir / '2025.09.yml'
        with open(invalid_yaml_file, 'w') as f:
            f.write('invalid: yaml: content: [')
        
        with pytest.raises(yaml.YAMLError):
            self.loader.load_rule_pack('UAL', '2025.09')

    def test_load_rule_pack_invalid_structure(self):
        """Test loading rule pack with invalid data structure."""
        airline_dir = self.temp_dir / 'UAL'
        airline_dir.mkdir()
        
        invalid_structure_file = airline_dir / '2025.09.yml'
        with open(invalid_structure_file, 'w') as f:
            yaml.dump("not a dictionary", f)
        
        with pytest.raises(ValueError, match="Invalid YAML structure"):
            self.loader.load_rule_pack('UAL', '2025.09')

    def test_rule_pack_caching(self):
        """Test that rule packs are cached on subsequent loads."""
        rules = [
            {
                'id': 'MIN_DAYS_OFF',
                'desc': 'Minimum 8 days off per month',
                'severity': 'hard',
                'evaluate': "context.get('days_off', 0) >= 8"
            }
        ]
        
        self.create_test_rule_pack_file('UAL', '2025.09', rules)
        
        # Load first time
        pack1 = self.loader.load_rule_pack('UAL', '2025.09')
        
        # Load second time (should be cached)
        pack2 = self.loader.load_rule_pack('UAL', '2025.09')
        
        # Should be the same object (cached)
        assert pack1 is pack2

    def test_clear_cache(self):
        """Test clearing the rule pack cache."""
        rules = [
            {
                'id': 'MIN_DAYS_OFF',
                'desc': 'Minimum 8 days off per month',
                'severity': 'hard',
                'evaluate': "context.get('days_off', 0) >= 8"
            }
        ]
        
        self.create_test_rule_pack_file('UAL', '2025.09', rules)
        
        # Load and cache
        pack1 = self.loader.load_rule_pack('UAL', '2025.09')
        
        # Clear cache
        self.loader.clear_cache()
        
        # Load again (should not be cached)
        pack2 = self.loader.load_rule_pack('UAL', '2025.09')
        
        # Should be different objects
        assert pack1 is not pack2
        assert pack1.airline == pack2.airline  # But same content

    def test_list_available_rule_packs(self):
        """Test listing available rule packs."""
        # Create multiple rule packs
        self.create_test_rule_pack_file('UAL', '2025.09', [])
        self.create_test_rule_pack_file('UAL', '2025.10', [])
        self.create_test_rule_pack_file('DAL', '2025.09', [])
        
        available = self.loader.list_available_rule_packs()
        
        assert len(available) == 3
        
        # Check that all packs are listed
        pack_keys = [(pack['airline'], pack['month']) for pack in available]
        assert ('UAL', '2025.09') in pack_keys
        assert ('UAL', '2025.10') in pack_keys
        assert ('DAL', '2025.09') in pack_keys

    def test_list_available_rule_packs_empty_dir(self):
        """Test listing rule packs when directory is empty."""
        available = self.loader.list_available_rule_packs()
        assert available == []

    def test_convert_yaml_to_rulepack_effective_dates(self):
        """Test that effective dates are correctly calculated."""
        rules = [
            {
                'id': 'MIN_DAYS_OFF',
                'desc': 'Minimum 8 days off per month',
                'severity': 'hard',
                'evaluate': "context.get('days_off', 0) >= 8"
            }
        ]
        
        self.create_test_rule_pack_file('UAL', '2025.09', rules)
        
        pack = self.loader.load_rule_pack('UAL', '2025.09')
        
        assert pack.effective_start == date(2025, 9, 1)
        assert pack.effective_end == date(2025, 10, 1)

    def test_convert_yaml_to_rulepack_december(self):
        """Test effective dates for December (year rollover)."""
        rules = []
        self.create_test_rule_pack_file('UAL', '2025.12', rules)
        
        pack = self.loader.load_rule_pack('UAL', '2025.12')
        
        assert pack.effective_start == date(2025, 12, 1)
        assert pack.effective_end == date(2026, 1, 1)

    def test_convert_yaml_to_rulepack_invalid_month_format(self):
        """Test handling of invalid month format."""
        rules = []
        self.create_test_rule_pack_file('UAL', 'invalid-month', rules)
        
        # Should not raise exception, but use fallback dates
        pack = self.loader.load_rule_pack('UAL', 'invalid-month')
        
        assert pack.effective_start is not None
        assert isinstance(pack.effective_start, date)

    def test_rule_pack_backward_compatibility_properties(self):
        """Test backward compatibility properties."""
        rules = [
            {
                'id': 'MIN_DAYS_OFF',
                'desc': 'Minimum 8 days off per month',
                'severity': 'hard',
                'evaluate': "context.get('days_off', 0) >= 8"
            }
        ]
        
        self.create_test_rule_pack_file('UAL', '2025.09', rules)
        
        pack = self.loader.load_rule_pack('UAL', '2025.09')
        
        # Test backward compatibility properties
        assert pack.month == '2025.09'
        assert pack.schema_version == '2025.09'
        assert isinstance(pack.checksum, str)
        assert len(pack.checksum) == 6  # Should be 6-digit checksum

    def test_hard_rule_backward_compatibility(self):
        """Test HardRule backward compatibility properties."""
        rules = [
            {
                'id': 'MIN_DAYS_OFF',
                'desc': 'Minimum 8 days off per month',
                'severity': 'hard',
                'evaluate': "context.get('days_off', 0) >= 8"
            }
        ]
        
        self.create_test_rule_pack_file('UAL', '2025.09', rules)
        
        pack = self.loader.load_rule_pack('UAL', '2025.09')
        hard_rule = pack.hard_rules[0]
        
        # Test backward compatibility properties
        assert hard_rule.id == 'MIN_DAYS_OFF'
        assert hard_rule.predicate is not None
        assert callable(hard_rule.predicate)
