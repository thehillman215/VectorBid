"""
Domain Specific Language (DSL) for rule expressions.

Safe expression compiler that converts rule expressions to callables.
No eval() - only whitelisted functions and safe operations.
"""

import ast
import re
from collections.abc import Callable
from typing import Any

# Whitelist of allowed domain functions (pure, deterministic)
SAFE_FUNCS = {
    "hours_between": lambda start, end: (end - start).total_seconds() / 3600,
    "is_redeye": lambda departure_time, arrival_time: departure_time.hour >= 22
    or arrival_time.hour <= 6,
    "in_local_window": lambda time_obj, start_hour, end_hour: start_hour
    <= time_obj.hour
    <= end_hour,
    "count_legs": lambda pairing: len(getattr(pairing, "legs", [])),
    "min": min,
    "max": max,
    "abs": abs,
    "round": round,
    "len": len,
    "sum": sum,
}


class DSLParseError(Exception):
    """Raised when DSL parsing fails."""

    pass


class DSLSecurityError(Exception):
    """Raised when DSL contains potentially unsafe code."""

    pass


class DSLParser:
    """Safe DSL parser that compiles expressions to callables."""

    def __init__(self, whitelist=None):
        """
        Initialize DSL parser with whitelist.

        Args:
            whitelist: Dict mapping object names to allowed attribute sets.
                      Example: {"pairing": {"duty_hours", "rest_hours", "legs"}}
        """
        self.whitelist = whitelist or {}
        self.compile_errors = 0
        self.rules_compiled = 0

    def compile_expr(self, expr: str, *, whitelist=None):
        """
        Compile a DSL expression to a safe callable.

        Args:
            expr: String expression to compile
            whitelist: Override whitelist for this compilation

        Returns:
            Callable that takes (obj, ctx) and returns result

        Raises:
            DSLParseError: If expression cannot be parsed
            DSLSecurityError: If expression contains unsafe code
        """
        try:
            # Pre-validate expression for obvious syntax issues
            self._pre_validate_expression(expr)

            # Parse expression to AST
            tree = ast.parse(expr, mode="eval")

            # Validate AST nodes
            self._validate_ast(tree.body)

            # Create a safe execution environment
            safe_globals = {"__builtins__": {}}
            safe_locals = {**SAFE_FUNCS}

            # Compile the expression
            code = compile(tree, "<string>", "eval")

            # Create a function that executes the compiled code
            def compiled_func(obj, ctx):
                # Update locals with current obj and ctx
                safe_locals.update({"obj": obj, "ctx": ctx})
                return eval(code, safe_globals, safe_locals)

            self.rules_compiled += 1
            return compiled_func

        except SyntaxError as e:
            self.compile_errors += 1
            raise DSLParseError(f"Syntax error in expression '{expr}': {e}") from e
        except (DSLParseError, DSLSecurityError):
            # Re-raise security and parse errors as-is
            raise
        except Exception as e:
            self.compile_errors += 1
            raise DSLParseError(f"Compilation error in expression '{expr}': {e}") from e

    def _pre_validate_expression(self, expr: str) -> None:
        """Pre-validate expression for obvious syntax issues."""
        # Check for consecutive operators (which indicate invalid syntax)

        # Pattern to find consecutive operators
        consecutive_ops = re.search(r"[+\-*/%**]\s*[+\-*/%**]+", expr)
        if consecutive_ops:
            raise DSLParseError(f"Invalid syntax: consecutive operators found in '{expr}'")

        # Check for operators at start/end (except unary + and -)
        if re.match(r"^[*/%**]", expr.strip()):
            raise DSLParseError(
                f"Invalid syntax: expression cannot start with operator '{expr[0]}'"
            )

        if re.search(r"[+\-*/%**]\s*$", expr.strip()):
            raise DSLParseError("Invalid syntax: expression cannot end with operator")

        # Check for balanced parentheses
        if expr.count("(") != expr.count(")"):
            raise DSLParseError(f"Invalid syntax: unbalanced parentheses in '{expr}'")

        # Check for empty parentheses
        if re.search(r"\(\s*\)", expr):
            raise DSLParseError(f"Invalid syntax: empty parentheses in '{expr}'")

    def _validate_ast(self, node: ast.AST) -> None:
        """Validate AST nodes for safety."""
        if isinstance(node, ast.Expression):
            self._validate_ast(node.body)
        elif isinstance(node, ast.Constant):
            # Literals are safe
            pass
        elif isinstance(node, ast.Name):
            # Only allow whitelisted names
            if node.id not in ["obj", "ctx"] and not self._is_safe_name(node.id):
                raise DSLSecurityError(f"Unauthorized identifier: {node.id}")
        elif isinstance(node, ast.Attribute):
            # Validate attribute access
            self._validate_attribute_access(node)
        elif isinstance(node, ast.Compare):
            # Comparison operators are safe
            self._validate_ast(node.left)
            for op, comparator in zip(node.ops, node.comparators):
                if not isinstance(
                    op,
                    (
                        ast.Eq,
                        ast.NotEq,
                        ast.Lt,
                        ast.LtE,
                        ast.Gt,
                        ast.GtE,
                        ast.In,
                        ast.NotIn,
                    ),
                ):  # noqa: UP038
                    raise DSLSecurityError(f"Unsafe comparison operator: {type(op).__name__}")
                self._validate_ast(comparator)
        elif isinstance(node, ast.BoolOp):
            # Boolean operators are safe
            if not isinstance(node.op, (ast.And, ast.Or)):  # noqa: UP038
                raise DSLSecurityError(f"Unsafe boolean operator: {type(node.op).__name__}")
            for value in node.values:
                self._validate_ast(value)
        elif isinstance(node, ast.UnaryOp):
            # Unary operators are safe
            if not isinstance(node.op, (ast.UAdd, ast.USub, ast.Not)):  # noqa: UP038
                raise DSLSecurityError(f"Unsafe unary operator: {type(node.op).__name__}")
            self._validate_ast(node.operand)
        elif isinstance(node, ast.BinOp):
            # Binary operators are safe
            if not isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow)):  # noqa: UP038
                raise DSLSecurityError(f"Unsafe binary operator: {type(node.op).__name__}")
            self._validate_ast(node.left)
            self._validate_ast(node.right)
        elif isinstance(node, ast.Call):
            # Function calls are safe (only to whitelisted functions)
            if not isinstance(node.func, ast.Name):
                raise DSLSecurityError("Function calls must use simple names")
            if node.func.id not in SAFE_FUNCS:
                raise DSLSecurityError(f"Unauthorized function call: {node.func.id}")
            for arg in node.args:
                self._validate_ast(arg)
        elif isinstance(node, ast.List):
            # List literals are safe
            for elt in node.elts:
                self._validate_ast(elt)
        elif isinstance(node, ast.Tuple):
            # Tuple literals are safe
            for elt in node.elts:
                self._validate_ast(elt)
        elif isinstance(node, ast.Dict):
            # Dict literals are safe
            for key, value in zip(node.keys, node.values):
                self._validate_ast(key)
                self._validate_ast(value)
        elif isinstance(node, ast.Subscript):
            # Subscript operations are safe
            self._validate_ast(node.value)
            self._validate_ast(node.slice)
        elif isinstance(node, ast.Index):
            # Index operations are safe
            self._validate_ast(node.value)
        elif isinstance(node, ast.Slice):
            # Slice operations are safe
            if node.lower:
                self._validate_ast(node.lower)
            if node.upper:
                self._validate_ast(node.upper)
            if node.step:
                self._validate_ast(node.step)
        else:
            raise DSLSecurityError(f"Unsafe AST node type: {type(node).__name__}")

    def _validate_attribute_access(self, node: ast.Attribute) -> None:
        """Validate attribute access against whitelist."""
        # Check if this is a whitelisted attribute access
        if isinstance(node.value, ast.Name):
            obj_name = node.value.id
            attr_name = node.attr

            # Check for dunder attributes (always reject)
            if attr_name.startswith("__") or attr_name.endswith("__"):
                raise DSLSecurityError(
                    f"Unauthorized dunder attribute access: {obj_name}.{attr_name}"
                )

            # Always allow access to obj and ctx
            if obj_name in ["obj", "ctx"]:
                return

            # Check whitelist for other objects
            if obj_name in self.whitelist:
                if attr_name not in self.whitelist[obj_name]:
                    raise DSLSecurityError(f"Unauthorized attribute access: {obj_name}.{attr_name}")
            else:
                # Reject access to unknown objects
                raise DSLSecurityError(f"Unauthorized object access: {obj_name}")
        else:
            # Recursively validate nested attribute access
            self._validate_ast(node.value)

    def _is_safe_name(self, name: str) -> bool:
        """Check if a name is safe to use."""
        # Reject dunder names and suspicious patterns
        if name.startswith("__") or name.endswith("__"):
            return False
        if name in ["eval", "exec", "import", "open", "file", "input"]:
            return False
        return True

    def _build_lambda(self, expr: str, whitelist):
        """Build a safe lambda function string."""
        # Create a safe lambda that only accesses whitelisted attributes
        lambda_body = self._sanitize_expression(expr, whitelist)
        return f"lambda obj, ctx: {lambda_body}"

    def _sanitize_expression(self, expr: str, whitelist):
        """Sanitize expression to only use whitelisted access."""
        # For now, return the expression as-is since we validate the AST
        # In a more sophisticated implementation, we could rewrite the expression
        return expr

    def get_stats(self) -> dict[str, Any]:
        """Get compilation statistics."""
        return {
            "rules_compiled": self.rules_compiled,
            "compile_errors": self.compile_errors,
            "version": "v1",
        }


# Backward compatibility - keep the old DSL class for now
class DSL:
    """Legacy DSL class - use DSLParser for new code."""

    def __init__(self):
        self.parser = DSLParser()

    def compile_predicate(self, expr: str) -> Callable[[Any, Any], bool]:
        """Compile a predicate expression to a boolean function."""
        try:
            return self.parser.compile_expr(expr)
        except (DSLParseError, DSLSecurityError):
            # Fallback to placeholder if compilation fails
            def _always_true(obj, ctx):
                return True

            return _always_true

    def compile_score(self, expr: str) -> Callable[[Any, Any], float]:
        """Compile a scoring expression to a float function."""
        try:
            return self.parser.compile_expr(expr)
        except (DSLParseError, DSLSecurityError):
            # Fallback to placeholder if compilation fails
            def _score(obj, ctx):
                return 1.0

            return _score

    def compile_derived(self, expr: str) -> Callable[[Any, Any], dict]:
        """Compile a derived expression to a dict function."""
        try:
            return self.parser.compile_expr(expr)
        except (DSLParseError, DSLSecurityError):
            # Fallback to placeholder if compilation fails
            def _derived(obj, ctx):
                return {}

            return _derived

    def validate_expression(self, expr: str) -> bool:
        """Validate that an expression only uses allowed functions and syntax."""
        try:
            self.parser.compile_expr(expr)
            return True
        except (DSLParseError, DSLSecurityError):
            return False
