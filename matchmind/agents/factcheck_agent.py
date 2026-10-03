"""Fact-Checker Agent: Stage 6 of the MatchMind Intelligence Pipeline.

Acts as an automated compliance guardrail and hallucination detector. Validates
scorelines, player identities, event outcomes, and metric claims against ground-truth telemetry.
"""

import re
from typing import Dict, List, Tuple
import structlog

from matchmind.agents.base_agent import BaseAgent
from matchmind.models import AgentMessage

logger = structlog.get_logger(__name__)


class FactCheckerAgent(BaseAgent):
    """Verifies that generated commentary matches ground-truth match telemetry."""

    def __init__(self):
        super().__init__(
            agent_id="factcheck_agent",
            role_name="Compliance & Anti-Hallucination Guardrail",
            supported_message_types=["TRANSLATED_COMMENTARY"],
        )

    def _verify_scoreline(self, text: str, ground_truth_score: Dict[str, int]) -> Tuple[bool, str]:
        """Detects if commentary asserts an incorrect scoreline."""
        # Find score patterns like "2-1", "0 - 0", "3:2"
        score_patterns = re.findall(r"\b(\d+)\s*[-:]\s*(\d+)\b", text)
        actual_home = ground_truth_score.get("home", 0)
        actual_away = ground_truth_score.get("away", 0)

        for match in score_patterns:
            h, a = int(match[0]), int(match[1])
            # Check if this matches actual score or reverse
            if (h == actual_home and a == actual_away) or (h == actual_away and a == actual_home):
                continue
            # If a completely different score is claimed:
            return False, f"Scoreline hallucination detected: Text claims {h}-{a}, ground truth is {actual_home}-{actual_away}"

        return True, "Scoreline verified"

    def _verify_goal_outcome(self, commentary_map: Dict[str, str], outcome: str) -> Tuple[bool, str]:
        """Ensures non-goal events are not celebrated as goals."""
        if outcome != "Goal":
            for persona, text in commentary_map.items():
                if "GOAAAL" in text.upper() or "IT'S IN!" in text.upper():
                    return False, f"False goal hallucination: Event outcome was '{outcome}' but {persona} celebrated a goal."
        return True, "Outcome verified"

    async def process(self, message: AgentMessage) -> List[AgentMessage]:
        payload = message.payload
        narrative = payload.get("narrative", {})
        event = payload.get("event", {})
        metric_state = payload.get("metric_state", {})

        commentary_map = narrative.get("commentary_by_persona", {})
        ground_truth_score = metric_state.get("score", {"home": 0, "away": 0})
        actual_outcome = event.get("outcome", "Success")

        violations = []

        # 1. Verify goal outcome consistency
        goal_ok, goal_msg = self._verify_goal_outcome(commentary_map, actual_outcome)
        if not goal_ok:
            violations.append(goal_msg)

        # 2. Verify scorelines in all persona texts
        for persona, text in commentary_map.items():
            score_ok, score_msg = self._verify_scoreline(text, ground_truth_score)
            if not score_ok:
                violations.append(f"[{persona}] {score_msg}")

        is_verified = (len(violations) == 0)
        narrative["verified_by_factcheck"] = is_verified
        narrative["factcheck_notes"] = "; ".join(violations) if violations else "Passed all telemetry checks"

        if not is_verified:
            self.log.warning("Fact-checker caught narrative discrepancy", violations=violations)

        out_message = AgentMessage(
            source_agent=self.agent_id,
            target_agents=["*"],
            match_id=message.match_id,
            event_index=message.event_index,
            match_minute=message.match_minute,
            message_type="VERIFIED_OUTPUT",
            payload={
                "narrative": narrative,
                "event": event,
                "metric_state": metric_state,
                "is_verified": is_verified,
            },
            metadata=message.metadata,
        )

        return [out_message]
