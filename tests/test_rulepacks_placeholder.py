"""
Test rule pack loading functionality.

This test ensures that rule pack YAML files can be loaded and contain
required metadata like version strings.
"""

import yaml
from pathlib import Path
from typing import Dict, Any

import pytest


def load_rule_pack(file_path: Path) -> Dict[str, Any]:
    """Load a rule pack YAML file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def test_rule_pack_loading():
    """Test that rule packs can be loaded from YAML files."""
    rule_packs_dir = Path("rule_packs")
    
    # Check if rule packs directory exists
    assert rule_packs_dir.exists(), "Rule packs directory should exist"
    
    # Find all YAML files in rule packs
    yaml_files = list(rule_packs_dir.rglob("*.yml")) + list(rule_packs_dir.rglob("*.yaml"))
    
    if not yaml_files:
        pytest.skip("No rule pack YAML files found")
    
    # Test each rule pack file
    for yaml_file in yaml_files:
        print(f"Testing rule pack: {yaml_file}")
        
        # Test that file can be loaded
        try:
            rule_pack = load_rule_pack(yaml_file)
            assert isinstance(rule_pack, dict), f"Rule pack should be a dict, got {type(rule_pack)}"
        except Exception as e:
            pytest.fail(f"Failed to load rule pack {yaml_file}: {e}")
        
        # Test required fields
        assert "version" in rule_pack, f"Rule pack {yaml_file} missing 'version' field"
        assert "airline" in rule_pack, f"Rule pack {yaml_file} missing 'airline' field"
        
        # Test version format (should be a string)
        version = rule_pack["version"]
        assert isinstance(version, str), f"Version should be string, got {type(version)}"
        assert len(version) > 0, "Version should not be empty"
        
        # Test airline format (should be a string)
        airline = rule_pack["airline"]
        assert isinstance(airline, str), f"Airline should be string, got {type(airline)}"
        assert len(airline) > 0, "Airline should not be empty"
        
        # Test optional fields if present
        if "far117" in rule_pack:
            far117 = rule_pack["far117"]
            assert isinstance(far117, dict), "FAR117 section should be a dict"
            
            if "min_rest_hours" in far117:
                min_rest = far117["min_rest_hours"]
                assert isinstance(min_rest, (int, float)), "min_rest_hours should be numeric"
                assert min_rest > 0, "min_rest_hours should be positive"
        
        if "union" in rule_pack:
            union = rule_pack["union"]
            assert isinstance(union, dict), "Union section should be a dict"
            
            if "max_duty_hours_per_day" in union:
                max_duty = union["max_duty_hours_per_day"]
                assert isinstance(max_duty, (int, float)), "max_duty_hours_per_day should be numeric"
                assert max_duty > 0, "max_duty_hours_per_day should be positive"


def test_specific_ual_rule_pack():
    """Test the specific UAL rule pack structure."""
    ual_rule_pack_path = Path("rule_packs/UAL/2025.08.yml")
    
    if not ual_rule_pack_path.exists():
        pytest.skip("UAL rule pack not found")
    
    # Load the rule pack
    rule_pack = load_rule_pack(ual_rule_pack_path)
    
    # Test specific UAL structure
    assert rule_pack["version"] == "2025.08"
    assert rule_pack["airline"] == "UAL"
    assert rule_pack["id"] == "UAL-2025-08"
    
    # Test FAR117 section
    far117 = rule_pack["far117"]
    assert far117["min_rest_hours"] == 10
    
    # Test hard constraints
    hard_constraints = far117.get("hard", [])
    assert isinstance(hard_constraints, list)
    
    # Test soft constraints
    soft_constraints = far117.get("soft", [])
    assert isinstance(soft_constraints, list)
    
    # Test union section
    union = rule_pack["union"]
    assert union["max_duty_hours_per_day"] == 16


def test_rule_pack_schema_validation():
    """Test that rule packs follow expected schema structure."""
    rule_packs_dir = Path("rule_packs")
    
    if not rule_packs_dir.exists():
        pytest.skip("Rule packs directory not found")
    
    yaml_files = list(rule_packs_dir.rglob("*.yml")) + list(rule_packs_dir.rglob("*.yaml"))
    
    if not yaml_files:
        pytest.skip("No rule pack YAML files found")
    
    for yaml_file in yaml_files:
        rule_pack = load_rule_pack(yaml_file)
        
        # Test top-level structure
        required_fields = ["version", "airline", "id"]
        for field in required_fields:
            assert field in rule_pack, f"Required field '{field}' missing from {yaml_file}"
        
        # Test optional sections have correct types
        optional_sections = ["far117", "union", "rules"]
        for section in optional_sections:
            if section in rule_pack:
                section_data = rule_pack[section]
                if section in ["far117", "union"]:
                    assert isinstance(section_data, dict), f"Section '{section}' should be dict"
                elif section == "rules":
                    assert isinstance(section_data, list), f"Section '{section}' should be list"


def test_rule_pack_yaml_syntax():
    """Test that all rule pack YAML files have valid syntax."""
    rule_packs_dir = Path("rule_packs")
    
    if not rule_packs_dir.exists():
        pytest.skip("Rule packs directory not found")
    
    yaml_files = list(rule_packs_dir.rglob("*.yml")) + list(rule_packs_dir.rglob("*.yaml"))
    
    if not yaml_files:
        pytest.skip("No rule pack YAML files found")
    
    for yaml_file in yaml_files:
        # Test that file can be parsed as YAML
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                yaml.safe_load(f)
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML syntax in {yaml_file}: {e}")
        except Exception as e:
            pytest.fail(f"Unexpected error reading {yaml_file}: {e}")


if __name__ == "__main__":
    # Run tests directly if script is executed
    pytest.main([__file__, "-v"])

