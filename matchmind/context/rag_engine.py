"""Historical Context & RAG Retrieval Engine for MatchMind.

Retrieves historical player profiles, team trends, and rivalry head-to-head records
via Local Historical RAG with an Azure Cosmos DB vector-search integration path.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import structlog

from matchmind.context.repository import (
    HistoricalContextRepository,
    LocalJsonRepository,
    get_context_repository,
)

logger = structlog.get_logger(__name__)


class HistoricalRAGEngine:
    """Retrieves deep historical football intelligence to enrich live telemetry.

    Employs Local Historical RAG with an Azure Cosmos DB vector-search integration path.
    """

    def __init__(
        self,
        repository: Optional[HistoricalContextRepository] = None,
        data_dir: Optional[Path] = None,
    ):
        self.repository = repository or get_context_repository(data_dir=data_dir)
        logger.info(
            "HistoricalRAGEngine initialized",
            storage_engine=self.repository.get_storage_type(),
        )

    def find_player(self, player_name: Optional[str]) -> Optional[Dict[str, Any]]:
        """Find player profile using repository."""
        if not player_name or player_name in ["Player", "Team", "None"]:
            return None
        return self.repository.get_player(player_name)

    def find_rivalry(self, home_team: str, away_team: str) -> Optional[Dict[str, Any]]:
        """Find historical head-to-head rivalry record."""
        return self.repository.get_rivalry(home_team, away_team)

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
                milestone_alert = milestones[0] if milestones else None
                player_nugget = (
                    f"{player_name} ({player_info.get('goals', 0)} goals in "
                    f"{player_info.get('appearances', 0)} appearances): "
                    f"{milestone_alert or player_info.get('signature_traits', '')}"
                )
            elif event_type == "Pass" and player_info.get("assists", 0) > 0:
                player_nugget = (
                    f"{player_name}: {player_info.get('assists', 0)} career Premier League assists. "
                    f"{player_info.get('signature_traits', '')}"
                )
            elif milestones:
                milestone_alert = milestones[0]
                player_nugget = f"{player_name}: {milestone_alert}"

        # 2. Situational Team Record
        team_info = self.repository.get_team_record(team) or {}
        team_trend = ""
        if team_info:
            trends = team_info.get("historical_trends", [])
            if minute >= 75 and abs(score_diff) <= 1:
                if "goals_scored_final_15_mins" in team_info:
                    team_trend = f"{team} are lethal late: {team_info['goals_scored_final_15_mins']} goals scored in final 15 minutes."
                elif trends:
                    team_trend = trends[0]
            elif minute >= 45 and score_diff != 0:
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
            "storage_engine": self.repository.get_storage_type(),
        }
