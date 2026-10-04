"""Persona Agent: Stage 4 of the MatchMind Intelligence Pipeline.

Customizes intelligence into tailored viewer perspectives:
Tactical Analyst, Casual Fan, Broadcast Commentator, and Accessible Audio.
"""

from typing import Dict, List
from matchmind.agents.base_agent import BaseAgent
from matchmind.constants import FanPersona
from matchmind.models import AgentMessage, NarrativeOutput, StructuredClaim


class PersonaAgent(BaseAgent):
    """Generates and refines persona-specific outputs for downstream delivery."""

    def __init__(self):
        super().__init__(
            agent_id="persona_agent",
            role_name="Audience Personalization Specialist",
            supported_message_types=["NARRATIVE_DRAFT"],
        )

    async def process(self, message: AgentMessage) -> List[AgentMessage]:
        payload = message.payload
        why_it_matters = payload.get("why_it_matters", "")
        story_arc = payload.get("story_arc", "Tactical Chess Match")
        draft_analyst = payload.get("draft_analyst", "")
        draft_casual = payload.get("draft_casual", "")
        draft_commentator = payload.get("draft_commentator", "")
        leverage = message.metadata.get("leverage_index", 1.0)
        event = payload.get("event", {})
        metric_dict = payload.get("metric_state", {})

        # Build accessibility description
        minute = message.match_minute
        player_obj = event.get("player") or {}
        player_name = player_obj.get("name", "Player") if isinstance(player_obj, dict) else "Player"
        team_obj = event.get("team") or {}
        team_name = team_obj.get("name", "Team") if isinstance(team_obj, dict) else "Team"
        score = metric_dict.get("score", {"home": 0, "away": 0})
        score_str = f"{score.get('home', 0)}-{score.get('away', 0)}"

        accessibility_commentary = (
            f"[Audio Description] Minute {minute}. {player_name} of {team_name} executes action in the "
            f"opponent's half. Current score stands at {score_str}. {why_it_matters}"
        )

        commentary_map: Dict[FanPersona, str] = {
            FanPersona.TACTICAL_ANALYST: draft_analyst,
            FanPersona.CASUAL_FAN: draft_casual,
            FanPersona.BROADCAST_COMMENTATOR: draft_commentator,
            FanPersona.ACCESSIBILITY_AUDIO: accessibility_commentary,
        }

        claims_raw = payload.get("structured_claims", [])
        structured_claims = [
            StructuredClaim(**c) if isinstance(c, dict) else c for c in claims_raw
        ]

        narrative_output = NarrativeOutput(
            match_id=message.match_id,
            event_index=message.event_index,
            minute=message.match_minute,
            game_state_arc=story_arc,
            leverage_index=leverage,
            why_it_matters_explanation=why_it_matters,
            commentary_by_persona=commentary_map,
            verified_by_factcheck=False,
            structured_claims=structured_claims,
        )


        out_message = AgentMessage(
            source_agent=self.agent_id,
            target_agents=["translator_agent"],
            match_id=message.match_id,
            event_index=message.event_index,
            match_minute=message.match_minute,
            message_type="PERSONA_COMMENTARY",
            payload={
                "narrative": narrative_output.model_dump(),
                "event": event,
                "metric_state": metric_dict,
                "historical_context": payload.get("historical_context"),
            },
            metadata={"leverage_index": leverage},
        )

        return [out_message]
