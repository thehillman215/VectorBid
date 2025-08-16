from typing import Any

from app.models import ContextSnapshot, FeatureBundle, PreferenceSchema


def fuse(ctx: ContextSnapshot, pref: PreferenceSchema, precheck: dict[str, Any], analytics: dict[str, Any], pairings: dict[str, Any]) -> FeatureBundle:
    raise NotImplementedError("Implemented in PR2")
