from typing import Dict, Any, List
from app.models import ContextSnapshot
def estimate_success_prob(filters: List[Dict[str, Any]], ctx: ContextSnapshot, analytics: Dict[str, Any]) -> float:
    raise NotImplementedError("Implemented in PR2")
