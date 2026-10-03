"""Historical Context & RAG Retrieval Engine for MatchMind.

Retrieves historical player profiles, team trends, and rivalry head-to-head records
via Azure Cosmos DB vector search or local in-memory fallback.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import structlog

from matchmind.config import settings

logger = structlog.get_logger(__name__)


class HistoricalRAGEngine:
    """Retrieves deep historical football intelligence to enrich live telemetry."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or (Path(__file__).parent.parent.parent / "data" / "historical")
        self.player_profiles: Dict[str, Any] = {}
        self.team_records: Dict[str, Any] = {}
        self.rivalries: Dict[str, Any] = {}

        self.cosmos_client = None
        self.is_cosmos_connected = False

        self._load_local_data()
        self._init_cosmos_db()

    def _load_local_data(self) -> None:
        """Load local JSON historical knowledge bases."""
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
                "Historical knowledge bases loaded successfully",
                players_count=len(self.player_profiles),
                teams_count=len(self.team_records),
                rivalries_count=len(self.rivalries),
            )
        except Exception as exc:
            logger.warning("Failed loading historical files, using empty defaults", error=str(exc))

    def _init_cosmos_db(self) -> None:
        """Initialize Azure Cosmos DB client if credentials are configured."""
        if settings.has_azure_cosmos:
            try:
                from azure.cosmos.aio import CosmosClient
                self.cosmos_client = CosmosClient(
                    url=settings.azure_cosmos_endpoint,
                    credential=settings.azure_cosmos_key,
                )
                self.is_cosmos_connected = True
                logger.info("Azure Cosmos DB historical vector client connected", database=settings.azure_cosmos_database)
            except Exception as exc:
                logger.warning("Could not connect to Azure Cosmos DB; operating in local RAG mode", error=str(exc))
                self.is_cosmos_connected = False
        else:
            logger.info("Azure Cosmos DB not configured; running in High-Performance Local RAG mode")

    def find_player(self, player_name: Optional[str]) -> Optional[Dict[str, Any]]:
        """Find player profile using fuzzy/token matching."""
        if not player_name or player_name in ["Player", "Team", "None"]:
            return None

        # 1. Exact match
        if player_name in self.player_profiles:
            return self.player_profiles[player_name]

        # 2. Case-insensitive / partial token match (e.g. "Salah" in "Mohamed Salah")
        p_name_lower = player_name.lower()
        for name, profile in self.player_profiles.items():
            if p_name_lower in name.lower() or any(token in name.lower() for token in p_name_lower.split() if len(token) > 2):
                return profile

        return None

    def find_rivalry(self, home_team: str, away_team: str) -> Optional[Dict[str, Any]]:
        """Find historical head-to-head rivalry record."""
        key1 = f"{home_team}_vs_{away_team}"
        key2 = f"{away_team}_vs_{home_team}"

        for key, rivalry in self.rivalries.items():
            if key == key1 or key == key2:
                return rivalry
            # Flexible match on team names
            if home_team.lower() in key.lower() and away_team.lower() in key.lower():
                return rivalry

        return None

    def retrieve_context(
        self,
        player_name: Optional[str],
        team_name: Optional[str],
        opponent_name: Optional[str],
        event_type: str,
        minute: int,
        score: Dict[str, int],
        leverage_index: float,
        outcome: str = "Success",
    ) -> Dict[str, Any]:
        """Synthesizes rich contextual historical intelligence for a match event."""
        team = team_name or "Team"
        opponent = opponent_name or "Opponent"
        score_diff = score.get("home", 0) - score.get("away", 0)

        # 1. Player milestone lookup
        player_info = self.find_player(player_name)
        milestone_alert = None
        player_nugget = ""

        if player_info:
            milestones = player_info.get("milestones", [])
            if outcome == "Goal" or event_type == "Shot":
                # Goal or shot highlight
                milestone_alert = milestones[0] if milestones else None
                player_nugget = f"{player_name} ({player_info.get('goals', 0)} goals in {player_info.get('appearances', 0)} appearances): {milestone_alert or player_info.get('signature_traits', '')}"
            elif event_type == "Pass" and player_info.get("assists", 0) > 0:
                player_nugget = f"{player_name}: {player_info.get('assists', 0)} career Premier League assists. {player_info.get('signature_traits', '')}"
            elif milestones:
                milestone_alert = milestones[0]
                player_nugget = f"{player_name}: {milestone_alert}"

        # 2. Situational Team Record
        team_info = self.team_records.get(team, {})
        team_trend = ""
        if team_info:
            trends = team_info.get("historical_trends", [])
            if minute >= 75 and abs(score_diff) <= 1:
                # Late close game trend
                if "goals_scored_final_15_mins" in team_info:
                    team_trend = f"{team} are lethal late: {team_info['goals_scored_final_15_mins']} goals scored in final 15 minutes."
                elif trends:
                    team_trend = trends[0]
            elif minute >= 45 and score_diff != 0:
                # Halftime / leading trend
                if score_diff > 0 and "win_rate_leading_at_halftime" in team_info:
                    team_trend = f"{team} convert leads ruthlessly: {team_info['win_rate_leading_at_halftime']}% win rate when leading at half-time."
                elif score_diff < 0 and "comeback_win_rate_trailing_at_halftime" in team_info:
                    team_trend = f"{team} comeback record: recover points in {team_info['comeback_win_rate_trailing_at_halftime']}% of matches when trailing."
            elif trends:
                team_trend = trends[0]

        # 3. Rivalry Dynamics
        rivalry_info = self.find_rivalry(team, opponent)
        rivalry_nugget = ""
        if rivalry_info:
            factors = rivalry_info.get("key_matchup_factors", [])
            if factors:
                rivalry_nugget = factors[0]
            else:
                rivalry_nugget = rivalry_info.get("historical_narrative", "")

        # 4. Synthesize single cohesive narrative nugget for broadcasters / LLM
        narrative_parts = []
        if milestone_alert:
            narrative_parts.append(f"Milestone Alert: {milestone_alert}.")
        elif player_nugget:
            narrative_parts.append(player_nugget)

        if team_trend:
            narrative_parts.append(team_trend)

        if rivalry_nugget and leverage_index >= 2.5:
            narrative_parts.append(f"Rivalry Context: {rivalry_nugget}")

        composite_nugget = " | ".join(narrative_parts) if narrative_parts else f"Historic fixture between {team} and {opponent}."

        return {
            "has_milestone": bool(milestone_alert),
            "milestone_alert": milestone_alert,
            "player_profile": player_info,
            "team_trend": team_trend,
            "rivalry_insight": rivalry_nugget,
            "narrative_nugget": composite_nugget,
        }
