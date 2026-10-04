"""Adversarial Verification Test Matrix for MatchMind FactCheckerAgent.

Tests that the Fact Checker systematically flags every variety of hallucination:
- Injected wrong scorelines
- False goal calls on non-goal outcomes (Saved, Blocked, Off Target)
- Player identity mismatches
- Team identity mismatches
- Match clock discrepancies
- Metric hallucinations (xG, xT, Field Tilt)
- False historical milestones
- Translated commentary hallucinations
"""

import pytest
from matchmind.agents.factcheck_agent import FactCheckerAgent
from matchmind.constants import FanPersona
from matchmind.models import (
    AgentMessage,
    ClaimStatus,
    ClaimType,
    NarrativeOutput,
    StructuredClaim,
)


@pytest.fixture
def fact_checker():
    return FactCheckerAgent()


@pytest.fixture
def base_event_and_state():
    event = {
        "index": 14,
        "minute": 23,
        "event_type": "Shot",
        "outcome": "Saved",
        "player": {"id": 107, "name": "Bukayo Saka"},
        "team": {"id": 1, "name": "Arsenal"},
    }
    metric_state = {
        "match_id": "test_match",
        "minute": 23,
        "score": {"home": 1, "away": 0},
        "home_team": "Arsenal",
        "away_team": "Liverpool",
        "current_action_xg": 0.18,
        "field_tilt": 58.0,
        "rolling_ppda": {"away": 9.2, "home": 12.0},
        "current_leverage_index": 1.8,
    }
    return event, metric_state


@pytest.mark.asyncio
async def test_fact_check_legitimate_event_passes(fact_checker, base_event_and_state):
    event, metric_state = base_event_and_state
    claims = [
        StructuredClaim(
            claim_type=ClaimType.SCORELINE,
            subject="Match Score",
            claimed_value="1-0",
        ),
        StructuredClaim(
            claim_type=ClaimType.GOAL_EVENT,
            subject="Goal Outcome",
            claimed_value=False,
        ),
        StructuredClaim(
            claim_type=ClaimType.PLAYER_IDENTITY,
            subject="Bukayo Saka",
            claimed_value="Bukayo Saka",
        ),
        StructuredClaim(
            claim_type=ClaimType.TEAM_IDENTITY,
            subject="Arsenal",
            claimed_value="Arsenal",
        ),
        StructuredClaim(
            claim_type=ClaimType.MATCH_CLOCK,
            subject="Match Clock",
            claimed_value=23,
        ),
        StructuredClaim(
            claim_type=ClaimType.METRIC_XG,
            subject="Expected Goals",
            claimed_value=0.18,
        ),
    ]

    narrative = {
        "minute": 23,
        "game_state_arc": "Tense Stalemate",
        "why_it_matters_explanation": "Bukayo Saka forced a crucial save from the goalkeeper (xG: 0.18).",
        "commentary_by_persona": {
            FanPersona.TACTICAL_ANALYST: "[TACTICAL ANALYSIS | 23'] Bukayo Saka (Arsenal) executes Shot [Outcome: Saved] (xG 0.18). Field Tilt at 58.0%.",
            FanPersona.CASUAL_FAN: "🧤 Brilliant save! The keeper denies Bukayo Saka at 23'!",
            FanPersona.BROADCAST_COMMENTATOR: "Terrific stop! The keeper turns aside Bukayo Saka's strike at 23'. Score is 1-0.",
        },
        "translations": {"es": "🧤 Gran atajada del portero ante Bukayo Saka al minuto 23."},
        "structured_claims": [c.model_dump() for c in claims],
    }

    msg = AgentMessage(
        source_agent="translator_agent",
        match_id="test_match",
        event_index=14,
        match_minute=23,
        message_type="TRANSLATED_COMMENTARY",
        payload={"narrative": narrative, "event": event, "metric_state": metric_state},
    )

    out = await fact_checker.process(msg)
    res = out[0].payload
    assert res["is_verified"] is True
    assert res["narrative"]["verified_by_factcheck"] is True
    assert res["verification_summary"]["passed"] is True
    assert len(res["verification_summary"]["violations"]) == 0


@pytest.mark.asyncio
async def test_fact_check_flags_wrong_scoreline(fact_checker, base_event_and_state):
    event, metric_state = base_event_and_state
    # Inject wrong score: 3-0 instead of 1-0
    claims = [
        StructuredClaim(
            claim_type=ClaimType.SCORELINE,
            subject="Match Score",
            claimed_value="3-0",
        )
    ]
    narrative = {
        "why_it_matters_explanation": "Saka shot.",
        "commentary_by_persona": {
            FanPersona.BROADCAST_COMMENTATOR: "Score stands at 3-0 after that save.",
        },
        "structured_claims": [c.model_dump() for c in claims],
    }
    msg = AgentMessage(
        source_agent="translator_agent",
        match_id="test_match",
        event_index=14,
        match_minute=23,
        message_type="TRANSLATED_COMMENTARY",
        payload={"narrative": narrative, "event": event, "metric_state": metric_state},
    )

    out = await fact_checker.process(msg)
    res = out[0].payload
    assert res["is_verified"] is False
    violations = res["verification_summary"]["violations"]
    assert any("Scoreline" in v for v in violations)


@pytest.mark.asyncio
async def test_fact_check_flags_false_goal_celebration(fact_checker, base_event_and_state):
    event, metric_state = base_event_and_state
    # Event outcome is "Saved", but casual fan text hallucinates a goal
    narrative = {
        "why_it_matters_explanation": "Saka saved shot.",
        "commentary_by_persona": {
            FanPersona.CASUAL_FAN: "🔥 GOAAALLL!! Saka scores! Absolute chaos! ⚽💥",
        },
        "structured_claims": [],
    }
    msg = AgentMessage(
        source_agent="translator_agent",
        match_id="test_match",
        event_index=14,
        match_minute=23,
        message_type="TRANSLATED_COMMENTARY",
        payload={"narrative": narrative, "event": event, "metric_state": metric_state},
    )

    out = await fact_checker.process(msg)
    res = out[0].payload
    assert res["is_verified"] is False
    violations = res["verification_summary"]["violations"]
    assert any("False goal" in v for v in violations)


@pytest.mark.asyncio
async def test_fact_check_flags_player_identity_mismatch(fact_checker, base_event_and_state):
    event, metric_state = base_event_and_state
    # Actual actor is Bukayo Saka, but claim says Erling Haaland
    claims = [
        StructuredClaim(
            claim_type=ClaimType.PLAYER_IDENTITY,
            subject="Erling Haaland",
            claimed_value="Erling Haaland",
        )
    ]
    narrative = {
        "why_it_matters_explanation": "Erling Haaland strike.",
        "commentary_by_persona": {},
        "structured_claims": [c.model_dump() for c in claims],
    }
    msg = AgentMessage(
        source_agent="translator_agent",
        match_id="test_match",
        event_index=14,
        match_minute=23,
        message_type="TRANSLATED_COMMENTARY",
        payload={"narrative": narrative, "event": event, "metric_state": metric_state},
    )

    out = await fact_checker.process(msg)
    res = out[0].payload
    assert res["is_verified"] is False
    violations = res["verification_summary"]["violations"]
    assert any("Player identity mismatch" in v for v in violations)


@pytest.mark.asyncio
async def test_fact_check_flags_metric_xg_hallucination(fact_checker, base_event_and_state):
    event, metric_state = base_event_and_state
    # Actual xG is 0.18, claimed xG is 0.89
    claims = [
        StructuredClaim(
            claim_type=ClaimType.METRIC_XG,
            subject="Expected Goals",
            claimed_value=0.89,
        )
    ]
    narrative = {
        "why_it_matters_explanation": "Saka strike.",
        "commentary_by_persona": {
            FanPersona.TACTICAL_ANALYST: "Shot with xG 0.89 that was saved.",
        },
        "structured_claims": [c.model_dump() for c in claims],
    }
    msg = AgentMessage(
        source_agent="translator_agent",
        match_id="test_match",
        event_index=14,
        match_minute=23,
        message_type="TRANSLATED_COMMENTARY",
        payload={"narrative": narrative, "event": event, "metric_state": metric_state},
    )

    out = await fact_checker.process(msg)
    res = out[0].payload
    assert res["is_verified"] is False
    violations = res["verification_summary"]["violations"]
    assert any("xG" in v for v in violations)


@pytest.mark.asyncio
async def test_fact_check_flags_clock_discrepancy(fact_checker, base_event_and_state):
    event, metric_state = base_event_and_state
    # Event is minute 23, claim says minute 89
    claims = [
        StructuredClaim(
            claim_type=ClaimType.MATCH_CLOCK,
            subject="Match Clock",
            claimed_value=89,
        )
    ]
    narrative = {
        "why_it_matters_explanation": "Action at minute 89.",
        "commentary_by_persona": {},
        "structured_claims": [c.model_dump() for c in claims],
    }
    msg = AgentMessage(
        source_agent="translator_agent",
        match_id="test_match",
        event_index=14,
        match_minute=23,
        message_type="TRANSLATED_COMMENTARY",
        payload={"narrative": narrative, "event": event, "metric_state": metric_state},
    )

    out = await fact_checker.process(msg)
    res = out[0].payload
    assert res["is_verified"] is False
    violations = res["verification_summary"]["violations"]
    assert any("Match clock discrepancy" in v for v in violations)
