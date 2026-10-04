"""High-Fidelity Local Narrative & Commentary Fallback Engine.

Provides deep, context-rich football explanations and persona commentary when
Azure OpenAI is either unconfigured or experiencing latency/rate-limit spikes.
Strictly branches descriptions by event outcome (Goal, Saved, Blocked, Off Target).
"""

from typing import Any, Dict, List, Optional
from matchmind.constants import FanPersona
from matchmind.models import ClaimType, StructuredClaim


class LocalNarrativeEngine:
    """Heuristic tactical causality generator producing pundit-grade commentary."""

    @staticmethod
    def generate_why_it_matters(
        event_type: str,
        team_name: str,
        player_name: str,
        minute: int,
        score: Dict[str, int],
        action_xg: Optional[float],
        action_xt: Optional[float],
        field_tilt: float,
        ppda: float,
        leverage_index: float,
        historical_context: Optional[str] = None,
        outcome: str = "Success",
    ) -> str:
        """Explains WHY the moment is tactically critical with strict outcome branch safety."""
        explanation = ""
        if event_type == "Shot":
            xg_val = action_xg or 0.10
            # Strict outcome-based language branching
            if outcome == "Goal":
                if xg_val >= 0.40:
                    explanation = (
                        f"{player_name} converted a high-probability opportunity (xG: {xg_val:.2f}) created by breaking "
                        f"the central defensive line. The opposing center-backs were dragged out "
                        f"of shape, presenting a clinical finish rarely conceded in Premier League fixtures."
                    )
                else:
                    explanation = (
                        f"An extraordinary low-probability finish (xG: {xg_val:.2f})! {player_name} converted "
                        f"under heavy defensive pressure from an acute angle, beating the goalkeeper's post-shot "
                        f"positioning through sheer individual technique."
                    )
            elif outcome in ["Saved", "Saved to Post"]:
                explanation = (
                    f"{player_name} forced a crucial save from the goalkeeper (xG: {xg_val:.2f}). "
                    f"Generated during sustained pressure (Field Tilt: {field_tilt:.1f}%), testing the keeper's reflexes."
                )
            elif outcome == "Blocked":
                explanation = (
                    f"{player_name} had the shot blocked by the retreating defensive line (xG: {xg_val:.2f}). "
                    f"The defensive block closed down the shooting lane in the nick of time."
                )
            elif outcome in ["Off Target", "Way Off"]:
                explanation = (
                    f"{player_name} attempted a strike (xG: {xg_val:.2f}) but fired off target. "
                    f"An ambitious effort that failed to trouble the goalkeeper."
                )
            elif outcome in ["Post", "Woodwork"]:
                explanation = (
                    f"{player_name} rattled the woodwork (xG: {xg_val:.2f})! Denied only by the width of the post."
                )
            else:
                explanation = (
                    f"{player_name} took the shot with an expected goal value of {xg_val:.2f}. "
                    f"Generated during sustained pressure (Field Tilt: {field_tilt:.1f}%)."
                )

        elif event_type == "Pass":
            xt_val = action_xt or 0.0
            if xt_val > 0.05:
                explanation = (
                    f"{player_name}'s progressive ball penetrated multiple defensive layers (Threat Added: +{xt_val:.3f} xT). "
                    f"This line-breaking pass bypasses the opponent's pressing trap and directly shifts play into the final third."
                )
            elif xt_val < -0.02:
                explanation = (
                    f"A backward recycling pass under tactical pressure. With the opponent maintaining an aggressive "
                    f"PPDA of {ppda:.1f}, {team_name} reset possession to evade a midfield turnover trap."
                )
            else:
                explanation = (
                    f"Routine possession maintenance by {player_name}. Sustaining tempo as {team_name} control "
                    f"possession rhythm."
                )

        elif event_type in ["Interception", "Duel", "Pressure", "Block"]:
            if ppda <= 9.0:
                explanation = (
                    f"High-intensity defensive intervention by {player_name}. Part of a coordinated counter-press "
                    f"(PPDA: {ppda:.1f}) specifically intended to choke transition lanes and force an immediate turnover."
                )
            else:
                explanation = (
                    f"Defensive containment by {player_name}. Resetting the defensive shape to restrict half-space penetration."
                )
        else:
            explanation = (
                f"Tactical phase at minute {minute}. {team_name} organizing their shape with leverage index at {leverage_index:.1f}."
            )

        if historical_context:
            explanation += f" Historical Context: {historical_context}"

        return explanation

    @classmethod
    def generate_persona_commentary(
        cls,
        persona: FanPersona,
        event_type: str,
        team_name: str,
        player_name: str,
        minute: int,
        score: Dict[str, int],
        action_xg: Optional[float],
        field_tilt: float,
        ppda: float,
        why_it_matters: str,
        outcome: str = "Success",
        action_xt: Optional[float] = None,
    ) -> str:
        """Renders persona-specific commentary with strict outcome-based truthfulness."""
        score_dict = score or {"home": 0, "away": 0}
        score_str = f"{score_dict.get('home', 0)}-{score_dict.get('away', 0)}"

        # Coerce string to FanPersona enum if necessary
        if isinstance(persona, str):
            try:
                persona = FanPersona(persona)
            except ValueError:
                pass

        if persona == FanPersona.TACTICAL_ANALYST:
            xg_txt = f" (xG {action_xg:.2f})" if action_xg is not None else ""
            xt_txt = f" (xT +{action_xt:.3f})" if action_xt is not None and action_xt > 0 else ""
            outcome_txt = f" [Outcome: {outcome}]" if outcome != "Success" else ""
            return (
                f"[TACTICAL ANALYSIS | {minute}'] {player_name} ({team_name}) executes {event_type}{outcome_txt}{xg_txt}{xt_txt}. "
                f"Field Tilt at {field_tilt:.1f}% with defending PPDA sitting at {ppda:.1f}. "
                f"Context: {why_it_matters}"
            )

        elif persona == FanPersona.CASUAL_FAN:
            if outcome == "Goal":
                return (
                    f"🔥 GOAAALLL!! {player_name} scores! Absolute chaos at {minute}'! "
                    f"Scoreline shifts to {score_str}! What a moment for {team_name} fans! ⚽💥"
                )
            elif event_type == "Shot":
                if outcome in ["Saved", "Saved to Post"]:
                    return (
                        f"🧤 Brilliant save! The keeper denies {player_name} at {minute}'! "
                        f"Heart in mouth moment for {team_name} supporters!"
                    )
                elif outcome == "Blocked":
                    return (
                        f"🛡️ Massive block! {player_name} shoots but it's charged down at {minute}'!"
                    )
                elif outcome in ["Off Target", "Way Off"]:
                    return (
                        f"😮 Off target from {player_name}! Had time to pick a spot at {minute}'!"
                    )
                return (
                    f"😮 Big chance for {player_name}! The crowd is on their feet! "
                    f"Can you believe how close that was at {minute}'?!"
                )
            elif event_type == "Pass" and ((action_xt or 0.0) > 0.04 or (action_xg or 0.0) > 0.2):
                return f"👀 Brilliant play by {player_name}! Beautiful pass that opens up the whole defense!"
            else:
                return f"⚡ {player_name} with great movement for {team_name} in the {minute}th minute."

        elif persona == FanPersona.BROADCAST_COMMENTATOR:
            if outcome == "Goal":
                return (
                    f"AND IT'S IN! {player_name} breaks through in the {minute}th minute! "
                    f"A seismic goal that makes it {score_str}. {why_it_matters}"
                )
            elif event_type == "Shot":
                if outcome in ["Saved", "Saved to Post"]:
                    return (
                        f"Terrific stop! The goalkeeper gets down well to turn aside {player_name}'s strike in the {minute}th minute. "
                        f"{why_it_matters}"
                    )
                elif outcome == "Blocked":
                    return (
                        f"Charged down! {player_name} lets fly in the {minute}th minute, but the defender throws their body on the line. "
                        f"{why_it_matters}"
                    )
                elif outcome in ["Off Target", "Way Off"]:
                    return (
                        f"High and wide! {player_name} opens up the angle in the {minute}th minute, but can't keep the effort down. "
                        f"{why_it_matters}"
                    )
                return (
                    f"Chance taken by {player_name}! Struck with conviction in the {minute}th minute, "
                    f"testing the defense as {team_name} ramp up the pressure."
                )
            else:
                return (
                    f"{minute}' into the match: {player_name} threads it forward for {team_name}. "
                    f"Patience and purpose in their build-up play."
                )

        elif persona == FanPersona.ACCESSIBILITY_AUDIO:
            action_desc = "scores a goal" if outcome == "Goal" else f"executes {event_type} ({outcome})"
            return (
                f"[Audio Description] Minute {minute}. {player_name} of {team_name} {action_desc}. "
                f"Current score stands at {score_str}. Action taking place in the attacking half. {why_it_matters}"
            )

        return f"{minute}' {player_name} with the {event_type} for {team_name}."

    @staticmethod
    def extract_structured_claims(
        event: Dict[str, Any],
        metric_state: Dict[str, Any],
        historical_context: Optional[Dict[str, Any]] = None,
    ) -> List[StructuredClaim]:
        """Extracts verifiable ground-truth claims for automated compliance validation."""
        claims: List[StructuredClaim] = []
        event_idx = event.get("index", 0)
        event_ids = [event_idx] if event_idx else []

        score = metric_state.get("score", {"home": 0, "away": 0})
        minute = event.get("minute", metric_state.get("minute", 0))
        outcome = event.get("outcome", "Success")
        event_type = event.get("event_type", "Event")

        player_obj = event.get("player") or {}
        player_name = player_obj.get("name") if isinstance(player_obj, dict) else str(player_obj) if player_obj else None

        team_obj = event.get("team") or {}
        team_name = team_obj.get("name") if isinstance(team_obj, dict) else str(team_obj) if team_obj else None

        # 1. Scoreline Claim
        score_str = f"{score.get('home', 0)}-{score.get('away', 0)}"
        claims.append(
            StructuredClaim(
                claim_type=ClaimType.SCORELINE,
                subject="Match Score",
                metric_name="score",
                claimed_value=score_str,
                ground_truth_value=score_str,
                source_event_ids=event_ids,
                details=f"Current official scoreline is {score_str}",
            )
        )

        # 2. Goal Event Claim
        is_goal = (outcome == "Goal")
        claims.append(
            StructuredClaim(
                claim_type=ClaimType.GOAL_EVENT,
                subject="Goal Outcome",
                metric_name="is_goal",
                claimed_value=is_goal,
                ground_truth_value=is_goal,
                source_event_ids=event_ids,
                details=f"Event outcome is '{outcome}' (Goal={is_goal})",
            )
        )

        # 3. Player Identity Claim
        if player_name:
            claims.append(
                StructuredClaim(
                    claim_type=ClaimType.PLAYER_IDENTITY,
                    subject=player_name,
                    metric_name="player_name",
                    claimed_value=player_name,
                    ground_truth_value=player_name,
                    source_event_ids=event_ids,
                    details=f"Actor player is {player_name}",
                )
            )

        # 4. Team Identity Claim
        if team_name:
            claims.append(
                StructuredClaim(
                    claim_type=ClaimType.TEAM_IDENTITY,
                    subject=team_name,
                    metric_name="team_name",
                    claimed_value=team_name,
                    ground_truth_value=team_name,
                    source_event_ids=event_ids,
                    details=f"Possession team is {team_name}",
                )
            )

        # 5. Match Clock Claim
        claims.append(
            StructuredClaim(
                claim_type=ClaimType.MATCH_CLOCK,
                subject="Match Clock",
                metric_name="minute",
                claimed_value=minute,
                ground_truth_value=minute,
                unit="minute",
                source_event_ids=event_ids,
                details=f"Action occurred at minute {minute}",
            )
        )

        # 6. xG Claim (if Shot)
        action_xg = metric_state.get("current_action_xg")
        if action_xg is not None:
            claims.append(
                StructuredClaim(
                    claim_type=ClaimType.METRIC_XG,
                    subject="Expected Goals",
                    metric_name="action_xg",
                    claimed_value=round(action_xg, 2),
                    ground_truth_value=round(action_xg, 2),
                    unit="xG",
                    source_event_ids=event_ids,
                    details=f"Shot xG model value is {action_xg:.2f}",
                )
            )

        # 7. xT Claim (if Pass)
        action_xt = metric_state.get("current_action_xt")
        if action_xt is not None and abs(action_xt) > 0.001:
            claims.append(
                StructuredClaim(
                    claim_type=ClaimType.METRIC_XT,
                    subject="Expected Threat",
                    metric_name="action_xt",
                    claimed_value=round(action_xt, 3),
                    ground_truth_value=round(action_xt, 3),
                    unit="xT",
                    source_event_ids=event_ids,
                    details=f"Pass threat added is {action_xt:.3f}",
                )
            )

        # 8. PPDA Claim
        ppda = metric_state.get("rolling_ppda")
        if ppda is not None:
            if isinstance(ppda, dict):
                defending_team = "away" if team_name == metric_state.get("home_team") else "home"
                val = ppda.get(defending_team) or ppda.get("away") or ppda.get("home")
            else:
                try:
                    val = float(ppda)
                except (ValueError, TypeError):
                    val = None
            if val is not None:
                claims.append(
                    StructuredClaim(
                        claim_type=ClaimType.METRIC_PPDA,
                        subject="Defensive Pressing PPDA",
                        metric_name="rolling_ppda",
                        claimed_value=round(val, 1),
                        ground_truth_value=round(val, 1),
                        unit="PPDA",
                        source_event_ids=event_ids,
                        details=f"Defending team rolling PPDA is {val:.1f}",
                    )
                )

        # 9. Field Tilt Claim
        field_tilt = metric_state.get("field_tilt")
        if field_tilt is not None:
            claims.append(
                StructuredClaim(
                    claim_type=ClaimType.METRIC_FIELD_TILT,
                    subject="Field Tilt",
                    metric_name="field_tilt",
                    claimed_value=round(field_tilt, 1),
                    ground_truth_value=round(field_tilt, 1),
                    unit="%",
                    source_event_ids=event_ids,
                    details=f"Territorial field tilt is {field_tilt:.1f}%",
                )
            )

        # 10. Historical Milestone Claim
        if historical_context and historical_context.get("has_milestone"):
            milestone = historical_context.get("milestone_alert")
            claims.append(
                StructuredClaim(
                    claim_type=ClaimType.HISTORICAL_MILESTONE,
                    subject="Career Milestone",
                    metric_name="milestone",
                    claimed_value=milestone,
                    ground_truth_value=milestone,
                    source_event_ids=event_ids,
                    details=f"Verified historical career milestone: {milestone}",
                )
            )

        return claims
