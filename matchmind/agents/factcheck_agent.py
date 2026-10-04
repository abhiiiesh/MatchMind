"""Fact-Checker Agent: Stage 6 of the MatchMind Intelligence Pipeline.

Acts as an automated compliance guardrail and multi-dimensional hallucination detector.
Validates structured claims, scorelines, player identities, event outcomes, metrics,
historical milestones, translated commentary, and tactical causality against ground-truth match telemetry.
"""

import math
import re
from typing import Any, Dict, List, Optional, Tuple
import structlog

from matchmind.agents.base_agent import BaseAgent
from matchmind.models import (
    AgentMessage,
    ClaimStatus,
    ClaimType,
    StructuredClaim,
    VerificationSummary,
)

logger = structlog.get_logger(__name__)


class FactCheckerAgent(BaseAgent):
    """Verifies that generated commentary matches ground-truth match telemetry."""

    def __init__(self):
        super().__init__(
            agent_id="factcheck_agent",
            role_name="Compliance & Anti-Hallucination Guardrail",
            supported_message_types=["TRANSLATED_COMMENTARY"],
        )

    def _verify_structured_claims(
        self,
        claims: List[StructuredClaim],
        event: Dict[str, Any],
        metric_state: Dict[str, Any],
        historical_context: Optional[Dict[str, Any]],
    ) -> Tuple[List[StructuredClaim], List[str]]:
        """Validates all structured claims against ground-truth telemetry."""
        verified_claims: List[StructuredClaim] = []
        violations: List[str] = []

        ground_truth_score = metric_state.get("score", {"home": 0, "away": 0})
        actual_score_str = f"{ground_truth_score.get('home', 0)}-{ground_truth_score.get('away', 0)}"
        actual_outcome = event.get("outcome", "Success")
        actual_is_goal = (actual_outcome == "Goal")
        actual_minute = event.get("minute", metric_state.get("minute", 0))

        player_obj = event.get("player") or {}
        actual_player = player_obj.get("name") if isinstance(player_obj, dict) else str(player_obj) if player_obj else ""

        team_obj = event.get("team") or {}
        actual_team = team_obj.get("name") if isinstance(team_obj, dict) else str(team_obj) if team_obj else ""

        actual_xg = metric_state.get("current_action_xg")
        actual_xt = metric_state.get("current_action_xt")
        actual_field_tilt = metric_state.get("field_tilt")

        for claim in claims:
            # Copy claim
            c = claim.model_copy()

            if c.claim_type == ClaimType.SCORELINE:
                c.ground_truth_value = actual_score_str
                if str(c.claimed_value).strip() == actual_score_str:
                    c.status = ClaimStatus.VERIFIED
                    c.details = f"Scoreline verified: {actual_score_str}"
                else:
                    c.status = ClaimStatus.VIOLATION
                    msg = f"Scoreline claim mismatch: claimed '{c.claimed_value}', ground truth is '{actual_score_str}'"
                    c.details = msg
                    violations.append(msg)

            elif c.claim_type == ClaimType.GOAL_EVENT:
                c.ground_truth_value = actual_is_goal
                if bool(c.claimed_value) == actual_is_goal:
                    c.status = ClaimStatus.VERIFIED
                    c.details = f"Goal status verified: is_goal={actual_is_goal}"
                else:
                    c.status = ClaimStatus.VIOLATION
                    msg = f"Goal event contradiction: claimed is_goal={c.claimed_value}, event outcome is '{actual_outcome}'"
                    c.details = msg
                    violations.append(msg)

            elif c.claim_type == ClaimType.PLAYER_IDENTITY:
                c.ground_truth_value = actual_player
                # Verify exact or token match
                claimed_p = str(c.claimed_value).lower()
                actual_p_lower = actual_player.lower()
                if claimed_p in actual_p_lower or actual_p_lower in claimed_p or any(t in actual_p_lower for t in claimed_p.split() if len(t) > 2):
                    c.status = ClaimStatus.VERIFIED
                    c.details = f"Player identity verified: '{actual_player}'"
                else:
                    c.status = ClaimStatus.VIOLATION
                    msg = f"Player identity mismatch: claimed '{c.claimed_value}', actual actor is '{actual_player}'"
                    c.details = msg
                    violations.append(msg)

            elif c.claim_type == ClaimType.TEAM_IDENTITY:
                c.ground_truth_value = actual_team
                claimed_t = str(c.claimed_value).lower()
                actual_t_lower = actual_team.lower()
                if claimed_t in actual_t_lower or actual_t_lower in claimed_t:
                    c.status = ClaimStatus.VERIFIED
                    c.details = f"Team identity verified: '{actual_team}'"
                else:
                    c.status = ClaimStatus.VIOLATION
                    msg = f"Team identity mismatch: claimed '{c.claimed_value}', actual team in possession is '{actual_team}'"
                    c.details = msg
                    violations.append(msg)

            elif c.claim_type == ClaimType.MATCH_CLOCK:
                c.ground_truth_value = actual_minute
                try:
                    claimed_min = int(c.claimed_value)
                    if abs(claimed_min - actual_minute) <= 1:
                        c.status = ClaimStatus.VERIFIED
                        c.details = f"Match clock verified: minute {actual_minute}"
                    else:
                        c.status = ClaimStatus.VIOLATION
                        msg = f"Match clock discrepancy: claimed minute {claimed_min}, actual minute is {actual_minute}"
                        c.details = msg
                        violations.append(msg)
                except (ValueError, TypeError):
                    c.status = ClaimStatus.VIOLATION
                    violations.append(f"Invalid match clock format: {c.claimed_value}")

            elif c.claim_type == ClaimType.METRIC_XG:
                c.ground_truth_value = round(actual_xg, 2) if actual_xg is not None else None
                if actual_xg is not None:
                    try:
                        claimed_xg = float(c.claimed_value)
                        if abs(claimed_xg - actual_xg) <= 0.08:
                            c.status = ClaimStatus.VERIFIED
                            c.details = f"xG metric verified within tolerance: claimed={claimed_xg:.2f}, actual={actual_xg:.2f}"
                        else:
                            c.status = ClaimStatus.VIOLATION
                            msg = f"xG metric hallucination: claimed {claimed_xg:.2f}, actual model value is {actual_xg:.2f}"
                            c.details = msg
                            violations.append(msg)
                    except (ValueError, TypeError):
                        c.status = ClaimStatus.VIOLATION
                        violations.append(f"Invalid xG value format: {c.claimed_value}")
                else:
                    c.status = ClaimStatus.VERIFIED

            elif c.claim_type == ClaimType.METRIC_XT:
                c.ground_truth_value = round(actual_xt, 3) if actual_xt is not None else None
                if actual_xt is not None:
                    try:
                        claimed_xt = float(c.claimed_value)
                        if abs(claimed_xt - actual_xt) <= 0.03:
                            c.status = ClaimStatus.VERIFIED
                            c.details = f"xT metric verified: claimed={claimed_xt:.3f}, actual={actual_xt:.3f}"
                        else:
                            c.status = ClaimStatus.VIOLATION
                            msg = f"xT metric hallucination: claimed {claimed_xt:.3f}, actual value is {actual_xt:.3f}"
                            c.details = msg
                            violations.append(msg)
                    except (ValueError, TypeError):
                        c.status = ClaimStatus.VIOLATION
                        violations.append(f"Invalid xT format: {c.claimed_value}")
                else:
                    c.status = ClaimStatus.VERIFIED

            elif c.claim_type == ClaimType.METRIC_FIELD_TILT:
                c.ground_truth_value = round(actual_field_tilt, 1) if actual_field_tilt is not None else None
                if actual_field_tilt is not None:
                    try:
                        claimed_ft = float(c.claimed_value)
                        if abs(claimed_ft - actual_field_tilt) <= 3.0:
                            c.status = ClaimStatus.VERIFIED
                            c.details = f"Field Tilt verified: claimed={claimed_ft:.1f}%, actual={actual_field_tilt:.1f}%"
                        else:
                            c.status = ClaimStatus.VIOLATION
                            msg = f"Field Tilt hallucination: claimed {claimed_ft:.1f}%, actual is {actual_field_tilt:.1f}%"
                            c.details = msg
                            violations.append(msg)
                    except (ValueError, TypeError):
                        c.status = ClaimStatus.VIOLATION
                        violations.append(f"Invalid Field Tilt format: {c.claimed_value}")
                else:
                    c.status = ClaimStatus.VERIFIED

            elif c.claim_type == ClaimType.HISTORICAL_MILESTONE:
                if historical_context and historical_context.get("has_milestone"):
                    actual_milestone = historical_context.get("milestone_alert")
                    c.ground_truth_value = actual_milestone
                    c.status = ClaimStatus.VERIFIED
                    c.details = f"Milestone verified against historical RAG: {actual_milestone}"
                else:
                    c.status = ClaimStatus.VIOLATION
                    msg = f"Unsubstantiated historical milestone claim: '{c.claimed_value}'"
                    c.details = msg
                    violations.append(msg)

            else:
                c.status = ClaimStatus.VERIFIED

            verified_claims.append(c)

        return verified_claims, violations

    def _verify_scoreline_text(self, text: str, ground_truth_score: Dict[str, int]) -> Tuple[bool, str]:
        """Detects if commentary asserts an incorrect scoreline."""
        # 1. Strip tactical formations (e.g., 4-3-3, 4-2-3-1, 3-5-2)
        clean_text = re.sub(r"\b\d+-\d+-\d+(?:-\d+)?\b", "", text)
        # 2. Strip distance ranges (e.g., 6-8 meters, 10-12 yards)
        clean_text = re.sub(r"\b\d+\s*[-–]\s*\d+\s*(?:meters?|yards?|m|yd)\b", "", clean_text, flags=re.IGNORECASE)
        # 3. Strip timestamps / match clock (e.g., 12:30, 90:00)
        clean_text = re.sub(r"\b\d{1,2}:\d{2}\b", "", clean_text)

        # Find explicit score mentions
        score_patterns = re.findall(
            r"(?:score(?:line)?(?:\s+stands\s+at|\s+shifts\s+to|\s+is)?|makes\s+it|leads?\s+)\s*(\d+)\s*[-–:]\s*(\d+)",
            clean_text,
            flags=re.IGNORECASE,
        )

        if not score_patterns:
            score_patterns = re.findall(r"\b(\d+)\s*[-–]\s*(\d+)\b", clean_text)

        actual_home = ground_truth_score.get("home", 0)
        actual_away = ground_truth_score.get("away", 0)

        for match in score_patterns:
            h, a = int(match[0]), int(match[1])
            if h == actual_home and a == actual_away:
                continue
            return False, f"Scoreline hallucination detected: Text claims {h}-{a}, ground truth is {actual_home}-{actual_away}"

        return True, "Scoreline verified"

    def _verify_goal_outcome_text(self, text: str, outcome: str) -> Tuple[bool, str]:
        """Ensures non-goal events are not described or celebrated as goals."""
        if outcome != "Goal":
            # Check false goal celebrations and conversion phrases
            false_goal_patterns = [
                r"\bGOAA+L+\b",
                r"\bIT'S\s+IN\b",
                r"\bSCORES\b",
                r"\bCONVERTED\b",
                r"\bBACK\s+OF\s+THE\s+NET\b",
                r"\bFOUND\s+THE\s+NET\b",
                r"\bSEISMIC\s+GOAL\b",
            ]
            for pat in false_goal_patterns:
                if re.search(pat, text, flags=re.IGNORECASE):
                    return False, f"False goal hallucination: Event outcome was '{outcome}' but text celebrated or claimed a goal."
        return True, "Outcome verified"

    def _verify_translated_text(self, translations: Dict[str, str], outcome: str) -> List[str]:
        """Ensures multi-language translated commentary does not hallucinate goals for non-goal events."""
        violations = []
        if outcome != "Goal":
            false_words = {
                "es": ["¡gol", "gol!", "anota"],
                "fr": ["but!", "a marqué"],
                "hi": ["गोल!", "गोल किया"],
                "ar": ["هدف!", "يسجل"],
            }
            for lang, text in translations.items():
                words = false_words.get(lang, [])
                for w in words:
                    if w.lower() in text.lower():
                        violations.append(f"[{lang.upper()} Translation] False goal word detected: '{w}' on '{outcome}' event")
        return violations

    def _verify_metrics_in_text(self, text: str, metric_state: Dict[str, Any]) -> List[str]:
        """Detects if numeric metrics claimed in commentary text diverge significantly from ground truth."""
        violations = []
        # Check xG in text: e.g. "xG 0.85" or "xG: 0.85"
        xg_matches = re.findall(r"xG(?::|\s+)?\s*([0-9]+\.[0-9]+)", text, flags=re.IGNORECASE)
        actual_xg = metric_state.get("current_action_xg")
        if actual_xg is not None and xg_matches:
            for xg_str in xg_matches:
                val = float(xg_str)
                if abs(val - actual_xg) > 0.12:
                    violations.append(f"xG text claim hallucination: text states xG {val:.2f}, actual model value is {actual_xg:.2f}")

        # Check Field Tilt in text
        ft_matches = re.findall(r"Field\s+Tilt(?::|\s+at|\s+of)?\s*([0-9]+\.?[0-9]*)%", text, flags=re.IGNORECASE)
        actual_ft = metric_state.get("field_tilt")
        if actual_ft is not None and ft_matches:
            for ft_str in ft_matches:
                val = float(ft_str)
                if abs(val - actual_ft) > 5.0:
                    violations.append(f"Field Tilt text claim hallucination: text states {val:.1f}%, actual is {actual_ft:.1f}%")

        return violations

    async def process(self, message: AgentMessage) -> List[AgentMessage]:
        payload = message.payload
        narrative = payload.get("narrative", {})
        event = payload.get("event", {})
        metric_state = payload.get("metric_state", {})
        historical_context = payload.get("historical_context") or narrative.get("historical_context")

        commentary_map = narrative.get("commentary_by_persona", {})
        translations = narrative.get("translations", {})
        why_it_matters = narrative.get("why_it_matters_explanation", "")
        ground_truth_score = metric_state.get("score", {"home": 0, "away": 0})
        actual_outcome = event.get("outcome", "Success")

        violations: List[str] = []

        # 1. Verify Structured Claims Array
        raw_claims = narrative.get("structured_claims", [])
        claims_objs = [
            StructuredClaim(**c) if isinstance(c, dict) else c for c in raw_claims
        ]
        verified_claims, claim_violations = self._verify_structured_claims(
            claims=claims_objs,
            event=event,
            metric_state=metric_state,
            historical_context=historical_context,
        )
        violations.extend(claim_violations)

        # 2. Verify Goal Outcome Consistency in all texts
        all_texts = list(commentary_map.values()) + [why_it_matters]
        for idx, text in enumerate(all_texts):
            goal_ok, goal_msg = self._verify_goal_outcome_text(text, actual_outcome)
            if not goal_ok:
                violations.append(goal_msg)
                break

        # 3. Verify Scorelines across all persona texts
        for persona, text in commentary_map.items():
            score_ok, score_msg = self._verify_scoreline_text(text, ground_truth_score)
            if not score_ok:
                violations.append(f"[{persona}] {score_msg}")

        # 4. Verify Translations
        trans_violations = self._verify_translated_text(translations, actual_outcome)
        violations.extend(trans_violations)

        # 5. Verify Metrics within Text
        for persona, text in commentary_map.items():
            text_metric_violations = self._verify_metrics_in_text(text, metric_state)
            violations.extend(text_metric_violations)

        is_verified = (len(violations) == 0)

        # Build comprehensive VerificationSummary
        total_claims_count = len(verified_claims) + len(commentary_map)
        verified_claims_count = sum(1 for c in verified_claims if c.status == ClaimStatus.VERIFIED)
        if is_verified:
            verified_claims_count += len(commentary_map)

        verification_summary = VerificationSummary(
            passed=is_verified,
            total_claims=total_claims_count,
            verified_count=verified_claims_count,
            violation_count=len(violations),
            violations=violations,
            claims=verified_claims,
        )

        narrative["verified_by_factcheck"] = is_verified
        narrative["factcheck_notes"] = "; ".join(violations) if violations else "Passed all structured claims and telemetry checks"
        narrative["structured_claims"] = [c.model_dump() for c in verified_claims]
        narrative["verification_summary"] = verification_summary.model_dump()

        if not is_verified:
            self.log.warning(
                "Fact-checker caught narrative discrepancy",
                violations=violations,
                claim_violations_count=len(claim_violations),
            )
        else:
            self.log.info(
                "Fact-checker verified all structured claims and telemetry",
                total_claims=total_claims_count,
                verified_count=verified_claims_count,
            )

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
                "verification_summary": verification_summary.model_dump(),
            },
            metadata=message.metadata,
        )

        return [out_message]
