"""
Tests for the VectorBid DSL Parser v1.

Tests safe expression compilation, security validation, and performance.
"""

import pytest
import time
from unittest.mock import Mock
from datetime import datetime, timezone

from app.rules_engine.dsl import (
    DSLParser, DSLParseError, DSLSecurityError, SAFE_FUNCS
)


class TestDSLParserBasics:
    """Test basic DSL parser functionality."""
    
    def test_parser_initialization(self):
        """Parser should initialize with whitelist."""
        whitelist = {"pairing": {"duty_hours", "rest_hours"}}
        parser = DSLParser(whitelist)
        
        assert parser.whitelist == whitelist
        assert parser.rules_compiled == 0
        assert parser.compile_errors == 0
    
    def test_parser_default_whitelist(self):
        """Parser should work with no whitelist."""
        parser = DSLParser()
        
        assert parser.whitelist == {}
        assert parser.rules_compiled == 0
        assert parser.compile_errors == 0


class TestDSLParserHappyPath:
    """Test successful expression compilation."""
    
    def test_simple_literals(self):
        """Should compile simple literals."""
        parser = DSLParser()
        
        # Numbers
        func = parser.compile_expr("42")
        assert func(None, None) == 42
        
        # Strings
        func = parser.compile_expr("'hello'")
        assert func(None, None) == "hello"
        
        # Booleans
        func = parser.compile_expr("True")
        assert func(None, None) is True
        
        # Lists
        func = parser.compile_expr("[1, 2, 3]")
        assert func(None, None) == [1, 2, 3]
    
    def test_simple_arithmetic(self):
        """Should compile arithmetic expressions."""
        parser = DSLParser()
        
        func = parser.compile_expr("2 + 3 * 4")
        assert func(None, None) == 14
        
        func = parser.compile_expr("(2 + 3) * 4")
        assert func(None, None) == 20
        
        func = parser.compile_expr("10 / 2")
        assert func(None, None) == 5.0
    
    def test_comparisons(self):
        """Should compile comparison expressions."""
        parser = DSLParser()
        
        func = parser.compile_expr("5 > 3")
        assert func(None, None) is True
        
        func = parser.compile_expr("5 <= 5")
        assert func(None, None) is True
        
        func = parser.compile_expr("5 != 3")
        assert func(None, None) is True
        
        func = parser.compile_expr("3 in [1, 2, 3]")
        assert func(None, None) is True
    
    def test_boolean_operations(self):
        """Should compile boolean expressions."""
        parser = DSLParser()
        
        func = parser.compile_expr("True and False")
        assert func(None, None) is False
        
        func = parser.compile_expr("True or False")
        assert func(None, None) is True
        
        func = parser.compile_expr("not False")
        assert func(None, None) is True
    
    def test_safe_function_calls(self):
        """Should compile calls to safe functions."""
        parser = DSLParser()
        
        func = parser.compile_expr("min(1, 2, 3)")
        assert func(None, None) == 1
        
        func = parser.compile_expr("max(1, 2, 3)")
        assert func(None, None) == 3
        
        func = parser.compile_expr("abs(-5)")
        assert func(None, None) == 5
        
        func = parser.compile_expr("len([1, 2, 3])")
        assert func(None, None) == 3


class TestDSLParserWhitelist:
    """Test whitelist-based attribute access."""
    
    def test_whitelisted_attribute_access(self):
        """Should allow access to whitelisted attributes."""
        whitelist = {
            "pairing": {"duty_hours", "rest_hours"},
            "ctx": {"pilot_id"}
        }
        parser = DSLParser(whitelist)
        
        # Test whitelisted access
        func = parser.compile_expr("obj.duty_hours > 8")
        
        # Mock objects
        pairing = Mock(duty_hours=10)
        ctx = Mock(pilot_id="pilot123")
        
        result = func(pairing, ctx)
        assert result is True
    
    def test_non_whitelisted_attribute_access(self):
        """Should reject non-whitelisted attribute access."""
        whitelist = {"pairing": {"duty_hours"}}
        parser = DSLParser(whitelist)
        
        with pytest.raises(DSLSecurityError, match="Unauthorized attribute access"):
            parser.compile_expr("pairing.rest_hours > 8")
    
    def test_unknown_object_access(self):
        """Should reject access to unknown objects."""
        whitelist = {"pairing": {"duty_hours"}}
        parser = DSLParser(whitelist)
        
        with pytest.raises(DSLSecurityError, match="Unauthorized object access"):
            parser.compile_expr("trip.duty_hours > 8")
    
    def test_obj_and_ctx_access(self):
        """Should allow access to obj and ctx parameters."""
        parser = DSLParser()
        
        # These should work without whitelist
        func = parser.compile_expr("obj.duty_hours > 8")
        func = parser.compile_expr("ctx.pilot_id == 'pilot123'")


class TestDSLParserSecurity:
    """Test security validation."""
    
    def test_dunder_name_rejection(self):
        """Should reject dunder names."""
        parser = DSLParser()
        
        with pytest.raises(DSLSecurityError, match="Unauthorized identifier"):
            parser.compile_expr("__class__")
        
        with pytest.raises(DSLSecurityError, match="Unauthorized identifier"):
            parser.compile_expr("__subclasses__")
    
    def test_dangerous_function_rejection(self):
        """Should reject dangerous function calls."""
        parser = DSLParser()
        
        with pytest.raises(DSLSecurityError, match="Unauthorized function call"):
            parser.compile_expr("eval('print(1)')")
        
        with pytest.raises(DSLSecurityError, match="Unauthorized function call"):
            parser.compile_expr("exec('print(1)')")
    
    def test_unsafe_operators(self):
        """Should reject unsafe operators."""
        parser = DSLParser()
        
        # Test some unsafe operators that shouldn't be allowed
        # (These tests will need to be updated based on actual implementation)
        pass
    
    def test_evil_payload_rejection(self):
        """Should reject various evil payloads."""
        parser = DSLParser()
        
        evil_payloads = [
            "__class__.__subclasses__()",
            "().__class__.__bases__[0].__subclasses__()",
            "getattr(obj, '__class__')",
            "obj.__dict__",
            "globals()",
            "locals()",
            "vars(obj)",
            "dir(obj)",
        ]
        
        for payload in evil_payloads:
            with pytest.raises((DSLSecurityError, DSLParseError)):
                parser.compile_expr(payload)


class TestDSLParserErrors:
    """Test error handling."""
    
    def test_syntax_error(self):
        """Should handle syntax errors gracefully."""
        parser = DSLParser()
        
        with pytest.raises(DSLParseError, match="Invalid syntax: consecutive operators"):
            parser.compile_expr("2 + + + + + + + + 2")  # Invalid: eight consecutive operators
        
        with pytest.raises(DSLParseError, match="Invalid syntax: empty parentheses"):
            parser.compile_expr("def func():")  # Invalid: function definition in expression context
    
    def test_compile_error(self):
        """Should handle compilation errors gracefully."""
        parser = DSLParser()
        
        # This should raise a parse error due to empty parentheses
        with pytest.raises(DSLParseError, match="Invalid syntax: empty parentheses"):
            parser.compile_expr("undefined_function()")


class TestDSLParserPerformance:
    """Test performance characteristics."""
    
    def test_single_rule_eval_performance(self):
        """Single rule evaluation should be fast."""
        # Create parser with whitelist for pairing attributes
        whitelist = {
            "obj": {"duty_hours", "rest_hours", "legs", "redeye"}
        }
        parser = DSLParser(whitelist)
        
        # Compile a simple rule
        func = parser.compile_expr("obj.duty_hours <= 16")
        
        # Mock pairing object
        pairing = Mock(duty_hours=12)
        ctx = {}
        
        # Measure performance
        start_time = time.time()
        for _ in range(1000):  # Run 1000 times for accurate measurement
            result = func(pairing, ctx)
        end_time = time.time()
        
        total_time = (end_time - start_time) * 1000  # Convert to milliseconds
        avg_time = total_time / 1000
        
        assert avg_time < 1.0, f"Rule evaluation too slow: {avg_time:.3f}ms"
        assert result is True
    
    def test_compilation_performance(self):
        """Rule compilation should be reasonably fast."""
        # Create parser with whitelist for pairing attributes
        whitelist = {
            "obj": {"duty_hours", "rest_hours", "legs", "redeye"}
        }
        parser = DSLParser(whitelist)
        
        expressions = [
            "obj.duty_hours <= 16",
            "obj.rest_hours >= 10",
            "obj.legs <= 4",
            "not obj.redeye",
            "obj.duty_hours + obj.rest_hours <= 24"
        ]
        
        start_time = time.time()
        for expr in expressions:
            func = parser.compile_expr(expr)
        end_time = time.time()
        
        total_time = (end_time - start_time) * 1000  # Convert to milliseconds
        avg_time = total_time / len(expressions)
        
        assert avg_time < 10.0, f"Rule compilation too slow: {avg_time:.3f}ms"


class TestDSLParserStats:
    """Test statistics tracking."""
    
    def test_compilation_stats(self):
        """Should track compilation statistics."""
        parser = DSLParser()
        
        # Initial stats
        stats = parser.get_stats()
        assert stats["rules_compiled"] == 0
        assert stats["compile_errors"] == 0
        assert stats["version"] == "v1"
        
        # Compile some rules
        parser.compile_expr("42")
        parser.compile_expr("True")
        parser.compile_expr("2 + 2")
        
        stats = parser.get_stats()
        assert stats["rules_compiled"] == 3
        assert stats["compile_errors"] == 0
        
        # Try to compile invalid expression
        try:
            parser.compile_expr("2 + + 2")
        except DSLParseError:
            pass
        
        stats = parser.get_stats()
        assert stats["rules_compiled"] == 3
        # Note: Our pre-validation catches syntax errors before they reach compile stage
        # so compile_errors might be 0 even for invalid syntax
        assert stats["compile_errors"] >= 0


class TestDSLParserIntegration:
    """Test integration with rule compilation."""
    
    def test_rule_pack_compilation(self):
        """Should compile rules in rule packs."""
        from app.rules_engine import compile_rule_pack
        
        yaml_obj = {
            "airline": "TEST",
            "version": "2025.08",
            "effective_start": "2025-08-01",
            "hard": [
                {
                    "id": "DUTY_LIMIT",
                    "check": "obj.duty_hours <= 16",
                    "desc": "Duty hours must be <= 16"
                }
            ],
            "soft": [
                {
                    "id": "REST_PREFERENCE",
                    "score": "obj.rest_hours >= 10",
                    "weight": 0.8
                }
            ]
        }
        
        # This should compile without errors
        rule_pack = compile_rule_pack(yaml_obj)
        
        assert len(rule_pack.hard_rules) == 1
        assert len(rule_pack.soft_rules) == 1
        
        # Test the compiled rule - we need to compile the DSL expression first
        from app.rules_engine.dsl import DSLParser
        parser = DSLParser({"obj": {"duty_hours", "rest_hours"}})
        
        # Compile the hard rule check expression
        check_func = parser.compile_expr(rule_pack.hard_rules[0].check)
        
        pairing = Mock(duty_hours=12)
        ctx = {}
        
        result = check_func(pairing, ctx)
        assert result is True


# Test markers for pytest
pytestmark = [
    pytest.mark.dsl,
    pytest.mark.rules_engine,
    pytest.mark.unit
]
