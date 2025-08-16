from typing import List
from app.models import CandidateSchedule, BidLayerArtifact, FeatureBundle
def candidates_to_layers(topk: List[CandidateSchedule], bundle: FeatureBundle) -> BidLayerArtifact:
    raise NotImplementedError("Implemented in PR2")
