"""Game State and Story Arc Classifier for MatchMind."""

from typing import Dict
from matchmind.constants import (
    FIELD_TILT_DOMINANT,
    LEVERAGE_INDEX_EXTREME,
    LEVERAGE_INDEX_HIGH,
    PPDA_ULTRA_HIGH_PRESS,
)
from matchmind.models import MetricState


class StoryArcClassifier:
    """Classifies the psychological and tactical macro-narrative of a football match."""

    @staticmethod
    def classify_arc(metric_state: MetricState) -> str:
        minute = metric_state.minute
        score_diff = metric_state.score.get("home", 0) - metric_state.score.get("away", 0)
        field_tilt = metric_state.field_tilt

        leverage = metric_state.current_leverage_index
        home_ppda = metric_state.rolling_ppda.get("home", 11.5)
        away_ppda = metric_state.rolling_ppda.get("away", 11.5)

        # 1. Late-game high drama / chaotic climax
        if minute >= 80:
            if leverage >= LEVERAGE_INDEX_EXTREME:
                return "Climactic Final Siege: Match on a Knife Edge"
            elif abs(score_diff) == 1:
                leader = metric_state.home_team if score_diff > 0 else metric_state.away_team
                chaser = metric_state.away_team if score_diff > 0 else metric_state.home_team
                return f"Desperate Climax: {chaser} Pushing for Equalizer against {leader}"
            elif score_diff == 0:
                return "Late Stalemate: Both Sides Risking Transitions for the Winner"

        # 2. Pressing Suffocation vs. Counter Ambush
        if home_ppda <= PPDA_ULTRA_HIGH_PRESS and field_tilt >= FIELD_TILT_DOMINANT:
            return f"Suffocation Phase: {metric_state.home_team} High-Press Siege"
        elif away_ppda <= PPDA_ULTRA_HIGH_PRESS and field_tilt <= (100.0 - FIELD_TILT_DOMINANT):
            return f"Suffocation Phase: {metric_state.away_team} High-Press Siege"

        # 3. Territorial Dominance
        if field_tilt >= 72.0:
            return f"Total Territorial Control by {metric_state.home_team}"
        elif field_tilt <= 28.0:
            return f"Total Territorial Control by {metric_state.away_team}"

        # 4. Opening Phases
        if minute < 15:
            return "Early Reconnaissance: Tactical Shape Probing"

        # 5. Default Mid-game balance
        if abs(score_diff) >= 2:
            leader = metric_state.home_team if score_diff > 0 else metric_state.away_team
            return f"Commanding Game Management by {leader}"

        return "Tactical Chess Match: Balanced Midfield Battle"
