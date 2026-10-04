"""Unit tests for LocalNarrativeEngine outcome-based language branching."""

import pytest
from matchmind.constants import FanPersona
from matchmind.narrative.local_fallback import LocalNarrativeEngine


def test_goal_outcome_uses_converted_and_goal_celebration():
    why = LocalNarrativeEngine.generate_why_it_matters(
        event_type="Shot",
        team_name="Arsenal",
        player_name="Bukayo Saka",
        minute=14,
        score={"home": 1, "away": 0},
        action_xg=0.45,
        action_xt=None,
        field_tilt=60.0,
        ppda=10.0,
        leverage_index=2.5,
        outcome="Goal",
    )
    assert "converted" in why.lower()

    casual = LocalNarrativeEngine.generate_persona_commentary(
        persona=FanPersona.CASUAL_FAN,
        event_type="Shot",
        team_name="Arsenal",
        player_name="Bukayo Saka",
        minute=14,
        score={"home": 1, "away": 0},
        action_xg=0.45,
        field_tilt=60.0,
        ppda=10.0,
        why_it_matters=why,
        outcome="Goal",
    )
    assert "GOAAALLL" in casual or "scores" in casual.lower()


def test_saved_outcome_never_uses_converted():
    why = LocalNarrativeEngine.generate_why_it_matters(
        event_type="Shot",
        team_name="Liverpool",
        player_name="Mohamed Salah",
        minute=28,
        score={"home": 0, "away": 0},
        action_xg=0.06,  # Low xG shot
        action_xt=None,
        field_tilt=50.0,
        ppda=11.0,
        leverage_index=1.5,
        outcome="Saved",
    )
    assert "converted" not in why.lower()
    assert "save" in why.lower()

    casual = LocalNarrativeEngine.generate_persona_commentary(
        persona=FanPersona.CASUAL_FAN,
        event_type="Shot",
        team_name="Liverpool",
        player_name="Mohamed Salah",
        minute=28,
        score={"home": 0, "away": 0},
        action_xg=0.06,
        field_tilt=50.0,
        ppda=11.0,
        why_it_matters=why,
        outcome="Saved",
    )
    assert "GOAAALLL" not in casual
    assert "save" in casual.lower() or "denies" in casual.lower()


def test_blocked_outcome_never_uses_converted():
    why = LocalNarrativeEngine.generate_why_it_matters(
        event_type="Shot",
        team_name="Arsenal",
        player_name="Gabriel Martinelli",
        minute=35,
        score={"home": 1, "away": 0},
        action_xg=0.22,
        action_xt=None,
        field_tilt=55.0,
        ppda=10.5,
        leverage_index=1.8,
        outcome="Blocked",
    )
    assert "converted" not in why.lower()
    assert "blocked" in why.lower()


def test_off_target_outcome_never_uses_converted():
    why = LocalNarrativeEngine.generate_why_it_matters(
        event_type="Shot",
        team_name="Manchester City",
        player_name="Erling Haaland",
        minute=52,
        score={"home": 1, "away": 1},
        action_xg=0.15,
        action_xt=None,
        field_tilt=65.0,
        ppda=8.5,
        leverage_index=2.0,
        outcome="Off Target",
    )
    assert "converted" not in why.lower()
    assert "off target" in why.lower() or "attempted" in why.lower()


def test_pass_xt_progressive_vs_recycling():
    progressive_why = LocalNarrativeEngine.generate_why_it_matters(
        event_type="Pass",
        team_name="Arsenal",
        player_name="Martin Ødegaard",
        minute=22,
        score={"home": 0, "away": 0},
        action_xg=None,
        action_xt=0.082,  # High progressive threat
        field_tilt=55.0,
        ppda=12.0,
        leverage_index=1.2,
        outcome="Success",
    )
    assert "penetrated multiple defensive layers" in progressive_why
    assert "+0.082 xT" in progressive_why

    recycling_why = LocalNarrativeEngine.generate_why_it_matters(
        event_type="Pass",
        team_name="Arsenal",
        player_name="Declan Rice",
        minute=24,
        score={"home": 0, "away": 0},
        action_xg=None,
        action_xt=-0.035,  # Backward recycling pass
        field_tilt=55.0,
        ppda=8.5,
        leverage_index=1.2,
        outcome="Success",
    )
    assert "recycling" in recycling_why.lower() or "reset possession" in recycling_why.lower()
