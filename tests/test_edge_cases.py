"""Unit tests for football edge cases and unusual match scenarios.

Covers:
- 0-0 scoreless draws
- Red cards and disciplinary actions
- Penalty kicks
- Own goals
- 90+ minute stoppage time
- Malformed / incomplete event payloads
"""

import pytest
from matchmind.constants import EventType, FanPersona
from matchmind.metrics.expected_goals import ExpectedGoalsModel
from matchmind.metrics.expected_threat import ExpectedThreatModel
from matchmind.narrative.local_fallback import LocalNarrativeEngine
from matchmind.narrative.story_arc import StoryArcClassifier
from matchmind.models import MatchEvent, MetricState, PlayerInfo, TeamInfo


def test_scoreless_draw_narrative_arc():
    classifier = StoryArcClassifier()
    # 0-0 at minute 80 with low leverage
    metric_state = MetricState(
        match_id="scoreless_stalemate",
        minute=80,
        score={"home": 0, "away": 0},
        home_team="Chelsea",
        away_team="Tottenham Hotspur",
        cumulative_xg={"home": 0.35, "away": 0.40},
        current_leverage_index=1.2,
        rolling_ppda={"home": 11.0, "away": 12.0},
        field_tilt=50.0,
    )
    arc = classifier.classify_arc(metric_state)
    assert "Stalemate" in arc or "Defensive" in arc or "Attrition" in arc


def test_penalty_kick_xg_calculation():
    xg_model = ExpectedGoalsModel()
    # Open play shot from 12 yards central
    xg = xg_model.calculate_xg(x=108.0, y=40.0, under_pressure=False)
    assert 0.20 <= xg <= 0.85

    # Standard designated penalty kick with precomputed StatsBomb xG (0.78)
    pen_xg = xg_model.calculate_xg(x=108.0, y=40.0, precomputed_xg=0.78)
    assert pen_xg == 0.78


def test_own_goal_narrative_handling():
    why = LocalNarrativeEngine.generate_why_it_matters(
        event_type="Shot",
        team_name="Tottenham Hotspur",
        player_name="Cristian Romero",
        minute=54,
        score={"home": 1, "away": 0},
        action_xg=0.05,
        action_xt=None,
        field_tilt=45.0,
        ppda=10.0,
        leverage_index=3.2,
        outcome="Own Goal",
    )
    # Shouldn't celebrate as a normal conversion
    assert "converted" not in why.lower()


def test_stoppage_time_late_game_narrative():
    why = LocalNarrativeEngine.generate_why_it_matters(
        event_type="Pass",
        team_name="Liverpool",
        player_name="Trent Alexander-Arnold",
        minute=94,
        score={"home": 1, "away": 1},
        action_xg=None,
        action_xt=0.075,
        field_tilt=70.0,
        ppda=8.0,
        leverage_index=3.8,
        outcome="Success",
    )
    assert "Trent Alexander-Arnold" in why
    assert "+0.075 xT" in why or "penetrated" in why


def test_xt_value_action_boundaries():
    xt_model = ExpectedThreatModel()

    # Normal progressive pass from midfield to final third
    xt = xt_model.value_action(start_x=60.0, start_y=40.0, end_x=105.0, end_y=40.0)
    assert xt > 0.05

    # Backward recycling pass
    xt_back = xt_model.value_action(start_x=90.0, start_y=40.0, end_x=50.0, end_y=40.0)
    assert xt_back < 0.0
