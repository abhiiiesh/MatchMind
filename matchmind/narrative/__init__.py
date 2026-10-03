"""Narrative engine package for MatchMind commentary and storytelling."""

from matchmind.narrative.story_arc import StoryArcClassifier
from matchmind.narrative.local_fallback import LocalNarrativeEngine
from matchmind.narrative.personas import PersonaProfile, PERSONA_REGISTRY

__all__ = [
    "StoryArcClassifier",
    "LocalNarrativeEngine",
    "PersonaProfile",
    "PERSONA_REGISTRY",
]
