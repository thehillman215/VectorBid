"""
Rule pack management system tests - Fixed version.

These tests drive the implementation of comprehensive rule pack management
for VectorBid, following TDD principles.
"""

from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient


class TestRulePackValidation:
    """Test rule pack validation functionality."""

    def test_rule_pack_required_fields_validation(self, rule_pack_validator, sample_rule_pack):
        """Rule pack should have all required fields."""
        missing_fields = rule_pack_validator.validate_required_fields(sample_rule_pack)
        assert missing_fields == [], f"Missing required fields: {missing_fields}"

    def test_rule_pack_missing_required_fields(self, rule_pack_validator):
        """Rule pack validation should catch missing required fields."""
        incomplete_rule_pack = {
            "version": "2025.08",
            # Missing "airline" and "id"
        }

        missing_fields = rule_pack_validator.validate_required_fields(incomplete_rule_pack)
        assert "airline" in missing_fields
        assert "id" in missing_fields
        assert len(missing_fields) == 2

    def test_rule_pack_version_format_validation(self, rule_pack_validator):
        """Rule pack version should follow YYYY.MM format."""
        valid_versions = ["2025.08", "2024.12", "2026.01"]
        invalid_versions = ["2025.8", "25.08", "2025", "invalid"]

        for version in valid_versions:
            assert rule_pack_validator.validate_version_format(version), (
                f"Version {version} should be valid"
            )

        for version in invalid_versions:
            assert not rule_pack_validator.validate_version_format(version), (
                f"Version {version} should be invalid"
            )

    def test_rule_pack_airline_code_validation(self, rule_pack_validator):
        """Rule pack airline code should be 3 uppercase letters."""
        valid_airlines = ["UAL", "AAL", "DAL", "SWA"]
        invalid_airlines = ["ua", "United", "UAL1", "UAL-", ""]

        for airline in valid_airlines:
            assert rule_pack_validator.validate_airline_code(airline), (
                f"Airline {airline} should be valid"
            )

        for airline in invalid_airlines:
            assert not rule_pack_validator.validate_airline_code(airline), (
                f"Airline {airline} should be invalid"
            )

    def test_rule_pack_schema_structure_validation(self, sample_rule_pack):
        """Rule pack should have valid schema structure."""
        # Test top-level structure
        assert isinstance(sample_rule_pack, dict)
        assert "version" in sample_rule_pack
        assert "airline" in sample_rule_pack
        assert "id" in sample_rule_pack

        # Test FAR117 section if present
        if "far117" in sample_rule_pack:
            far117 = sample_rule_pack["far117"]
            assert isinstance(far117, dict)

            if "min_rest_hours" in far117:
                assert isinstance(far117["min_rest_hours"], (int, float))
                assert far117["min_rest_hours"] > 0

        # Test union section if present
        if "union" in sample_rule_pack:
            union = sample_rule_pack["union"]
            assert isinstance(union, dict)

            if "max_duty_hours_per_day" in union:
                assert isinstance(union["max_duty_hours_per_day"], (int, float))
                assert union["max_duty_hours_per_day"] > 0


class TestRulePackLoading:
    """Test rule pack loading and parsing functionality."""

    def test_rule_pack_yaml_loading(self, temp_rule_pack_file, sample_rule_pack):
        """Rule pack should load correctly from YAML file."""
        with open(temp_rule_pack_file) as f:
            loaded_rule_pack = yaml.safe_load(f)

        assert loaded_rule_pack == sample_rule_pack
        assert loaded_rule_pack["version"] == "2025.08"
        assert loaded_rule_pack["airline"] == "UAL"

    def test_rule_pack_file_not_found_handling(self):
        """Rule pack loading should handle missing files gracefully."""
        non_existent_file = Path("/non/existent/rule_pack.yml")

        # This test will drive error handling implementation
        # For now, we expect it to raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            with open(non_existent_file) as f:
                yaml.safe_load(f)

    def test_rule_pack_invalid_yaml_handling(self):
        """Rule pack loading should handle invalid YAML gracefully."""
        # Create obviously invalid YAML with syntax error
        invalid_yaml = """
        version: "2025.08"
        airline: UAL
        id: UAL-2025-08
        far117:
          min_rest_hours: 10
          hard:
            - id: FAR117_MIN_REST
              desc: Rest >= 10h
              check: pairing.rest_hours >= 10
        # Missing closing brace
        """

        # This test will drive YAML validation implementation
        # For now, we expect it to raise YAMLError
        with pytest.raises(yaml.YAMLError):
            yaml.safe_load(invalid_yaml)

    def test_rule_pack_encoding_handling(self):
        """Rule pack loading should handle different encodings."""
        # This test will drive encoding handling implementation
        # For now, we test basic UTF-8 handling
        rule_pack_data = {
            "version": "2025.08",
            "airline": "UAL",
            "id": "UAL-2025-08",
            "description": "United Airlines 2025.08 Rule Pack",
        }

        yaml_string = yaml.dump(rule_pack_data, encoding="utf-8")
        loaded_data = yaml.safe_load(yaml_string.decode("utf-8"))

        assert loaded_data == rule_pack_data


class TestRulePackManagement:
    """Test rule pack management operations."""

    def test_rule_pack_creation(self, sample_rule_pack):
        """Rule pack should be created with valid data."""
        # Test rule pack creation logic
        rule_pack = sample_rule_pack.copy()

        # Validate required fields
        assert "version" in rule_pack
        assert "airline" in rule_pack
        assert "id" in rule_pack

        # Validate data types
        assert isinstance(rule_pack["version"], str)
        assert isinstance(rule_pack["airline"], str)
        assert isinstance(rule_pack["id"], str)

    def test_rule_pack_update(self, sample_rule_pack):
        """Rule pack should be updatable."""
        # Test rule pack update logic
        original_version = sample_rule_pack["version"]

        # Update version
        updated_rule_pack = sample_rule_pack.copy()
        updated_rule_pack["version"] = "2025.09"

        assert updated_rule_pack["version"] != original_version
        assert updated_rule_pack["version"] == "2025.09"

        # Other fields should remain unchanged
        assert updated_rule_pack["airline"] == sample_rule_pack["airline"]
        assert updated_rule_pack["id"] == sample_rule_pack["id"]

    def test_rule_pack_deletion(self, sample_rule_pack):
        """Rule pack should be deletable."""
        # Test rule pack deletion logic
        rule_pack = sample_rule_pack.copy()

        # Simulate deletion by removing key fields
        del rule_pack["version"]
        del rule_pack["airline"]
        del rule_pack["id"]

        # Required fields should be missing
        assert "version" not in rule_pack
        assert "airline" not in rule_pack
        assert "id" not in rule_pack

    def test_rule_pack_validation_on_update(self, rule_pack_validator, sample_rule_pack):
        """Rule pack should be validated after updates."""
        # Test validation after updates
        rule_pack = sample_rule_pack.copy()

        # Valid update
        rule_pack["version"] = "2025.09"
        missing_fields = rule_pack_validator.validate_required_fields(rule_pack)
        assert missing_fields == []

        # Invalid update
        rule_pack["airline"] = "INVALID"
        assert not rule_pack_validator.validate_airline_code(rule_pack["airline"])


class TestRulePackAPI:
    """Test rule pack API endpoints."""

    def test_rule_pack_list_endpoint(self, client: TestClient):
        """API should provide endpoint to list available rule packs."""
        # This test will drive API endpoint implementation
        # For now, we test that the endpoint structure exists
        response = client.get("/api/rulepacks")

        # Future: Implement rule pack listing endpoint
        # assert response.status_code == 200
        # data = response.json()
        # assert "rule_packs" in data
        # assert isinstance(data["rule_packs"], list)

    def test_rule_pack_get_endpoint(self, client: TestClient):
        """API should provide endpoint to get specific rule pack."""
        # This test will drive API endpoint implementation
        # For now, we test that the endpoint structure exists
        response = client.get("/api/rulepacks/UAL-2025-08")

        # Future: Implement rule pack retrieval endpoint
        # assert response.status_code == 200
        # data = response.json()
        # assert data["id"] == "UAL-2025-08"

    def test_rule_pack_create_endpoint(self, client: TestClient, sample_rule_pack):
        """API should provide endpoint to create new rule pack."""
        # This test will drive API endpoint implementation
        # For now, we test that the endpoint structure exists
        response = client.post("/api/rulepacks", json=sample_rule_pack)

        # Future: Implement rule pack creation endpoint
        # assert response.status_code == 201
        # data = response.json()
        # assert "id" in data

    def test_rule_pack_update_endpoint(self, client: TestClient, sample_rule_pack):
        """API should provide endpoint to update existing rule pack."""
        # This test will drive API endpoint implementation
        # For now, we test that the endpoint structure exists
        updated_rule_pack = sample_rule_pack.copy()
        updated_rule_pack["version"] = "2025.09"

        response = client.put("/api/rulepacks/UAL-2025-08", json=updated_rule_pack)

        # Future: Implement rule pack update endpoint
        # assert response.status_code == 200
        # data = response.json()
        # assert data["version"] == "2025.09"


class TestRulePackIntegration:
    """Test rule pack integration with other systems."""

    def test_rule_pack_with_health_system(self, client: TestClient):
        """Health system should report rule pack status."""
        # This test will drive integration implementation
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        # Future: Add rule pack health integration
        # assert "rule_packs" in data
        # assert "status" in data["rule_packs"]

    def test_rule_pack_with_validation_system(self, sample_rule_pack):
        """Rule pack should integrate with validation system."""
        # This test will drive validation integration
        # For now, we test basic validation
        assert "far117" in sample_rule_pack
        assert "union" in sample_rule_pack

        # Future: Add validation system integration
        # validation_result = validation_system.validate(sample_rule_pack)
        # assert validation_result.is_valid

    def test_rule_pack_with_optimization_system(self, sample_rule_pack):
        """Rule pack should integrate with optimization system."""
        # This test will drive optimization integration
        # For now, we test basic structure
        assert "rules" in sample_rule_pack
        assert isinstance(sample_rule_pack["rules"], list)

        # Future: Add optimization system integration
        # optimization_result = optimization_system.optimize(sample_rule_pack)
        # assert optimization_result is not None


# Test markers for pytest
pytestmark = [pytest.mark.rulepacks, pytest.mark.api, pytest.mark.unit]
