from typing import List
from app.models import FeatureBundle, CandidateSchedule, StrategyDirectives
def propose_strategy(bundle: FeatureBundle, topk: List[CandidateSchedule]) -> StrategyDirectives:
    raise NotImplementedError("Implemented in PR2")
