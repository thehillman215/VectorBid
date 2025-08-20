"""API tests for rule pack endpoints."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from fastapi.testclient import TestClient

from app.main import app
from app.services.rule_pack_loader import RulePackLoader

client = TestClient(app)


class TestRulePackAPI:
    """Test cases for rule pack API endpoints."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.create_test_rule_packs()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_rule_packs(self):
        """Create test rule pack files."""
        # Create UAL rule pack
        ual_dir = self.temp_dir / 'UAL'
        ual_dir.mkdir()
        
        ual_rules = [
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
        
        ual_data = {
            'version': '2025.09',
            'airline': 'UAL',
            'id': 'UAL-2025-09',
            'rules': ual_rules
        }
        
        with open(ual_dir / '2025.09.yml', 'w') as f:
            yaml.dump(ual_data, f)
        
        # Create another UAL rule pack for different month
        ual_rules_oct = [
            {
                'id': 'MIN_DAYS_OFF',
                'desc': 'Minimum 8 days off per month',
                'severity': 'hard',
                'evaluate': "context.get('days_off', 0) >= 8"
            }
        ]
        
        ual_data_oct = {
            'version': '2025.10',
            'airline': 'UAL',
            'id': 'UAL-2025-10',
            'rules': ual_rules_oct
        }
        
        with open(ual_dir / '2025.10.yml', 'w') as f:
            yaml.dump(ual_data_oct, f)

    @patch('app.routes.rule_packs.rule_pack_loader')
    def test_get_rule_pack_success(self, mock_loader):
        """Test successful rule pack retrieval."""
        # Setup mock loader
        mock_rule_pack_loader = RulePackLoader(rule_packs_dir=self.temp_dir)
        mock_loader.load_rule_pack = mock_rule_pack_loader.load_rule_pack
        
        response = client.get("/api/rule-packs/UAL/2025.09")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['airline'] == 'UAL'
        assert data['contract_period'] == '2025.09'
        assert len(data['hard_rules']) == 1
        assert len(data['soft_rules']) == 1
        
        # Check hard rule
        hard_rule = data['hard_rules'][0]
        assert hard_rule['name'] == 'MIN_DAYS_OFF'
        assert hard_rule['severity'] == 'error'
        
        # Check soft rule
        soft_rule = data['soft_rules'][0]
        assert soft_rule['name'] == 'LAYOVER_PREFERENCE'
        assert soft_rule['weight'] == 1.5

    @patch('app.routes.rule_packs.rule_pack_loader')
    def test_get_rule_pack_not_found(self, mock_loader):
        """Test rule pack not found error."""
        # Make the loader raise FileNotFoundError
        mock_loader.load_rule_pack.side_effect = FileNotFoundError("Rule pack not found")
        
        response = client.get("/api/rule-packs/FAKE/2025.01")
        
        assert response.status_code == 404
        data = response.json()
        assert "Rule pack not found for FAKE/2025.01" in data['detail']

    @patch('app.routes.rule_packs.rule_pack_loader')
    def test_get_rule_pack_server_error(self, mock_loader):
        """Test server error during rule pack loading."""
        # Make the loader raise a generic exception
        mock_loader.load_rule_pack.side_effect = Exception("Internal error")
        
        response = client.get("/api/rule-packs/UAL/2025.09")
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to load rule pack" in data['detail']

    @patch('app.routes.rule_packs.rule_pack_loader')
    def test_list_rule_packs_success(self, mock_loader):
        """Test successful listing of rule packs."""
        # Setup mock loader
        mock_rule_pack_loader = RulePackLoader(rule_packs_dir=self.temp_dir)
        mock_loader.list_available_rule_packs = mock_rule_pack_loader.list_available_rule_packs
        
        response = client.get("/api/rule-packs")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 2  # UAL 2025.09 and 2025.10
        
        # Check that both rule packs are listed
        airlines_months = [(item['airline'], item['month']) for item in data]
        assert ('UAL', '2025.09') in airlines_months
        assert ('UAL', '2025.10') in airlines_months
        
        # Check that paths are included
        for item in data:
            assert 'path' in item
            assert item['path'].endswith('.yml')

    @patch('app.routes.rule_packs.rule_pack_loader')
    def test_list_rule_packs_server_error(self, mock_loader):
        """Test server error during rule pack listing."""
        # Make the loader raise an exception
        mock_loader.list_available_rule_packs.side_effect = Exception("Directory error")
        
        response = client.get("/api/rule-packs")
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to list rule packs" in data['detail']

    @patch('app.routes.rule_packs.rule_pack_loader')
    def test_clear_rule_pack_cache_success(self, mock_loader):
        """Test successful cache clearing."""
        response = client.post("/api/rule-packs/clear-cache")
        
        assert response.status_code == 200
        data = response.json()
        assert data['message'] == "Rule pack cache cleared successfully"
        
        # Verify that clear_cache was called
        mock_loader.clear_cache.assert_called_once()

    @patch('app.routes.rule_packs.rule_pack_loader')
    def test_clear_rule_pack_cache_error(self, mock_loader):
        """Test error during cache clearing."""
        # Make clear_cache raise an exception
        mock_loader.clear_cache.side_effect = Exception("Cache error")
        
        response = client.post("/api/rule-packs/clear-cache")
        
        assert response.status_code == 500
        data = response.json()
        assert "Failed to clear cache" in data['detail']

    def test_rule_pack_endpoints_without_mock(self):
        """Test that rule pack endpoints work with actual rule pack loader."""
        # This test doesn't use mocks to ensure the endpoints work with real loader
        response = client.get("/api/rule-packs")
        
        # Should return 200 even if no rule packs exist
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_rule_pack_with_actual_file(self):
        """Test loading an actual rule pack file."""
        # Test with the real UAL rule pack if it exists
        response = client.get("/api/rule-packs/UAL/2025.09")
        
        # Should either return the rule pack or 404 if it doesn't exist
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert 'airline' in data
            assert 'contract_period' in data
            assert 'hard_rules' in data
            assert 'soft_rules' in data

    def test_rule_pack_api_response_format(self):
        """Test that API responses have correct format."""
        with patch('app.routes.rule_packs.rule_pack_loader') as mock_loader:
            # Setup mock loader
            mock_rule_pack_loader = RulePackLoader(rule_packs_dir=self.temp_dir)
            mock_loader.load_rule_pack = mock_rule_pack_loader.load_rule_pack
            
            response = client.get("/api/rule-packs/UAL/2025.09")
            
            assert response.status_code == 200
            data = response.json()
            
            # Check required fields
            required_fields = [
                'version', 'airline', 'contract_period', 'effective_start',
                'hard_rules', 'soft_rules', 'derived_rules', 'metadata'
            ]
            
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"
            
            # Check that dates are serialized as strings
            assert isinstance(data['effective_start'], str)
            
            # Check rule structure
            if data['hard_rules']:
                hard_rule = data['hard_rules'][0]
                assert 'name' in hard_rule
                assert 'description' in hard_rule
                assert 'check' in hard_rule
                assert 'severity' in hard_rule
            
            if data['soft_rules']:
                soft_rule = data['soft_rules'][0]
                assert 'name' in soft_rule
                assert 'description' in soft_rule
                assert 'weight' in soft_rule
                assert 'score' in soft_rule
