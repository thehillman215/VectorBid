"""
Rule pack validator.

Enforces hard constraints at three checkpoints: inputs, schedule, and export.
"""

from typing import Any

from .models import RulePack, ScoreBreakdown, Violation


class RulePackValidator:
    """Validates objects against compiled rule packs."""

    def __init__(self, pack: RulePack, context: dict):
        self.pack = pack
        self.ctx = context

    def validate_inputs(self, preferences: dict) -> list[Violation]:
        """Validate pilot preferences against hard constraints."""
        return self._run_hard(preferences, path="/preferences")

    def validate_schedule(self, candidate: Any) -> list[Violation]:
        """Validate a schedule candidate against hard constraints."""
        return self._run_hard(candidate, path="/schedule")

    def validate_export(self, bid_layers: dict) -> list[Violation]:
        """Validate bid layers before export."""
        return self._run_hard(bid_layers, path="/export")

    def _run_hard(self, obj: Any, path: str) -> list[Violation]:
        """Run all hard rules against an object."""
        violations: list[Violation] = []

        for rule in self.pack.hard_rules:
            try:
                ok = rule.predicate(obj, self.ctx)
            except Exception:
                # If rule evaluation fails, treat as violation
                ok = False

            if not ok:
                violations.append(
                    Violation(
                        rule_id=rule.id,
                        severity=rule.severity,
                        message=rule.message,
                        path=path,
                        data_excerpt=None,  # TODO: extract relevant data
                        fix_hint="Adjust preference or remove item",
                        ctx_id=self.ctx.get("ctx_id"),
                        pack_version=f"{self.pack.airline}/{self.pack.month}",
                    )
                )

        return violations


def score_schedule(pack: RulePack, obj: Any, ctx: dict) -> ScoreBreakdown:
    """Score an object using soft rules."""
    components = {}

    for rule in pack.soft_rules:
        try:
            # Apply bounds if specified
            score = max(0.0, min(1.0, rule.score(obj, ctx)) * rule.weight)
            if rule.bounds:
                score = max(rule.bounds[0], min(rule.bounds[1], score))
            components[rule.id] = score
        except Exception:
            # If scoring fails, assign 0
            components[rule.id] = 0.0

    total = sum(components.values())
    return ScoreBreakdown(total=total, components=components)
