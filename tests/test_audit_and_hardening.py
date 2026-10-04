"""Unit tests verifying audit and hardening fixes:
1. Replay own goal player attribution (Gabriel Magalhães, not Joe Gomez) and 45' 1st half period.
2. OBS Overlay parameter validation and sanitization against script injection.
3. Fact Checker strict grounding: missing evidence marks claims UNVERIFIED; milestone mismatch triggers VIOLATION.
4. Cosmos DB relevance query abstraction and storage type naming.
"""

import pytest
from fastapi.testclient import TestClient

from matchmind.agents.factcheck_agent import FactCheckerAgent
from matchmind.constants import FanPersona
from matchmind.context.repository import CosmosVectorRepository, LocalJsonRepository
from matchmind.delivery.rest_api import app
from matchmind.models import (
    AgentMessage,
    ClaimStatus,
    ClaimType,
    StructuredClaim,
)
from matchmind.playback.replay_session import ReplaySession


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.asyncio
async def test_replay_own_goal_attribution_and_period():
    """Verify that the 45' Gabriel Magalhães own goal attributes to Gabriel and period 1 (1st Half)."""
    session = ReplaySession()
    summary = session.load_match("arsenal_liverpool_2024")
    assert summary is not None

    # Directly seek the m1_45 key moment
    ev = await session.seek_to_moment("m1_45")
    assert ev is not None
    assert ev.minute == 45
    # Must correctly identify Gabriel Magalhães from Arsenal's squad even though goal is credited to Liverpool
    assert ev.player is not None
    assert "Gabriel" in ev.player.name
    assert ev.player.name == "Gabriel Magalhães"
    # Period must be 1 (1st Half), NOT 2 (2nd Half)
    assert ev.period == 1

    timeline_info = session.get_timeline_info()
    assert timeline_info["current_period"] == 1
    assert timeline_info["current_minute"] == 45


def test_obs_overlay_security_and_escaping(client):
    """Verify that /overlay validates inputs and sanitizes parameters against XSS."""
    # 1. Clean parameters work
    res = client.get("/overlay?match_id=arsenal_liverpool_2024&persona=tactical_analyst&lang=es")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    body = res.text
    # Parameters must be stored in data attributes, not raw string interpolation inside script
    assert 'data-match-id="arsenal_liverpool_2024"' in body
    assert 'data-persona="tactical_analyst"' in body
    assert 'data-lang="es"' in body

    # 2. Malicious match_id with script tags or quote escapes is rejected with 400
    bad_res = client.get('/overlay?match_id=bad"<script>alert(1)</script>')
    assert bad_res.status_code == 400

    # 3. Invalid persona falls back to default safely
    fallback_res = client.get("/overlay?match_id=demo_match&persona=invalid_hacker_mode&lang=en")
    assert fallback_res.status_code == 200
    assert 'data-persona="casual_fan"' in fallback_res.text


@pytest.mark.asyncio
async def test_fact_check_missing_telemetry_marks_unverified():
    """Verify that claims with missing ground-truth telemetry become UNVERIFIED, not VERIFIED."""
    fact_checker = FactCheckerAgent()
    event = {
        "index": 1,
        "minute": 10,
        "event_type": "Pass",
        "outcome": "Success",
        "player": {"id": 101, "name": "Martin Ødegaard"},
        "team": {"id": 1, "name": "Arsenal"},
    }
    # Telemetry has NO xG and NO xT
    metric_state = {
        "match_id": "test_m",
        "minute": 10,
        "score": {"home": 0, "away": 0},
        "home_team": "Arsenal",
        "away_team": "Liverpool",
        "current_action_xg": None,  # Missing
        "current_action_xt": None,  # Missing
    }

    claims = [
        StructuredClaim(
            claim_type=ClaimType.METRIC_XG,
            subject="Expected Goals",
            claimed_value=0.25,
        ),
        StructuredClaim(
            claim_type=ClaimType.METRIC_XT,
            subject="Expected Threat",
            claimed_value=0.04,
        ),
    ]

    verified_claims, violations = fact_checker._verify_structured_claims(
        claims=claims,
        event=event,
        metric_state=metric_state,
        historical_context=None,
    )

    # Both claims must be marked UNVERIFIED
    xg_claim = next(c for c in verified_claims if c.claim_type == ClaimType.METRIC_XG)
    xt_claim = next(c for c in verified_claims if c.claim_type == ClaimType.METRIC_XT)
    assert xg_claim.status == ClaimStatus.UNVERIFIED
    assert xt_claim.status == ClaimStatus.UNVERIFIED
    assert "unavailable" in xg_claim.details.lower()
    assert "unavailable" in xt_claim.details.lower()


@pytest.mark.asyncio
async def test_fact_check_milestone_mismatch_flags_violation():
    """Verify that milestone claim must match the specific milestone record in context."""
    fact_checker = FactCheckerAgent()
    event = {
        "index": 2,
        "minute": 50,
        "event_type": "Goal",
        "outcome": "Goal",
        "player": {"id": 109, "name": "Bukayo Saka"},
        "team": {"id": 1, "name": "Arsenal"},
    }
    metric_state = {
        "match_id": "test_m",
        "minute": 50,
        "score": {"home": 1, "away": 0},
        "home_team": "Arsenal",
        "away_team": "Liverpool",
    }
    # Historical context contains milestone for Havertz, not Saka
    historical_context = {
        "has_milestone": True,
        "milestone_alert": "Kai Havertz 50th Premier League Appearance",
    }

    # Claim asserts Saka scored his 100th goal
    claims = [
        StructuredClaim(
            claim_type=ClaimType.HISTORICAL_MILESTONE,
            subject="Bukayo Saka",
            claimed_value="Bukayo Saka 100th Premier League Goal",
        )
    ]

    verified_claims, violations = fact_checker._verify_structured_claims(
        claims=claims,
        event=event,
        metric_state=metric_state,
        historical_context=historical_context,
    )

    ms_claim = verified_claims[0]
    assert ms_claim.status == ClaimStatus.VIOLATION
    assert len(violations) > 0
    assert "mismatch" in ms_claim.details.lower()


def test_cosmos_repository_search_and_naming():
    """Verify CosmosVectorRepository storage type naming and fallback search execution."""
    local_repo = LocalJsonRepository()
    cosmos_repo = CosmosVectorRepository(fallback_repo=local_repo)

    # When credentials not configured, storage type reflects fallback
    assert cosmos_repo.get_storage_type() == "local_historical_rag_cosmos_fallback"

    # Search with keyword delegates gracefully to relevance search
    results = cosmos_repo.vector_search("Saka Arsenal", top_k=2)
    assert isinstance(results, list)
    assert len(results) > 0
    assert any("Saka" in str(r) for r in results)
