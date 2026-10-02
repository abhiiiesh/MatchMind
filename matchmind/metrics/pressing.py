"""Passes Per Defensive Action (PPDA) & Pressing Intensity Engine."""

from typing import Dict, List
from matchmind.constants import PPDA_BALANCED_PRESS, PPDA_ULTRA_HIGH_PRESS


class PressingEngine:
    """Computes rolling pressing intensity and PPDA in the attacking 60% of the pitch."""

    def __init__(self, window_minutes: int = 5):
        self.window_minutes = window_minutes
        self.history: List[Dict] = []

    def record_action(
        self,
        minute: int,
        team_name: str,
        is_defensive_action: bool,
        is_opponent_pass: bool,
        is_pressing_zone: bool,
    ) -> None:
        """Record an event for rolling PPDA calculation."""
        if not is_pressing_zone:
            return

        self.history.append({
            "minute": minute,
            "team": team_name,
            "is_defensive": is_defensive_action,
            "is_opponent_pass": is_opponent_pass,
        })

    def get_current_ppda(self, current_minute: int, team_name: str, opponent_name: str) -> float:
        """Calculates PPDA for the defending team over the sliding window.

        PPDA = Opponent Passes in Pressing Zone / Team Defensive Actions in Pressing Zone
        """
        min_cutoff = max(0, current_minute - self.window_minutes)
        window_events = [e for e in self.history if e["minute"] >= min_cutoff]

        opponent_passes = sum(
            1 for e in window_events if e["team"] == opponent_name and e["is_opponent_pass"]
        )
        team_def_actions = sum(
            1 for e in window_events if e["team"] == team_name and e["is_defensive"]
        )

        if team_def_actions == 0:
            return 14.5  # Passive baseline when no challenges occur

        ppda = opponent_passes / team_def_actions
        return round(float(ppda), 1)

    @staticmethod
    def classify_press(ppda: float) -> str:
        """Classify tactical pressing intensity."""
        if ppda <= PPDA_ULTRA_HIGH_PRESS:
            return "Aggressive High Press"
        elif ppda <= PPDA_BALANCED_PRESS:
            return "Active Mid-Block Press"
        return "Passive Low-Block Structure"
