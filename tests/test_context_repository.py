"""Unit tests for HistoricalContextRepository and HistoricalRAGEngine."""

import pytest
from matchmind.context.rag_engine import HistoricalRAGEngine
from matchmind.context.repository import (
    HistoricalContextRepository,
    LocalJsonRepository,
    get_context_repository,
)


@pytest.fixture
def repo():
    return LocalJsonRepository()


@pytest.fixture
def rag_engine(repo):
    return HistoricalRAGEngine(repository=repo)


def test_local_repository_initialization(repo):
    assert isinstance(repo, HistoricalContextRepository)
    assert repo.get_storage_type() == "local_json"
    assert len(repo.player_profiles) > 0
    assert len(repo.team_records) > 0
    assert len(repo.rivalries) > 0


def test_player_lookup_exact_and_fuzzy(repo):
    # Exact lookup
    saka = repo.get_player("Bukayo Saka")
    assert saka is not None
    assert saka.get("team") == "Arsenal"
    assert "milestones" in saka

    # Fuzzy lookup with just last name
    salah = repo.get_player("Salah")
    assert salah is not None
    assert "Mohamed Salah" in salah.get("name", "Mohamed Salah")

    # Non-existent player
    unknown = repo.get_player("NonExistentPlayerXYZ")
    assert unknown is None


def test_team_record_lookup(repo):
    arsenal_rec = repo.get_team_record("Arsenal")
    assert arsenal_rec is not None
    assert "historical_trends" in arsenal_rec

    liverpool_rec = repo.get_team_record("Liverpool")
    assert liverpool_rec is not None


def test_rivalry_lookup(repo):
    rivalry = repo.get_rivalry("Arsenal", "Liverpool")
    assert rivalry is not None
    assert "historical_narrative" in rivalry

    # Reversed order should still resolve
    rivalry_rev = repo.get_rivalry("Liverpool", "Arsenal")
    assert rivalry_rev is not None


def test_vector_search_keyword_ranking(repo):
    results = repo.vector_search("Salah goals Liverpool", top_k=2)
    assert len(results) > 0
    # First result should relate to Salah or Liverpool
    first = results[0]
    assert "Salah" in first["name"] or "Liverpool" in first["name"]


def test_rag_engine_retrieve_context(rag_engine):
    ctx = rag_engine.retrieve_context(
        player_name="Bukayo Saka",
        team_name="Arsenal",
        opponent_name="Liverpool",
        event_type="Shot",
        minute=14,
        score={"home": 1, "away": 0},
        leverage_index=2.8,
        outcome="Goal",
    )

    assert ctx["has_milestone"] is True
    assert ctx["milestone_alert"] is not None
    assert "Arsenal" in ctx["narrative_nugget"]
    assert "Rivalry Context" in ctx["narrative_nugget"]
    assert ctx["storage_engine"] == "local_json"
