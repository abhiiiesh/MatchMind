"""Context Agent: Stage 3 of the MatchMind Intelligence Pipeline.

Enriches raw match telemetry and tactical metrics with deep historical intelligence
(player career milestones, head-to-head records, situational comeback trends)
using local historical RAG with an Azure Cosmos DB vector-search integration path.
"""

from typing import List, Optional
import structlog

from matchmind.agents.base_agent import BaseAgent
from matchmind.context.rag_engine import HistoricalRAGEngine
from matchmind.models import AgentMessage

logger = structlog.get_logger(__name__)


class ContextAgent(BaseAgent):
    """Retrieves situational historical context for high-impact match moments."""

    def __init__(self, rag_engine: Optional[HistoricalRAGEngine] = None):
        super().__init__(
            agent_id="context_agent",
            role_name="Historical Intelligence & RAG Retrieval Specialist",
            supported_message_types=["METRIC_UPDATE"],
        )
        self.rag_engine = rag_engine or HistoricalRAGEngine()

    async def process(self, message: AgentMessage) -> List[AgentMessage]:
        payload = message.payload
        event = payload.get("event", {})
        metric_state = payload.get("metric_state", {})

        # Extract event participants and match context
        player_obj = event.get("player") or {}
        player_name = player_obj.get("name") if isinstance(player_obj, dict) else str(player_obj) if player_obj else None

        team_obj = event.get("team") or {}
        team_name = team_obj.get("name") if isinstance(team_obj, dict) else str(team_obj) if team_obj else None

        home_team = metric_state.get("home_team")
        away_team = metric_state.get("away_team")
        opp_team = away_team if team_name == home_team else (home_team or "Opponent")

        event_type = event.get("event_type", "Event")
        minute = message.match_minute
        score = metric_state.get("score", {"home": 0, "away": 0})
        leverage = metric_state.get("current_leverage_index", 1.0)
        outcome = event.get("outcome", "Success")

        # Query Historical RAG Engine
        context_data = self.rag_engine.retrieve_context(
            player_name=player_name,
            team_name=team_name,
            opponent_name=opp_team,
            event_type=event_type,
            minute=minute,
            score=score,
            leverage_index=leverage,
            outcome=outcome,
        )

        out_payload = {
            "event": event,
            "metric_state": metric_state,
            "historical_context": context_data,
        }

        out_metadata = dict(message.metadata)
        if context_data.get("has_milestone"):
            out_metadata["milestone_alert"] = context_data.get("milestone_alert")

        out_message = AgentMessage(
            source_agent=self.agent_id,
            target_agents=["narrative_agent"],
            match_id=message.match_id,
            event_index=message.event_index,
            match_minute=message.match_minute,
            message_type="CONTEXT_ENRICHED",
            payload=out_payload,
            metadata=out_metadata,
        )

        return [out_message]
