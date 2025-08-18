from typing import Any

from app.models import ContextSnapshot


def estimate_success_prob(
    filters: list[dict[str, Any]], ctx: ContextSnapshot, analytics: dict[str, Any]
) -> float:
    raise NotImplementedError("Implemented in PR2")
