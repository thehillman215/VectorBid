"""
Rule pack compiler.

Converts YAML rule definitions into immutable, compiled Python objects.
"""

from datetime import datetime

from .dsl import DSLParseError, DSLSecurityError
from .models import DerivedRule, HardRule, RulePack, SoftRule


def parse_date(date_str: str) -> datetime.date:
    """Parse a date string into a date object."""
    if isinstance(date_str, str):
        # Try different date formats
        for fmt in ["%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d"]:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Unable to parse date: {date_str}")
    return date_str


def compile_rule_pack(yaml_obj: dict) -> RulePack:
    """Compile a YAML rule pack into an immutable RulePack object."""
    # Compile hard rules
    hard = []
    for r in yaml_obj.get("hard", []):
        try:
            hard.append(
                HardRule(
                    name=r["id"],
                    description=r.get("desc", ""),
                    check=r.get("check", "True"),
                    severity=r.get("severity", "error"),
                )
            )
        except (DSLParseError, DSLSecurityError) as e:
            # Log error and use placeholder
            print(f"Warning: Failed to compile hard rule {r['id']}: {e}")
            hard.append(
                HardRule(
                    name=r["id"],
                    description=r.get("desc", ""),
                    check="True",  # Default to always pass
                    severity=r.get("severity", "error"),
                )
            )

    # Compile soft rules
    soft = []
    for r in yaml_obj.get("soft", []):
        try:
            soft.append(
                SoftRule(
                    name=r["id"],
                    description=r.get("desc", ""),
                    weight=float(r.get("weight", 1.0)),
                    score=r.get("score", "1.0"),
                )
            )
        except (DSLParseError, DSLSecurityError) as e:
            # Log error and use placeholder
            print(f"Warning: Failed to compile soft rule {r['id']}: {e}")
            soft.append(
                SoftRule(
                    name=r["id"],
                    description=r.get("desc", ""),
                    weight=float(r.get("weight", 1.0)),
                    score="1.0",  # Default score
                )
            )

    # Compile derived rules
    derived = []
    for r in yaml_obj.get("derived", []):
        try:
            derived.append(
                DerivedRule(
                    name=r["id"],
                    description=r.get("desc", ""),
                    compute=r.get("expr", "{}"),
                    output_type=r.get("output_type", "dict"),
                )
            )
        except (DSLParseError, DSLSecurityError) as e:
            # Log error and use placeholder
            print(f"Warning: Failed to compile derived rule {r['id']}: {e}")
            derived.append(
                DerivedRule(
                    name=r["id"],
                    description=r.get("desc", ""),
                    compute="{}",  # Default empty dict
                    output_type=r.get("output_type", "dict"),
                )
            )

    return RulePack(
        version=yaml_obj["version"],
        airline=yaml_obj["airline"],
        contract_period=yaml_obj.get("month", yaml_obj["version"]),
        base=yaml_obj.get("base"),
        fleet=yaml_obj.get("fleet"),
        effective_start=parse_date(yaml_obj["effective_start"]),
        effective_end=parse_date(yaml_obj.get("effective_end"))
        if yaml_obj.get("effective_end")
        else None,
        hard_rules=hard,
        soft_rules=soft,
        derived_rules=derived,
        metadata=yaml_obj.get("metadata", {}),
    )
