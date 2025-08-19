"""
Rule pack resolver.

Finds the most specific rule pack for a given airline/month/base/fleet combination.
"""

from .models import RulePack


class PackResolver:
    """Resolves rule packs based on airline, month, base, and fleet."""

    def __init__(self, registry: list[RulePack]):
        self.registry = registry

    def resolve(
        self, airline: str, month: str, base: str = None, fleet: str = None
    ) -> RulePack:
        """Find the most specific rule pack available."""
        # Find candidates matching airline and month
        candidates = [
            p for p in self.registry if p.airline == airline and p.month == month
        ]

        if candidates:
            # Filter candidates by base/fleet compatibility
            compatible_candidates = []
            for p in candidates:
                # Pack is compatible if:
                # 1. Base matches or pack has no base (general)
                # 2. Fleet matches or pack has no fleet (general)
                base_compatible = (p.base is None) or (p.base == base) or (base is None)
                fleet_compatible = (
                    (p.fleet is None) or (p.fleet == fleet) or (fleet is None)
                )

                if base_compatible and fleet_compatible:
                    compatible_candidates.append(p)

            if compatible_candidates:
                # Sort by specificity: base+fleet > base > fleet > general
                def specificity_key(p: RulePack) -> tuple[bool, bool]:
                    return (p.base is not None, p.fleet is not None)

                compatible_candidates.sort(key=specificity_key, reverse=True)
                return compatible_candidates[0]

        # Fallback to latest pack <= month (lexicographic compare ok for YYYY.MM)
        candidates = [
            p for p in self.registry if p.airline == airline and p.month <= month
        ]
        candidates.sort(key=lambda p: p.month, reverse=True)

        if not candidates:
            raise LookupError(f"No rule pack found for {airline} {month}")

        return candidates[0]

    @staticmethod
    def enforce_effective_dates(pack: RulePack, bid_month: str) -> bool:
        """Check if bid month is within pack's effective window."""
        # TODO: Implement exact month/date comparison as needed
        # For now, basic string comparison
        if pack.effective_end and bid_month > pack.effective_end:
            return False
        if bid_month < pack.month:  # Can't use future rules for past months
            return False
        return True

    def get_available_packs(self, airline: str = None) -> list[RulePack]:
        """Get list of available rule packs, optionally filtered by airline."""
        if airline:
            return [p for p in self.registry if p.airline == airline]
        return self.registry.copy()

    def get_pack_coverage(self) -> dict:
        """Get coverage information for all rule packs."""
        coverage = {}
        for pack in self.registry:
            key = f"{pack.airline}_{pack.month}"
            if key not in coverage:
                coverage[key] = {
                    "airline": pack.airline,
                    "month": pack.month,
                    "base": pack.base,
                    "fleet": pack.fleet,
                    "effective_start": pack.effective_start,
                    "effective_end": pack.effective_end,
                    "rule_counts": {
                        "hard": len(pack.hard_rules),
                        "soft": len(pack.soft_rules),
                        "derived": len(pack.derived_rules),
                    },
                }
        return coverage
