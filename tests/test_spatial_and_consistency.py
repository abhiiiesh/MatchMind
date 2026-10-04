"""Deterministic tests for spatial analytics filtering and replay timeline state consistency."""

import pytest
from matchmind.constants import EventType
from matchmind.models import MatchEvent, PlayerInfo, TeamInfo
from matchmind.metrics.spatial_analytics import SpatialAnalyticsEngine
from matchmind.playback.replay_session import ReplaySession
from matchmind.agents.metrics_agent import MetricsAgent


def test_pressure_zones_strictly_filters_defensive_actions():
    """Verifies that passes under pressure are NOT falsely classified as defensive pressing actions."""
    engine = SpatialAnalyticsEngine()
    team_a = TeamInfo(id=1, name="Arsenal")
    team_b = TeamInfo(id=2, name="Liverpool")
    player_att = PlayerInfo(id=10, name="Bukayo Saka")
    player_def = PlayerInfo(id=20, name="Virgil van Dijk")

    events = [
        # 1. Genuine high press by defending team at x=85.0
        MatchEvent(
            index=1,
            minute=10,
            second=0,
            match_id="test_match",
            event_type=EventType.PRESSURE,
            team=team_a,
            player=player_att,
            start_x=85.0,
            start_y=35.0,
            under_pressure=False,
            outcome="Success",
        ),
        # 2. Genuine tackle/duel in middle third at x=55.0
        MatchEvent(
            index=2,
            minute=10,
            second=15,
            match_id="test_match",
            event_type=EventType.DUEL,
            team=team_b,
            player=player_def,
            start_x=55.0,
            start_y=40.0,
            under_pressure=False,
            outcome="Success",
        ),
        # 3. Ordinary PASS made under pressure at x=88.0 (attacking team in possession)
        # MUST NOT be counted as a defensive pressure action!
        MatchEvent(
            index=3,
            minute=10,
            second=30,
            match_id="test_match",
            event_type=EventType.PASS,
            team=team_a,
            player=player_att,
            start_x=88.0,
            start_y=20.0,
            under_pressure=True,
            outcome="Success",
        ),
        # 4. Ordinary SHOT taken under pressure at x=92.0
        # MUST NOT be counted as a defensive pressure action!
        MatchEvent(
            index=4,
            minute=10,
            second=45,
            match_id="test_match",
            event_type=EventType.SHOT,
            team=team_a,
            player=player_att,
            start_x=92.0,
            start_y=38.0,
            under_pressure=True,
            outcome="Saved",
        ),
        # 5. Defensive interception in defensive third at x=25.0
        MatchEvent(
            index=5,
            minute=11,
            second=0,
            match_id="test_match",
            event_type=EventType.INTERCEPTION,
            team=team_b,
            player=player_def,
            start_x=25.0,
            start_y=50.0,
            under_pressure=False,
            outcome="Success",
        ),
    ]

    result = engine.compute_pressure_zones(events)

    # Only events 1, 2, and 5 are defensive actions! Total pressures must be 3, NOT 5!
    assert result["total_pressures"] == 3
    assert result["actions_under_pressure_faced"] == 2  # Events 3 and 4 were faced under pressure
    assert result["breakdown"]["high_press_attacking_third"] == 1  # Only Event 1 (Pressure at x=85.0)
    assert result["breakdown"]["mid_block_middle_third"] == 1      # Only Event 2 (Tackle at x=55.0)
    assert result["breakdown"]["low_block_defensive_third"] == 1   # Only Event 5 (Interception at x=25.0)

    # high_press_actions must only contain Event 1 (Pressure), NEVER the Pass or Shot
    assert len(result["high_press_actions"]) == 1
    assert result["high_press_actions"][0]["type"] == EventType.PRESSURE
    assert result["high_press_actions"][0]["player"] == "Bukayo Saka"
    assert result["high_press_actions"][0]["x"] == 85.0


def test_replay_session_score_progression_consistency():
    """Verifies that replay timeline score strictly reflects the score up to that minute, not the final score."""
    session = ReplaySession()
    session.load_match("arsenal_liverpool_2024")

    # Initial state (minute 0): score must be 0-0, while final_score is 3-1
    timeline_0 = session.get_timeline_info()
    assert timeline_0["final_score"] == {"home": 3, "away": 1}
    assert timeline_0["current_score"] == {"home": 0, "away": 0}

    # At minute 11 (before Saka's 14' goal): current_score must be 0-0!
    # (Fixes the issue where live state and replay disagreed at 11')
    session.current_index = next(i for i, ev in enumerate(session.events) if ev.minute == 11)
    timeline_11 = session.get_timeline_info()
    assert timeline_11["current_score"] == {"home": 0, "away": 0}
    assert timeline_11["final_score"] == {"home": 3, "away": 1}

    # At minute 20 (after Saka's 14' goal, before 45' OG): current_score must be 1-0!
    session.current_index = next(i for i, ev in enumerate(session.events) if ev.minute == 20)
    timeline_20 = session.get_timeline_info()
    assert timeline_20["current_score"] == {"home": 1, "away": 0}

    # At minute 50 (after Gabriel 45' OG, before Martinelli 67'): current_score must be 1-1!
    session.current_index = next(i for i, ev in enumerate(session.events) if ev.minute == 50)
    timeline_50 = session.get_timeline_info()
    assert timeline_50["current_score"] == {"home": 1, "away": 1}

    # At minute 75 (after Martinelli 67'): current_score must be 2-1!
    session.current_index = next(i for i, ev in enumerate(session.events) if ev.minute == 75)
    timeline_75 = session.get_timeline_info()
    assert timeline_75["current_score"] == {"home": 2, "away": 1}

    # At minute 95 (after Trossard 92'): current_score must be 3-1!
    session.current_index = len(session.events) - 1
    timeline_end = session.get_timeline_info()
    assert timeline_end["current_score"] == {"home": 3, "away": 1}


def test_metrics_agent_clean_reset_on_match_switch():
    """Verifies that switching matches resets MetricsAgent internal rolling state completely."""
    agent = MetricsAgent()
    agent.score = {"home": 2, "away": 1}
    agent.cumulative_xg = {"home": 2.45, "away": 0.82}
    agent.active_match_id = "old_match"

    # Reset
    agent.reset("new_match")
    assert agent.active_match_id == "new_match"
    assert agent.score == {"home": 0, "away": 0}
    assert agent.cumulative_xg == {"home": 0.0, "away": 0.0}
    assert agent.cumulative_xt == {"home": 0.0, "away": 0.0}
    assert agent.pass_counts == {"home": 0, "away": 0}
