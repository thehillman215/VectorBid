"""
Test rule pack loading and compilation.

This test verifies that the rules engine can load and compile
actual rule pack YAML files.
"""

import pytest
import yaml
from datetime import date
from pathlib import Path

from app.rules_engine import compile_rule_pack, RulePackValidator


class TestRulePackLoading:
    """Test loading and compiling actual rule pack files."""
    
    def test_load_test_rule_pack(self):
        """Should be able to load and compile the test rule pack."""
        rule_pack_path = Path("rule_packs/TEST/2025.08.yml")
        
        # Check if test rule pack exists
        if not rule_pack_path.exists():
            pytest.skip("Test rule pack not found")
        
        # Load YAML
        with open(rule_pack_path, 'r', encoding='utf-8') as f:
            yaml_data = yaml.safe_load(f)
        
        # Compile rule pack
        rule_pack = compile_rule_pack(yaml_data)
        
        # Verify basic structure
        assert rule_pack.airline == "TEST"
        assert rule_pack.month == "2025.08"
        assert rule_pack.base == "TEST"
        assert rule_pack.fleet == "TEST"
        assert rule_pack.schema_version == "v1"
        assert rule_pack.checksum == "test-checksum-123"
        
        # Verify rules were compiled
        assert len(rule_pack.hard_rules) == 3
        assert len(rule_pack.soft_rules) == 2
        assert len(rule_pack.derived_rules) == 2
        
        # Check hard rule details
        hard_rule_ids = [r.id for r in rule_pack.hard_rules]
        assert "MIN_REST_HOURS" in hard_rule_ids
        assert "MAX_DUTY_HOURS" in hard_rule_ids
        assert "NO_REDEYE_IF_FLAGGED" in hard_rule_ids
        
        # Check soft rule details
        soft_rule_ids = [r.id for r in rule_pack.soft_rules]
        assert "PREF_SHORT_TRIPS" in soft_rule_ids
        assert "PREF_WEEKEND_OFF" in soft_rule_ids
        
        # Check derived rule details
        derived_rule_ids = [r.id for r in rule_pack.derived_rules]
        assert "MAX_DUTY_BY_LEGS" in derived_rule_ids
        assert "REST_REQUIREMENT" in derived_rule_ids
    
    def test_rule_pack_validation_works(self):
        """Should be able to create a validator from the compiled rule pack."""
        rule_pack_path = Path("rule_packs/TEST/2025.08.yml")
        
        if not rule_pack_path.exists():
            pytest.skip("Test rule pack not found")
        
        # Load and compile
        with open(rule_pack_path, 'r', encoding='utf-8') as f:
            yaml_data = yaml.safe_load(f)
        
        rule_pack = compile_rule_pack(yaml_data)
        
        # Create validator
        context = {"ctx_id": "test123", "pilot_id": "pilot456"}
        validator = RulePackValidator(rule_pack, context)
        
        # Test validation (should work even with placeholder predicates)
        violations = validator.validate_inputs({"test": "data"})
        
        # For now, all rules return True (placeholder), so no violations
        # This will change when we implement actual DSL parsing
        assert isinstance(violations, list)
    
    def test_rule_pack_health_integration(self):
        """Should be able to get health status for the loaded rule pack."""
        rule_pack_path = Path("rule_packs/TEST/2025.08.yml")
        
        if not rule_pack_path.exists():
            pytest.skip("Test rule pack not found")
        
        # Load and compile
        with open(rule_pack_path, 'r', encoding='utf-8') as f:
            yaml_data = yaml.safe_load(f)
        
        rule_pack = compile_rule_pack(yaml_data)
        
        # Test health functions
        from app.rules_engine import pack_status, pack_registry_health
        
        # Single pack status
        status = pack_status(rule_pack)
        assert status["airline"] == "TEST"
        assert status["month"] == "2025.08"
        assert status["hard_rules"] == 3
        assert status["soft_rules"] == 2
        assert status["derived_rules"] == 2
        
        # Registry health
        registry_health = pack_registry_health([rule_pack])
        assert registry_health["status"] == "ok"
        assert registry_health["count"] == 1
        assert "TEST" in registry_health["airlines"]
        assert registry_health["airlines"]["TEST"] == ["2025.08"]


# Test markers for pytest
pytestmark = [
    pytest.mark.rules_engine,
    pytest.mark.integration
]

