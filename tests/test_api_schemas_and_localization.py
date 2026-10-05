"""Deterministic tests for OpenAPI schemas and multilingual sports localization consistency."""

import pytest
from fastapi.testclient import TestClient
from matchmind.delivery.rest_api import (
    app,
    MatchCatalogResponse,
    TimelineInfoResponse,
    PressureZonesResponse,
    HeatmapResponse,
    PassNetworkResponse,
    SeekResponse,
)
from matchmind.agents.translator_agent import SportsLocalizationEngine


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_api_matches_schema_matches_response_model(client):
    """Verifies that /api/matches conforms to MatchCatalogResponse schema."""
    res = client.get("/api/matches")
    assert res.status_code == 200
    data = res.json()
    validated = MatchCatalogResponse(**data)
    assert len(validated.matches) >= 3
    assert any(m.match_id == "arsenal_liverpool_2024" for m in validated.matches)


def test_api_timeline_schema_and_current_score(client):
    """Verifies that /api/match/{id}/timeline conforms to TimelineInfoResponse and includes current_score."""
    res = client.get("/api/match/arsenal_liverpool_2024/timeline")
    assert res.status_code == 200
    data = res.json()
    validated = TimelineInfoResponse(**data)
    assert validated.match_id == "arsenal_liverpool_2024"
    assert validated.final_score == {"home": 3, "away": 1}
    assert validated.current_score is not None
    assert len(validated.key_moments) >= 4


def test_api_pressure_zones_schema_and_breakdown_consistency(client):
    """Verifies that /api/match/{id}/spatial/pressure_zones conforms to PressureZonesResponse."""
    res = client.get("/api/match/arsenal_liverpool_2024/spatial/pressure_zones")
    assert res.status_code == 200
    data = res.json()
    validated = PressureZonesResponse(**data)
    bd = validated.breakdown
    assert bd.high_press_attacking_third + bd.mid_block_middle_third + bd.low_block_defensive_third == validated.total_pressures
    for action in validated.high_press_actions:
        assert action.x >= 80.0
        assert action.type.lower() in [
            "pressure", "tackle", "interception", "foul committed", "duel", "ball recovery", "block", "counterpress"
        ]


def test_api_seek_schema_and_synced_context(client):
    """Verifies that /api/match/{id}/seek returns seeked event, synced metric state, and narrative."""
    res = client.post(
        "/api/match/arsenal_liverpool_2024/seek",
        json={"target_minute": 14},
    )
    assert res.status_code == 200
    data = res.json()
    validated = SeekResponse(**data)
    assert validated.status == "seek_complete"
    assert validated.event is not None
    assert validated.metric_state is not None
    assert validated.narrative is not None
    assert validated.timeline.current_score is not None


def test_sports_localization_engine_spanish():
    """Verifies authentic Spanish localization across distinct outcome phrases."""
    phrase_goal = "🔥 GOAAALLL!! Bukayo Saka scores! Absolute chaos at 14'! What a moment for Arsenal fans! ⚽💥"
    es_goal = SportsLocalizationEngine.translate_phrase(phrase_goal, "es")
    assert "¡GOLAÇO TOTAL!" in es_goal
    assert "¡Qué momento inolvidable para la hinchada de Arsenal !" in es_goal

    phrase_save = "🧤 Brilliant save! The keeper denies Bukayo Saka at 14'! Heart in mouth moment for Arsenal supporters!"
    es_save = SportsLocalizationEngine.translate_phrase(phrase_save, "es")
    assert "¡Parada colosal! El arquero le niega el gol a Bukayo Saka" in es_save
    assert "¡Momento de máxima tensión para la afición de Arsenal !" in es_save

    phrase_block = "🛡️ Massive block! Bukayo Saka shoots but it's charged down at 14'!"
    es_block = SportsLocalizationEngine.translate_phrase(phrase_block, "es")
    assert "¡Bloqueo heroico!" in es_block


def test_sports_localization_engine_hindi():
    """Verifies authentic Hindi localization across distinct outcome phrases."""
    phrase = "🔥 GOAAALLL!! Bukayo Saka scores! What a moment for Arsenal fans! ⚽💥"
    hi = SportsLocalizationEngine.translate_phrase(phrase, "hi")
    assert "शानदार गोल!!" in hi
    assert "समर्थकों के लिए क्या ऐतिहासिक क्षण है!" in hi


def test_simulation_uses_selected_fixture_teams(client):
    """Verifies that simulation for City vs Chelsea seeds correct teams in match state."""
    res = client.post("/api/match/mancity_chelsea_2024/simulate?source=synthetic&events_count=10&delay_seconds=0.05")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "simulation_started"
    assert data["match_id"] == "mancity_chelsea_2024"

    state_res = client.get("/api/match/mancity_chelsea_2024/state")
    assert state_res.status_code == 200
    state_data = state_res.json()
    assert state_data["home_team"] == "Manchester City"
    assert state_data["away_team"] == "Chelsea"


def test_match_state_synchronized_with_selected_and_seeked_fixture(client):
    """Verifies that match state is synchronized with replay selection and seek position."""
    # 1. Select match
    sel_res = client.post("/api/match/mancity_chelsea_2024/select")
    assert sel_res.status_code == 200
    state_res = client.get("/api/match/mancity_chelsea_2024/state")
    assert state_res.status_code == 200
    state = state_res.json()
    assert state["home_team"] == "Manchester City"
    assert state["away_team"] == "Chelsea"

    # 2. Seek to moment m2_42 (Chelsea goal at 42')
    seek_res = client.post(
        "/api/match/mancity_chelsea_2024/seek",
        json={"moment_id": "m2_42"},
    )
    assert seek_res.status_code == 200
    seek_data = seek_res.json()
    assert seek_data["metric_state"]["score"] == {"home": 0, "away": 1}
    assert seek_data["metric_state"]["home_team"] == "Manchester City"
    assert seek_data["metric_state"]["away_team"] == "Chelsea"

    # 3. Query state endpoint directly and verify it reflects the seeked instant
    state_after_seek = client.get("/api/match/mancity_chelsea_2024/state").json()
    assert state_after_seek["home_team"] == "Manchester City"
    assert state_after_seek["away_team"] == "Chelsea"
    assert state_after_seek["score"] == {"home": 0, "away": 1}

    # 4. Verify multilingual translations in seek narrative
    narrative = seek_data["narrative"]
    assert "translations" in narrative
    assert "es" in narrative["translations"]
    assert len(narrative["translations"]["es"]) > 0
    assert "translations_by_persona" in narrative


def test_historical_rag_has_city_chelsea_rivalry_and_profiles(client):
    """Verifies that Historical RAG provides profiles and rivalry records for City and Chelsea."""
    riv_res = client.get("/api/rag/rivalry/Manchester City/Chelsea")
    assert riv_res.status_code == 200
    riv_data = riv_res.json()
    assert "rivalry" in riv_data
    assert "Manchester City" in riv_data["home_team"]

    p1_res = client.get("/api/rag/player/Erling Haaland")
    assert p1_res.status_code == 200
    assert p1_res.json()["profile"]["team"] == "Manchester City"

    p2_res = client.get("/api/rag/player/Cole Palmer")
    assert p2_res.status_code == 200
    assert p2_res.json()["profile"]["team"] == "Chelsea"
