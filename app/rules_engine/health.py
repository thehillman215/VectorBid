"""
Rule pack health monitoring.

Provides status and metrics for rule packs in the health system.
"""

from .models import RulePack


def pack_status(pack: RulePack) -> dict:
    """Get status information for a single rule pack."""
    return {
        "airline": pack.airline,
        "contract_period": pack.contract_period,
        "month": pack.month,  # Backward compatibility
        "base": pack.base,
        "fleet": pack.fleet,
        "hard_rules": len(pack.hard_rules),
        "soft_rules": len(pack.soft_rules),
        "derived_rules": len(pack.derived_rules),
        "version": pack.version,
        "effective_start": pack.effective_start.isoformat() if pack.effective_start else None,
        "effective_end": pack.effective_end.isoformat() if pack.effective_end else None,
    }


def pack_registry_health(packs: list[RulePack]) -> dict:
    """Get overall health status for the rule pack registry."""
    if not packs:
        return {
            "status": "error",
            "message": "No rule packs available",
            "count": 0,
            "coverage": {},
        }

    # Count rules by type
    total_hard = sum(len(p.hard_rules) for p in packs)
    total_soft = sum(len(p.soft_rules) for p in packs)
    total_derived = sum(len(p.derived_rules) for p in packs)

    # Group by airline
    airlines = {}
    for pack in packs:
        if pack.airline not in airlines:
            airlines[pack.airline] = []
        airlines[pack.airline].append(pack.contract_period)

    # Coverage window
    periods = [p.contract_period for p in packs]
    periods.sort()
    coverage_window = f"{periods[0]} to {periods[-1]}" if periods else "none"

    return {
        "status": "ok",
        "count": len(packs),
        "rule_counts": {
            "hard": total_hard,
            "soft": total_soft,
            "derived": total_derived,
        },
        "airlines": airlines,
        "coverage_window": coverage_window,
        "last_updated": "now",  # TODO: track actual last update time
    }


def pack_validation_health(packs: list[RulePack]) -> dict:
    """Get validation health status for rule packs."""
    health_status = {
        "total_packs": len(packs),
        "validation_results": {},
        "overall_status": "ok",
    }

    for pack in packs:
        pack_key = f"{pack.airline}_{pack.contract_period}"

        # Basic validation checks
        validation_checks = {
            "has_hard_rules": len(pack.hard_rules) > 0,
            "has_soft_rules": len(pack.soft_rules) > 0,
            "valid_version": pack.version in ["v1"],  # TODO: expand valid versions
            "has_metadata": bool(pack.metadata),
            "valid_dates": pack.effective_start is not None,
        }

        # Check if all validation checks pass
        all_passed = all(validation_checks.values())

        health_status["validation_results"][pack_key] = {
            "status": "ok" if all_passed else "error",
            "checks": validation_checks,
            "rule_counts": {
                "hard": len(pack.hard_rules),
                "soft": len(pack.soft_rules),
                "derived": len(pack.derived_rules),
            },
        }

        # Update overall status if any pack has issues
        if not all_passed:
            health_status["overall_status"] = "warning"

    return health_status


def dsl_health() -> dict:
    """Get DSL compilation health status."""
    try:
        from .dsl import DSLParser

        # Create a temporary parser to get stats
        parser = DSLParser()
        stats = parser.get_stats()

        return {
            "version": stats["version"],
            "rules_compiled": stats["rules_compiled"],
            "compile_errors": stats["compile_errors"],
            "status": "ok" if stats["compile_errors"] == 0 else "warning",
        }
    except ImportError:
        return {
            "version": "unknown",
            "rules_compiled": 0,
            "compile_errors": 0,
            "status": "error",
            "message": "DSL module not available",
        }
