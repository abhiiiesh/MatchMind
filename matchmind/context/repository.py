"""Historical Context Repository Abstraction for MatchMind.

Implements clean Repository Pattern supporting Local JSON storage and Azure Cosmos DB
vector-search integration path with transparent fallback.
"""

from abc import ABC, abstractmethod
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional
import structlog

from matchmind.config import settings

logger = structlog.get_logger(__name__)


class HistoricalContextRepository(ABC):
    """Abstract interface for historical football intelligence retrieval."""

    @abstractmethod
    def get_player(self, player_name: str) -> Optional[Dict[str, Any]]:
        """Find player profile and career milestones."""
        pass

    @abstractmethod
    def get_team_record(self, team_name: str) -> Optional[Dict[str, Any]]:
        """Find team situational comeback and tactical trends."""
        pass

    @abstractmethod
    def get_rivalry(self, home_team: str, away_team: str) -> Optional[Dict[str, Any]]:
        """Find head-to-head rivalry history and key matchup factors."""
        pass

    @abstractmethod
    def vector_search(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Perform semantic or vector similarity search across historical archives."""
        pass

    @abstractmethod
    def get_storage_type(self) -> str:
        """Returns human-readable name of underlying repository engine."""
        pass


class LocalJsonRepository(HistoricalContextRepository):
    """Local file-based historical knowledge repository with fuzzy token search."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or (Path(__file__).parent.parent.parent / "data" / "historical")
        self.player_profiles: Dict[str, Any] = {}
        self.team_records: Dict[str, Any] = {}
        self.rivalries: Dict[str, Any] = {}
        self._load_local_data()

    def _load_local_data(self) -> None:
        try:
            players_file = self.data_dir / "player_profiles.json"
            if players_file.exists():
                with open(players_file, "r", encoding="utf-8") as f:
                    self.player_profiles = json.load(f).get("players", {})

            teams_file = self.data_dir / "team_records.json"
            if teams_file.exists():
                with open(teams_file, "r", encoding="utf-8") as f:
                    self.team_records = json.load(f).get("teams", {})

            rivalries_file = self.data_dir / "rivalry_database.json"
            if rivalries_file.exists():
                with open(rivalries_file, "r", encoding="utf-8") as f:
                    self.rivalries = json.load(f).get("rivalries", {})

            logger.info(
                "LocalJsonRepository loaded knowledge archives",
                players=len(self.player_profiles),
                teams=len(self.team_records),
                rivalries=len(self.rivalries),
            )
        except Exception as exc:
            logger.warning("Failed loading historical files into LocalJsonRepository", error=str(exc))

    def get_player(self, player_name: str) -> Optional[Dict[str, Any]]:
        if not player_name or player_name in ["Player", "Team", "None"]:
            return None

        # 1. Exact match
        if player_name in self.player_profiles:
            return self.player_profiles[player_name]

        # 2. Case-insensitive / partial token match
        p_name_lower = player_name.lower()
        for name, profile in self.player_profiles.items():
            if p_name_lower in name.lower() or any(t in name.lower() for t in p_name_lower.split() if len(t) > 2):
                return profile

        return None

    def get_team_record(self, team_name: str) -> Optional[Dict[str, Any]]:
        if not team_name:
            return None
        if team_name in self.team_records:
            return self.team_records[team_name]
        t_lower = team_name.lower()
        for name, record in self.team_records.items():
            if t_lower in name.lower() or name.lower() in t_lower:
                return record
        return None

    def get_rivalry(self, home_team: str, away_team: str) -> Optional[Dict[str, Any]]:
        key1 = f"{home_team}_vs_{away_team}"
        key2 = f"{away_team}_vs_{home_team}"

        for key, rivalry in self.rivalries.items():
            if key == key1 or key == key2:
                return rivalry
            if home_team.lower() in key.lower() and away_team.lower() in key.lower():
                return rivalry
        return None

    def vector_search(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Keyword relevance search fallback simulating vector similarity ranking."""
        query_tokens = set(query_text.lower().split())
        scored: List[Tuple[float, Dict[str, Any]]] = []

        for p_name, prof in self.player_profiles.items():
            content = f"{p_name} {prof.get('team', '')} {prof.get('signature_traits', '')} {' '.join(prof.get('milestones', []))}"
            c_tokens = set(content.lower().split())
            overlap = len(query_tokens.intersection(c_tokens))
            if overlap > 0:
                scored.append((float(overlap), {"type": "player", "name": p_name, "data": prof}))

        for r_name, riv in self.rivalries.items():
            content = f"{r_name} {riv.get('historical_narrative', '')} {' '.join(riv.get('key_matchup_factors', []))}"
            c_tokens = set(content.lower().split())
            overlap = len(query_tokens.intersection(c_tokens))
            if overlap > 0:
                scored.append((float(overlap), {"type": "rivalry", "name": r_name, "data": riv}))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]

    def get_storage_type(self) -> str:
        return "local_json"


class CosmosVectorRepository(HistoricalContextRepository):
    """Azure Cosmos DB vector-search repository with graceful local fallback."""

    def __init__(self, fallback_repo: Optional[LocalJsonRepository] = None):
        self.fallback = fallback_repo or LocalJsonRepository()
        self.client = None
        self.container = None
        self.is_connected = False
        self._init_cosmos()

    def _init_cosmos(self) -> None:
        if settings.has_azure_cosmos:
            try:
                from azure.cosmos import CosmosClient
                self.client = CosmosClient(
                    url=settings.azure_cosmos_endpoint,
                    credential=settings.azure_cosmos_key,
                )
                db = self.client.get_database_client(settings.azure_cosmos_database)
                self.container = db.get_container_client(settings.azure_cosmos_container)
                self.is_connected = True
                logger.info("Azure Cosmos DB vector repository initialized", database=settings.azure_cosmos_database)
            except Exception as exc:
                logger.warning("Failed connecting to Cosmos DB; using local JSON fallback", error=str(exc))
                self.is_connected = False
        else:
            logger.info("Azure Cosmos DB credentials not present; using local JSON repository fallback")
            self.is_connected = False

    def get_player(self, player_name: str) -> Optional[Dict[str, Any]]:
        if self.is_connected and self.container:
            try:
                query = "SELECT * FROM c WHERE c.type = 'player' AND CONTAINS(c.name, @name, true)"
                items = list(self.container.query_items(
                    query=query,
                    parameters=[{"name": "@name", "value": player_name}],
                    enable_cross_partition_query=True,
                ))
                if items:
                    return items[0]
            except Exception as exc:
                logger.debug("Cosmos player lookup failed; falling back", error=str(exc))
        return self.fallback.get_player(player_name)

    def get_team_record(self, team_name: str) -> Optional[Dict[str, Any]]:
        if self.is_connected and self.container:
            try:
                query = "SELECT * FROM c WHERE c.type = 'team' AND c.team_name = @team"
                items = list(self.container.query_items(
                    query=query,
                    parameters=[{"name": "@team", "value": team_name}],
                    enable_cross_partition_query=True,
                ))
                if items:
                    return items[0]
            except Exception as exc:
                logger.debug("Cosmos team lookup failed; falling back", error=str(exc))
        return self.fallback.get_team_record(team_name)

    def get_rivalry(self, home_team: str, away_team: str) -> Optional[Dict[str, Any]]:
        if self.is_connected and self.container:
            try:
                query = "SELECT * FROM c WHERE c.type = 'rivalry' AND (c.id = @k1 OR c.id = @k2)"
                items = list(self.container.query_items(
                    query=query,
                    parameters=[
                        {"name": "@k1", "value": f"{home_team}_vs_{away_team}"},
                        {"name": "@k2", "value": f"{away_team}_vs_{home_team}"},
                    ],
                    enable_cross_partition_query=True,
                ))
                if items:
                    return items[0]
            except Exception as exc:
                logger.debug("Cosmos rivalry lookup failed; falling back", error=str(exc))
        return self.fallback.get_rivalry(home_team, away_team)

    def vector_search(self, query_text: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Executes relevance-ranked semantic retrieval on Cosmos DB with graceful local fallback."""
        if self.is_connected and self.container:
            try:
                # Extract clean search tokens from query text (words >= 3 chars)
                tokens = [t.lower() for t in re.findall(r"\b[a-zA-Z0-9_\-]{3,}\b", query_text)]
                if tokens:
                    conditions = []
                    parameters = [{"name": "@top_k", "value": top_k}]
                    for idx, tok in enumerate(tokens[:5]):
                        p_name = f"@tok{idx}"
                        parameters.append({"name": p_name, "value": tok})
                        conditions.append(
                            f"(CONTAINS(LOWER(c.content), {p_name}) OR CONTAINS(LOWER(c.name), {p_name}) OR CONTAINS(LOWER(c.type), {p_name}))"
                        )
                    where_clause = " OR ".join(conditions)
                    query = f"SELECT TOP @top_k c.id, c.name, c.type, c.content FROM c WHERE {where_clause}"
                    items = list(self.container.query_items(
                        query=query,
                        parameters=parameters,
                        enable_cross_partition_query=True,
                    ))
                    if items:
                        return items
            except Exception as exc:
                logger.debug("Cosmos relevance search query failed; using local fallback", error=str(exc))
        return self.fallback.vector_search(query_text, top_k=top_k)

    def get_storage_type(self) -> str:
        return "azure_cosmos_nosql_relevance" if self.is_connected else "local_historical_rag_cosmos_fallback"


def get_context_repository(data_dir: Optional[Path] = None) -> HistoricalContextRepository:
    """Factory creating the active repository based on environment configuration."""
    local_repo = LocalJsonRepository(data_dir=data_dir)
    if settings.has_azure_cosmos:
        return CosmosVectorRepository(fallback_repo=local_repo)
    return local_repo
