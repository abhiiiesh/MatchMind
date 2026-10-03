"""Azure OpenAI Client with Automatic Local Fallback & Error Resilience."""

import json
from typing import Any, Dict, List, Optional
import structlog
from openai import AsyncAzureOpenAI

from matchmind.config import settings
from matchmind.narrative.local_fallback import LocalNarrativeEngine

logger = structlog.get_logger(__name__)


class AzureOpenAIClient:
    """Manages Azure OpenAI GPT-4o / GPT-4o-mini connections.

    Gracefully falls back to LocalNarrativeEngine if Azure credentials are missing
    or network/rate-limit errors occur.
    """

    def __init__(self):
        self.is_configured = settings.has_azure_openai
        self.client: Optional[AsyncAzureOpenAI] = None
        self.gpt4o_deployment = settings.azure_openai_gpt4o_deployment
        self.gpt4o_mini_deployment = settings.azure_openai_gpt4o_mini_deployment

        if self.is_configured:
            try:
                self.client = AsyncAzureOpenAI(
                    azure_endpoint=settings.azure_openai_endpoint,
                    api_key=settings.azure_openai_api_key,
                    api_version=settings.azure_openai_api_version,
                )
                logger.info(
                    "Azure OpenAI client successfully initialized",
                    endpoint=settings.azure_openai_endpoint,
                    gpt4o=self.gpt4o_deployment,
                    gpt4o_mini=self.gpt4o_mini_deployment,
                )
            except Exception as exc:
                logger.warning(
                    "Failed to initialize Azure OpenAI client; enabling fallback mode",
                    error=str(exc),
                )
                self.is_configured = False
        else:
            logger.info("Azure OpenAI credentials not configured; running in High-Fidelity Local Engine mode")

    async def generate_chat(
        self,
        system_prompt: str,
        user_prompt: str,
        deployment: Optional[str] = None,
        json_mode: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 500,
    ) -> str:
        """Call Azure OpenAI chat completion, or fall back if unconfigured/failed."""
        if not self.is_configured or not self.client:
            return ""

        model_name = deployment or self.gpt4o_mini_deployment
        try:
            kwargs: Dict[str, Any] = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            response = await self.client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content or ""
            return content.strip()
        except Exception as exc:
            logger.warning("Azure OpenAI call failed; falling back", error=str(exc), model=model_name)
            return ""

    async def generate_structured_narrative(
        self,
        match_context: Dict[str, Any],
        fallback_params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate tactical narrative with structured JSON output, falling back gracefully."""
        if self.is_configured and self.client:
            system_prompt = (
                "You are the MatchMind AI Tactical Intelligence Engine for Premier League broadcasts. "
                "Analyze the provided match telemetry and output a strict JSON object with these keys:\n"
                "- 'game_state_arc': string (e.g. 'Dominant Siege', 'Counter-Attack Ambush', 'Tense Stalemate')\n"
                "- 'why_it_matters': string (Explain WHY this moment matters tactically, citing metrics and spaces)\n"
                "- 'analyst_commentary': string (Pundit-grade tactical breakdown with stats)\n"
                "- 'casual_commentary': string (Excited, approachable fan-friendly reaction with emojis)\n"
                "- 'commentator_commentary': string (Television play-by-play broadcast call)\n"
            )
            user_prompt = f"Match Telemetry:\n{json.dumps(match_context, default=str)}"

            raw_response = await self.generate_chat(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                deployment=self.gpt4o_deployment,
                json_mode=True,
                temperature=0.6,
            )
            if raw_response:
                try:
                    return json.loads(raw_response)
                except json.JSONDecodeError:
                    logger.warning("Failed to decode JSON from Azure OpenAI; using local engine")

        # Fallback to local heuristic engine
        evt = fallback_params["event"]
        ms = fallback_params["metric_state"]
        player_name = evt.get("player", {}).get("name", "Player") if evt.get("player") else "Team"
        team_name = evt.get("team", {}).get("name", "Team")
        event_type = evt.get("event_type", "Event")
        minute = ms.get("minute", 0)
        score = ms.get("score", {"home": 0, "away": 0})
        action_xg = ms.get("current_action_xg")
        action_xt = ms.get("current_action_xt")
        field_tilt = ms.get("field_tilt", 50.0)
        ppda = ms.get("rolling_ppda", {}).get("away", 11.5)
        leverage = ms.get("current_leverage_index", 1.0)
        outcome = evt.get("outcome", "Success")

        why_matters = LocalNarrativeEngine.generate_why_it_matters(
            event_type=event_type,
            team_name=team_name,
            player_name=player_name,
            minute=minute,
            score=score,
            action_xg=action_xg,
            action_xt=action_xt,
            field_tilt=field_tilt,
            ppda=ppda,
            leverage_index=leverage,
        )

        analyst = LocalNarrativeEngine.generate_persona_commentary(
            persona=settings.FanPersona.TACTICAL_ANALYST if hasattr(settings, "FanPersona") else "tactical_analyst",
            event_type=event_type,
            team_name=team_name,
            player_name=player_name,
            minute=minute,
            score=score,
            action_xg=action_xg,
            field_tilt=field_tilt,
            ppda=ppda,
            why_it_matters=why_matters,
            outcome=outcome,
        )

        casual = LocalNarrativeEngine.generate_persona_commentary(
            persona="casual_fan",
            event_type=event_type,
            team_name=team_name,
            player_name=player_name,
            minute=minute,
            score=score,
            action_xg=action_xg,
            field_tilt=field_tilt,
            ppda=ppda,
            why_it_matters=why_matters,
            outcome=outcome,
        )

        commentator = LocalNarrativeEngine.generate_persona_commentary(
            persona="broadcast_commentator",
            event_type=event_type,
            team_name=team_name,
            player_name=player_name,
            minute=minute,
            score=score,
            action_xg=action_xg,
            field_tilt=field_tilt,
            ppda=ppda,
            why_it_matters=why_matters,
            outcome=outcome,
        )

        return {
            "game_state_arc": ms.get("momentum_direction", "balanced").replace("_", " ").title(),
            "why_it_matters": why_matters,
            "analyst_commentary": analyst,
            "casual_commentary": casual,
            "commentator_commentary": commentator,
        }
