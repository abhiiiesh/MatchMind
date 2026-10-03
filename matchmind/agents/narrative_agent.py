"""Narrative Agent: Stage 3 of the MatchMind Intelligence Pipeline.

Formulates tactical causation, dramatic game arcs, and the 'Why It Matters'
explanation for critical match moments.
"""

from typing import List
from matchmind.agents.base_agent import BaseAgent
from matchmind.models import AgentMessage, MetricState
from matchmind.narrative.story_arc import StoryArcClassifier
from matchmind.utils.azure_client import AzureOpenAIClient


class NarrativeAgent(BaseAgent):
    """The central reasoning brain that translates mathematical metrics into tactical narratives."""

    def __init__(self):
        super().__init__(
            agent_id="narrative_agent",
            role_name="Tactical Narrative & Causality Engine",
            supported_message_types=["METRIC_UPDATE"],
        )
        self.azure_client = AzureOpenAIClient()
        self.arc_classifier = StoryArcClassifier()

    async def process(self, message: AgentMessage) -> List[AgentMessage]:
        payload = message.payload
        metric_dict = payload.get("metric_state", {})
        if isinstance(metric_dict, MetricState):
            metric_state = metric_dict
        else:
            if "match_id" not in metric_dict:
                metric_dict["match_id"] = message.match_id
            metric_state = MetricState(**metric_dict)
        event = payload.get("event", {})

        # Classify the global narrative arc
        story_arc = self.arc_classifier.classify_arc(metric_state)

        team_obj = event.get("team") or {}
        team_name = team_obj.get("name") if isinstance(team_obj, dict) else str(team_obj)
        player_obj = event.get("player") or {}
        player_name = player_obj.get("name") if isinstance(player_obj, dict) else None

        # Prepare context payload for LLM / fallback engine
        match_context = {
            "minute": metric_state.minute,
            "score": metric_state.score,
            "home_team": metric_state.home_team,
            "away_team": metric_state.away_team,
            "cumulative_xg": metric_state.cumulative_xg,
            "rolling_ppda": metric_state.rolling_ppda,
            "field_tilt": metric_state.field_tilt,
            "leverage_index": metric_state.current_leverage_index,
            "story_arc": story_arc,
            "event": {
                "type": event.get("event_type"),
                "team": team_name,
                "player": player_name,
                "outcome": event.get("outcome"),
                "under_pressure": event.get("under_pressure"),
                "action_xg": metric_state.current_action_xg,
                "action_xt": metric_state.current_action_xt,
            },
        }


        # Generate structured explanation and draft commentary
        narrative_result = await self.azure_client.generate_structured_narrative(
            match_context=match_context,
            fallback_params={
                "event": event,
                "metric_state": metric_dict,
            },
        )

        out_payload = {
            "story_arc": story_arc,
            "why_it_matters": narrative_result.get("why_it_matters", ""),
            "draft_analyst": narrative_result.get("analyst_commentary", ""),
            "draft_casual": narrative_result.get("casual_commentary", ""),
            "draft_commentator": narrative_result.get("commentator_commentary", ""),
            "metric_state": metric_dict,
            "event": event,
        }

        out_message = AgentMessage(
            source_agent=self.agent_id,
            target_agents=["persona_agent"],
            match_id=message.match_id,
            event_index=message.event_index,
            match_minute=message.match_minute,
            message_type="NARRATIVE_DRAFT",
            payload=out_payload,
            metadata={"leverage_index": metric_state.current_leverage_index},
        )

        return [out_message]
