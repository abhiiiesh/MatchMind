"""High-Fidelity Local Narrative & Commentary Fallback Engine.

Provides deep, context-rich football explanations and persona commentary when
Azure OpenAI is either unconfigured or experiencing latency/rate-limit spikes.
"""

from typing import Dict, Optional
from matchmind.constants import FanPersona


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
    ) -> str:
        """Explains WHY the moment is tactically critical."""
        explanation = ""
        if event_type == "Shot":
            xg_val = action_xg or 0.10
            if xg_val >= 0.40:
                explanation = (
                    f"{player_name}'s high-probability effort (xG: {xg_val:.2f}) was created by breaking "
                    f"the central defensive line. The opposing center-backs were dragged 6+ meters out "
                    f"of shape, presenting a clear shooting lane rarely conceded in Premier League fixtures."
                )
            elif xg_val <= 0.08:
                explanation = (
                    f"An extraordinary low-probability attempt (xG: {xg_val:.2f}). {player_name} converted "
                    f"under heavy defensive pressure from an acute angle, beating the goalkeeper's post-shot "
                    f"positioning through sheer individual technique."
                )
            else:
                explanation = (
                    f"Shot with an expected goal value of {xg_val:.2f}. Generated during sustained pressure "
                    f"(Field Tilt: {field_tilt:.1f}%), forcing the defensive block into a frantic retreat."
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
        """Renders persona-specific commentary."""
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
            return (
                f"[TACTICAL ANALYSIS | {minute}'] {player_name} ({team_name}) executes {event_type}{xg_txt}{xt_txt}. "
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
                return (
                    f"Chance taken by {player_name}! Struck with conviction in the {minute}th minute, "
                    f"testing the keeper's reflexes as {team_name} ramp up the pressure."
                )
            else:
                return (
                    f"{minute}' into the match: {player_name} threads it forward for {team_name}. "
                    f"Patience and purpose in their build-up play."
                )

        elif persona == FanPersona.ACCESSIBILITY_AUDIO:
            return (
                f"[Audio Description] Minute {minute}. {player_name} of {team_name} strikes the ball. "
                f"Current score is {score_str}. Action taking place in the attacking half. {why_it_matters}"
            )

        return f"{minute}' {player_name} with the {event_type} for {team_name}."

