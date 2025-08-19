"""
Tests for the VectorBid Rules Engine.

Tests the validation engine, rule compilation, and pack resolution.
"""

import pytest
from datetime import date
from unittest.mock import Mock

from app.rules_engine import (
    RulePack, HardRule, SoftRule, DerivedRule, Violation, ScoreBreakdown,
    compile_rule_pack, RulePackValidator, score_schedule, PackResolver,
    pack_status, pack_registry_health
)


class TestRulePackModels:
    """Test the basic rule pack data models."""
    
    def test_hard_rule_creation(self):
        """HardRule should be created with correct attributes."""
        def test_predicate(obj, ctx):
            return True
        
        rule = HardRule(
            id="TEST_RULE",
            predicate=test_predicate,
            message="Test rule message",
            severity="ERROR"
        )
        
        assert rule.id == "TEST_RULE"
        assert rule.message == "Test rule message"
        assert rule.severity == "ERROR"
        assert rule.predicate(None, None) is True
    
    def test_soft_rule_creation(self):
        """SoftRule should be created with correct attributes."""
        def test_score(obj, ctx):
            return 0.8
        
        rule = SoftRule(
            id="TEST_SCORE",
            score=test_score,
            weight=0.5,
            bounds=(0.0, 1.0)
        )
        
        assert rule.id == "TEST_SCORE"
        assert rule.weight == 0.5
        assert rule.bounds == (0.0, 1.0)
        assert rule.score(None, None) == 0.8
    
    def test_derived_rule_creation(self):
        """DerivedRule should be created with correct attributes."""
        def test_expr(obj, ctx):
            return {"computed_field": 42}
        
        rule = DerivedRule(
            id="TEST_DERIVED",
            outputs={"computed_field": int},
            expr=test_expr
        )
        
        assert rule.id == "TEST_DERIVED"
        assert rule.outputs == {"computed_field": int}
        assert rule.expr(None, None) == {"computed_field": 42}
    
    def test_rule_pack_creation(self):
        """RulePack should be created with correct attributes."""
        pack = RulePack(
            airline="UAL",
            month="2025.08",
            base="ORD",
            fleet="B737",
            effective_start=date(2025, 8, 1),
            effective_end=date(2025, 8, 31),
            schema_version="v1",
            checksum="abc123",
            hard_rules=[],
            soft_rules=[],
            derived_rules=[]
        )
        
        assert pack.airline == "UAL"
        assert pack.month == "2025.08"
        assert pack.base == "ORD"
        assert pack.fleet == "B737"
        assert pack.schema_version == "v1"
        assert pack.checksum == "abc123"
        assert len(pack.hard_rules) == 0
        assert len(pack.soft_rules) == 0
        assert len(pack.derived_rules) == 0


class TestRulePackCompiler:
    """Test the rule pack compiler."""
    
    def test_compile_rule_pack_basic(self):
        """Should compile a basic rule pack from YAML."""
        yaml_obj = {
            "airline": "UAL",
            "version": "2025.08",
            "base": "ORD",
            "fleet": "B737",
            "effective_start": "2025-08-01",
            "effective_end": "2025-08-31",
            "schema_version": "v1",
            "checksum": "abc123",
            "hard": [
                {
                    "id": "MIN_REST",
                    "predicate": "rest_hours >= 10",
                    "message": "Rest must be at least 10 hours"
                }
            ],
            "soft": [
                {
                    "id": "PREF_SHORT_TRIPS",
                    "score": "if trip_length_days <= 4 then 1.0 else 0.5",
                    "weight": 0.8
                }
            ],
            "derived": [
                {
                    "id": "MAX_DUTY_BY_LEGS",
                    "outputs": {"max_duty_hours": "float"},
                    "expr": "if legs_count <= 4 then 14 else 12"
                }
            ]
        }
        
        pack = compile_rule_pack(yaml_obj)
        
        assert pack.airline == "UAL"
        assert pack.month == "2025.08"
        assert pack.base == "ORD"
        assert pack.fleet == "B737"
        assert pack.schema_version == "v1"
        assert pack.checksum == "abc123"
        assert len(pack.hard_rules) == 1
        assert len(pack.soft_rules) == 1
        assert len(pack.derived_rules) == 1
        
        # Check hard rule
        hard_rule = pack.hard_rules[0]
        assert hard_rule.id == "MIN_REST"
        assert hard_rule.message == "Rest must be at least 10 hours"
        assert hard_rule.severity == "ERROR"
        
        # Check soft rule
        soft_rule = pack.soft_rules[0]
        assert soft_rule.id == "PREF_SHORT_TRIPS"
        assert soft_rule.weight == 0.8
        
        # Check derived rule
        derived_rule = pack.derived_rules[0]
        assert derived_rule.id == "MAX_DUTY_BY_LEGS"
        assert derived_rule.outputs == {"max_duty_hours": "float"}
    
    def test_compile_rule_pack_minimal(self):
        """Should compile a minimal rule pack with defaults."""
        yaml_obj = {
            "airline": "UAL",
            "version": "2025.08",
            "effective_start": "2025-08-01"
        }
        
        pack = compile_rule_pack(yaml_obj)
        
        assert pack.airline == "UAL"
        assert pack.month == "2025.08"
        assert pack.base is None
        assert pack.fleet is None
        assert pack.effective_end is None
        assert pack.schema_version == "v1"
        assert pack.checksum == ""
        assert len(pack.hard_rules) == 0
        assert len(pack.soft_rules) == 0
        assert len(pack.derived_rules) == 0


class TestRulePackValidator:
    """Test the rule pack validator."""
    
    def test_validate_inputs_no_violations(self):
        """Should return empty list when no violations."""
        # Create a mock rule pack with a rule that always passes
        def always_pass(obj, ctx):
            return True
        
        hard_rule = HardRule(
            id="TEST_RULE",
            predicate=always_pass,
            message="Test rule"
        )
        
        pack = RulePack(
            airline="UAL",
            month="2025.08",
            base=None,
            fleet=None,
            effective_start=date(2025, 8, 1),
            effective_end=None,
            schema_version="v1",
            checksum="test",
            hard_rules=[hard_rule],
            soft_rules=[],
            derived_rules=[]
        )
        
        validator = RulePackValidator(pack, {"ctx_id": "test123"})
        violations = validator.validate_inputs({"test": "data"})
        
        assert len(violations) == 0
    
    def test_validate_inputs_with_violations(self):
        """Should return violations when rules fail."""
        # Create a mock rule pack with a rule that always fails
        def always_fail(obj, ctx):
            return False
        
        hard_rule = HardRule(
            id="TEST_RULE",
            predicate=always_fail,
            message="Test rule failed"
        )
        
        pack = RulePack(
            airline="UAL",
            month="2025.08",
            base=None,
            fleet=None,
            effective_start=date(2025, 8, 1),
            effective_end=None,
            schema_version="v1",
            checksum="test",
            hard_rules=[hard_rule],
            soft_rules=[],
            derived_rules=[]
        )
        
        validator = RulePackValidator(pack, {"ctx_id": "test123"})
        violations = validator.validate_inputs({"test": "data"})
        
        assert len(violations) == 1
        violation = violations[0]
        assert violation.rule_id == "TEST_RULE"
        assert violation.message == "Test rule failed"
        assert violation.severity == "ERROR"
        assert violation.path == "/preferences"
        assert violation.ctx_id == "test123"
        assert violation.pack_version == "UAL/2025.08"
    
    def test_validate_schedule(self):
        """Should validate schedule candidates."""
        def schedule_rule(obj, ctx):
            return getattr(obj, "valid", True)
        
        hard_rule = HardRule(
            id="SCHEDULE_RULE",
            predicate=schedule_rule,
            message="Schedule validation failed"
        )
        
        pack = RulePack(
            airline="UAL",
            month="2025.08",
            base=None,
            fleet=None,
            effective_start=date(2025, 8, 1),
            effective_end=None,
            schema_version="v1",
            checksum="test",
            hard_rules=[hard_rule],
            soft_rules=[],
            derived_rules=[]
        )
        
        validator = RulePackValidator(pack, {"ctx_id": "test123"})
        
        # Test valid schedule
        valid_schedule = Mock(valid=True)
        violations = validator.validate_schedule(valid_schedule)
        assert len(violations) == 0
        
        # Test invalid schedule
        invalid_schedule = Mock(valid=False)
        violations = validator.validate_schedule(invalid_schedule)
        assert len(violations) == 1
        assert violations[0].rule_id == "SCHEDULE_RULE"
    
    def test_validate_export(self):
        """Should validate bid layers before export."""
        def export_rule(obj, ctx):
            return getattr(obj, "exportable", True)
        
        hard_rule = HardRule(
            id="EXPORT_RULE",
            predicate=export_rule,
            message="Export validation failed"
        )
        
        pack = RulePack(
            airline="UAL",
            month="2025.08",
            base=None,
            fleet=None,
            effective_start=date(2025, 8, 1),
            effective_end=None,
            schema_version="v1",
            checksum="test",
            hard_rules=[hard_rule],
            soft_rules=[],
            derived_rules=[]
        )
        
        validator = RulePackValidator(pack, {"ctx_id": "test123"})
        
        # Test exportable layers
        exportable_layers = Mock(exportable=True)
        violations = validator.validate_export(exportable_layers)
        assert len(violations) == 0
        
        # Test non-exportable layers
        non_exportable_layers = Mock(exportable=False)
        violations = validator.validate_export(non_exportable_layers)
        assert len(violations) == 1
        assert violations[0].rule_id == "EXPORT_RULE"


class TestPackResolver:
    """Test the pack resolver."""
    
    def test_resolve_exact_match(self):
        """Should resolve exact airline/month/base/fleet match."""
        pack1 = RulePack(
            airline="UAL", month="2025.08", base="ORD", fleet="B737",
            effective_start=date(2025, 8, 1), effective_end=None,
            schema_version="v1", checksum="test",
            hard_rules=[], soft_rules=[], derived_rules=[]
        )
        
        pack2 = RulePack(
            airline="UAL", month="2025.08", base="ORD", fleet="B787",
            effective_start=date(2025, 8, 1), effective_end=None,
            schema_version="v1", checksum="test",
            hard_rules=[], soft_rules=[], derived_rules=[]
        )
        
        resolver = PackResolver([pack1, pack2])
        
        # Should find exact match
        result = resolver.resolve("UAL", "2025.08", "ORD", "B737")
        assert result == pack1
        
        # Should find other exact match
        result = resolver.resolve("UAL", "2025.08", "ORD", "B787")
        assert result == pack2
    
    def test_resolve_fallback(self):
        """Should fallback to less specific matches."""
        pack1 = RulePack(
            airline="UAL", month="2025.08", base="ORD", fleet="B737",
            effective_start=date(2025, 8, 1), effective_end=None,
            schema_version="v1", checksum="test",
            hard_rules=[], soft_rules=[], derived_rules=[]
        )
        
        pack2 = RulePack(
            airline="UAL", month="2025.08", base=None, fleet=None,
            effective_start=date(2025, 8, 1), effective_end=None,
            schema_version="v1", checksum="test",
            hard_rules=[], soft_rules=[], derived_rules=[]
        )
        
        resolver = PackResolver([pack1, pack2])
        
        # Should fallback to general pack when specific not found
        result = resolver.resolve("UAL", "2025.08", "LAX", "B787")
        assert result == pack2
    
    def test_resolve_month_fallback(self):
        """Should fallback to earlier months when exact not found."""
        pack1 = RulePack(
            airline="UAL", month="2025.07", base=None, fleet=None,
            effective_start=date(2025, 7, 1), effective_end=None,
            schema_version="v1", checksum="test",
            hard_rules=[], soft_rules=[], derived_rules=[]
        )
        
        pack2 = RulePack(
            airline="UAL", month="2025.06", base=None, fleet=None,
            effective_start=date(2025, 6, 1), effective_end=None,
            schema_version="v1", checksum="test",
            hard_rules=[], soft_rules=[], derived_rules=[]
        )
        
        resolver = PackResolver([pack1, pack2])
        
        # Should find July pack for August request
        result = resolver.resolve("UAL", "2025.08")
        assert result == pack1
    
    def test_resolve_not_found(self):
        """Should raise LookupError when no pack found."""
        resolver = PackResolver([])
        
        with pytest.raises(LookupError, match="No rule pack found for UAL 2025.08"):
            resolver.resolve("UAL", "2025.08")


class TestHealthFunctions:
    """Test the health monitoring functions."""
    
    def test_pack_status(self):
        """Should return status for a single pack."""
        pack = RulePack(
            airline="UAL",
            month="2025.08",
            base="ORD",
            fleet="B737",
            effective_start=date(2025, 8, 1),
            effective_end=date(2025, 8, 31),
            schema_version="v1",
            checksum="abc123",
            hard_rules=[Mock()],  # Mock rules for counting
            soft_rules=[Mock(), Mock()],
            derived_rules=[Mock(), Mock(), Mock()]
        )
        
        status = pack_status(pack)
        
        assert status["airline"] == "UAL"
        assert status["month"] == "2025.08"
        assert status["base"] == "ORD"
        assert status["fleet"] == "B737"
        assert status["hard_rules"] == 1
        assert status["soft_rules"] == 2
        assert status["derived_rules"] == 3
        assert status["checksum"] == "abc123"
        assert status["schema_version"] == "v1"
    
    def test_pack_registry_health(self):
        """Should return overall registry health."""
        pack1 = RulePack(
            airline="UAL", month="2025.08", base=None, fleet=None,
            effective_start=date(2025, 8, 1), effective_end=None,
            schema_version="v1", checksum="test",
            hard_rules=[Mock()], soft_rules=[Mock()], derived_rules=[]
        )
        
        pack2 = RulePack(
            airline="AAL", month="2025.08", base=None, fleet=None,
            effective_start=date(2025, 8, 1), effective_end=None,
            schema_version="v1", checksum="test",
            hard_rules=[Mock(), Mock()], soft_rules=[], derived_rules=[Mock()]
        )
        
        health = pack_registry_health([pack1, pack2])
        
        assert health["status"] == "ok"
        assert health["count"] == 2
        assert health["rule_counts"]["hard"] == 3
        assert health["rule_counts"]["soft"] == 1
        assert health["rule_counts"]["derived"] == 1
        assert "UAL" in health["airlines"]
        assert "AAL" in health["airlines"]
        assert health["coverage_window"] == "2025.08 to 2025.08"
    
    def test_pack_registry_health_empty(self):
        """Should handle empty registry."""
        health = pack_registry_health([])
        
        assert health["status"] == "error"
        assert health["message"] == "No rule packs available"
        assert health["count"] == 0


# Test markers for pytest
pytestmark = [
    pytest.mark.rules_engine,
    pytest.mark.unit
]

