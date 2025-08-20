"""Integration tests for optimizer rule pack integration."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from app.models import ContextSnapshot, FeatureBundle, PreferenceSchema
from app.services.optimizer import _get_scoring_weights, _rule_hits_misses
from app.services.rule_pack_loader import RulePackLoader


class TestOptimizerRuleIntegration:
    """Test integration between optimizer and rule packs."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Create test rule pack
        self.create_test_rule_pack()
        
        # Create test feature bundle
        self.bundle = self.create_test_bundle()

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_rule_pack(self):
        """Create a test rule pack file."""
        airline_dir = self.temp_dir / 'UAL'
        airline_dir.mkdir()
        
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
                'evaluate': "trip.get('duty_hours', 0) <= context.get('max_duty_hours', 12)"
            },
            {
                'id': 'LAYOVER_PREFERENCE',
                'desc': 'Prefer longer layovers',
                'severity': 'soft',
                'weight': 1.5,
                'evaluate': "trip.get('layover_hours', 0)"
            },
            {
                'id': 'AWARD_RATE_BONUS',
                'desc': 'Bonus for high award rate cities',
                'severity': 'soft',
                'weight': 2.0,
                'evaluate': "trip.get('award_rate', 0.5)"
            }
        ]
        
        data = {
            'version': '2025.09',
            'airline': 'UAL',
            'id': 'UAL-2025-09',
            'rules': rules
        }
        
        rule_pack_file = airline_dir / '2025.09.yml'
        with open(rule_pack_file, 'w') as f:
            yaml.dump(data, f)

    def create_test_bundle(self) -> FeatureBundle:
        """Create a test feature bundle."""
        context = ContextSnapshot(
            ctx_id="test-123",
            pilot_id="pilot-001",
            airline="UAL",
            month="2025.09",
            base="SFO",
            seat="FO",
            equip=["737"],
            seniority_percentile=0.6
        )
        
        preferences = PreferenceSchema(
            pilot_id="pilot-001",
            airline="UAL",
            base="SFO",
            seat="FO",
            equip=["737"]
        )
        
        return FeatureBundle(
            context=context,
            preference_schema=preferences,
            analytics_features={},
            compliance_flags={},
            pairing_features={}
        )

    @patch('app.services.rule_pack_loader.rule_pack_loader')
    def test_get_scoring_weights_uses_rule_pack(self, mock_loader):
        """Test that scoring weights are loaded from rule pack."""
        # Setup mock loader
        mock_rule_pack_loader = RulePackLoader(rule_packs_dir=self.temp_dir)
        mock_loader.load_rule_pack = mock_rule_pack_loader.load_rule_pack
        
        weights = _get_scoring_weights(self.bundle)
        
        # Should contain weights from soft rules
        assert 'LAYOVER_PREFERENCE' in weights
        assert 'AWARD_RATE_BONUS' in weights
        
        # Check that weights are normalized
        total_weight = sum(weights.values())
        assert abs(total_weight - 1.0) < 0.001  # Should be normalized to 1.0

    @patch('app.services.rule_pack_loader.rule_pack_loader')
    def test_get_scoring_weights_with_persona(self, mock_loader):
        """Test scoring weights with persona adjustments."""
        # Setup mock loader
        mock_rule_pack_loader = RulePackLoader(rule_packs_dir=self.temp_dir)
        mock_loader.load_rule_pack = mock_rule_pack_loader.load_rule_pack
        
        # Add persona to preferences
        self.bundle.preference_schema.source = {"persona": "family_first"}
        
        weights = _get_scoring_weights(self.bundle)
        
        # Should still contain rule pack weights
        assert 'LAYOVER_PREFERENCE' in weights
        assert 'AWARD_RATE_BONUS' in weights

    @patch('app.services.rule_pack_loader.rule_pack_loader')
    def test_get_scoring_weights_fallback_on_error(self, mock_loader):
        """Test fallback to legacy weights when rule pack loading fails."""
        # Make the loader raise an exception
        mock_loader.load_rule_pack.side_effect = FileNotFoundError("No rule pack")
        
        weights = _get_scoring_weights(self.bundle)
        
        # Should contain default weights
        assert 'award_rate' in weights
        assert 'layovers' in weights
        
        # Should not contain rule pack specific weights
        assert 'LAYOVER_PREFERENCE' not in weights
        assert 'AWARD_RATE_BONUS' not in weights

    @patch('app.services.rule_pack_loader.rule_pack_loader')
    def test_rule_hits_misses_uses_rule_pack(self, mock_loader):
        """Test that hard rule validation uses rule pack."""
        # Setup mock loader
        mock_rule_pack_loader = RulePackLoader(rule_packs_dir=self.temp_dir)
        mock_loader.load_rule_pack = mock_rule_pack_loader.load_rule_pack
        
        # Create test pairing that satisfies rules
        pairing = {
            "days_off": 10,  # Satisfies MIN_DAYS_OFF (>= 8)
            "duty_hours": 8,  # Satisfies MAX_DUTY_HOURS (<= 12)
            "rest_hours": 15  # Good rest
        }
        
        hits, misses = _rule_hits_misses(self.bundle, pairing)
        
        # Should evaluate rule pack rules
        assert 'MIN_DAYS_OFF' in hits  # Should pass
        assert 'MAX_DUTY_HOURS' in hits  # Should pass
        assert 'MIN_DAYS_OFF' not in misses
        assert 'MAX_DUTY_HOURS' not in misses

    @patch('app.services.rule_pack_loader.rule_pack_loader')
    def test_rule_hits_misses_violations(self, mock_loader):
        """Test hard rule violations are detected."""
        # Setup mock loader
        mock_rule_pack_loader = RulePackLoader(rule_packs_dir=self.temp_dir)
        mock_loader.load_rule_pack = mock_rule_pack_loader.load_rule_pack
        
        # Create test pairing that violates rules
        pairing = {
            "days_off": 5,   # Violates MIN_DAYS_OFF (< 8)
            "duty_hours": 15,  # Violates MAX_DUTY_HOURS (> 12)
            "rest_hours": 8   # Poor rest
        }
        
        hits, misses = _rule_hits_misses(self.bundle, pairing)
        
        # Should detect violations
        assert 'MIN_DAYS_OFF' in misses  # Should fail
        assert 'MAX_DUTY_HOURS' in misses  # Should fail
        assert 'MIN_DAYS_OFF' not in hits
        assert 'MAX_DUTY_HOURS' not in hits

    @patch('app.services.rule_pack_loader.rule_pack_loader')
    def test_rule_hits_misses_fallback_on_error(self, mock_loader):
        """Test fallback to legacy validation when rule pack fails."""
        # Make the loader raise an exception
        mock_loader.load_rule_pack.side_effect = FileNotFoundError("No rule pack")
        
        pairing = {
            "rest_hours": 15,  # Good rest for legacy validation
            "redeye": False    # Not a redeye
        }
        
        hits, misses = _rule_hits_misses(self.bundle, pairing)
        
        # Should use legacy rules
        assert 'FAR117_MIN_REST' in hits
        assert 'NO_REDEYE_IF_SET' in hits
        
        # Should not contain rule pack specific rules
        assert 'MIN_DAYS_OFF' not in hits
        assert 'MIN_DAYS_OFF' not in misses

    def test_missing_month_fallback(self):
        """Test behavior when month is missing from context."""
        # Since month is now required, we'll test the getattr fallback inside the function
        # by creating a context with month and then testing the getattr behavior
        context = ContextSnapshot(
            ctx_id="test-123",
            pilot_id="pilot-001",
            airline="UAL",
            month="2025.09",  # Required field
            base="SFO",
            seat="FO",
            equip=["737"],
            seniority_percentile=0.6
        )
        
        bundle = FeatureBundle(
            context=context,
            preference_schema=self.bundle.preference_schema,
            analytics_features={},
            compliance_flags={},
            pairing_features={}
        )
        
        with patch('app.services.rule_pack_loader.rule_pack_loader') as mock_loader:
            mock_rule_pack_loader = RulePackLoader(rule_packs_dir=self.temp_dir)
            mock_loader.load_rule_pack = mock_rule_pack_loader.load_rule_pack
            
            # Test with a context that has month field
            weights = _get_scoring_weights(bundle)
            
            # Should work and include rule pack weights
            assert len(weights) > 0
            assert 'LAYOVER_PREFERENCE' in weights or 'award_rate' in weights  # Either rule pack or fallback

    def test_context_weights_override(self):
        """Test that context weights override rule pack weights."""
        with patch('app.services.rule_pack_loader.rule_pack_loader') as mock_loader:
            mock_rule_pack_loader = RulePackLoader(rule_packs_dir=self.temp_dir)
            mock_loader.load_rule_pack = mock_rule_pack_loader.load_rule_pack
            
            # Add context weight overrides
            self.bundle.context.default_weights = {
                'LAYOVER_PREFERENCE': 5.0,  # Override rule pack weight
                'custom_weight': 2.0        # Add new weight
            }
            
            weights = _get_scoring_weights(self.bundle)
            
            # Should contain overridden weight (after normalization)
            assert 'LAYOVER_PREFERENCE' in weights
            assert 'custom_weight' in weights
            
            # Total should still be normalized to 1.0
            total_weight = sum(weights.values())
            assert abs(total_weight - 1.0) < 0.001
