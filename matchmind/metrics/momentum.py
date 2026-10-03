"""Match Momentum and Leverage Index Engine for MatchMind.

Calculates continuous rolling momentum curves [-100.0 to +100.0] comparing
territorial pressure, progressive xT, and shot danger between competing teams.
"""

from typing import Dict, List, Optional
import structlog

from matchmind.constants import (
    FIELD_TILT_DOMINANT,
    LEVERAGE_INDEX_EXTREME,
    LEVERAGE_INDEX_HIGH,
    MOMENTUM_SHIFT_THRESHOLD,
)

logger = structlog.get_logger(__name__)


class MomentumEngine:
    """Computes rolling match momentum and emotional leverage."""

    def __init__(self, window_minutes: int = 5):
        self.window_minutes = window_minutes
        self.timeline: List[Dict[str, float]] = []
        self.recent_events: List[Dict] = []
        self.prev_momentum = 0.0

    def calculate_momentum_value(
        self,
        minute: int,
        field_tilt: float,
        home_xg: float,
        away_xg: float,
        home_xt_added: float,
        away_xt_added: float,
        home_ppda: float,
        away_ppda: float,
    ) -> float:
        """Computes current momentum value [-100.0 to +100.0].

        Positive = Home dominance, Negative = Away dominance.
        """
        # 1. Territorial component (weight: 40%)
        # field_tilt is home percentage [0, 100] -> scale to [-40, +40]
        tilt_score = (field_tilt - 50.0) * 0.8

        # 2. Progressive xT difference (weight: 35%)
        # Scale typical xT differential (-0.5 to +0.5) to [-35, +35]
        xt_diff = (home_xt_added - away_xt_added) * 70.0
        xt_score = max(-35.0, min(35.0, xt_diff))

        # 3. Cumulative xG differential (weight: 15%)
        xg_diff = (home_xg - away_xg) * 10.0
        xg_score = max(-15.0, min(15.0, xg_diff))

        # 4. Pressing intensity advantage (weight: 10%)
        # Lower PPDA = more aggressive press
        # If home PPDA is lower than away PPDA, home is pressing harder
        ppda_adv = (away_ppda - home_ppda) * 1.5
        ppda_score = max(-10.0, min(10.0, ppda_adv))

        raw_momentum = tilt_score + xt_score + xg_score + ppda_score
        clamped = max(-100.0, min(100.0, raw_momentum))
        return round(clamped, 1)

    def record_step(
        self,
        minute: int,
        field_tilt: float,
        home_xg: float,
        away_xg: float,
        home_xt_added: float,
        away_xt_added: float,
        home_ppda: float,
        away_ppda: float,
        event_type: str = "Pass",
    ) -> Dict[str, float]:
        """Records momentum point and detects significant tactical shifts."""
        current_value = self.calculate_momentum_value(
            minute=minute,
            field_tilt=field_tilt,
            home_xg=home_xg,
            away_xg=away_xg,
            home_xt_added=home_xt_added,
            away_xt_added=away_xt_added,
            home_ppda=home_ppda,
            away_ppda=away_ppda,
        )

        delta = abs(current_value - self.prev_momentum)
        is_shift = delta >= MOMENTUM_SHIFT_THRESHOLD or (
            (self.prev_momentum > 15.0 and current_value < -15.0)
            or (self.prev_momentum < -15.0 and current_value > 15.0)
        )

        entry = {
            "minute": minute,
            "value": current_value,
            "is_shift": is_shift,
            "event_type": event_type,
        }

        self.timeline.append(entry)
        self.prev_momentum = current_value
        return entry

    @staticmethod
    def calculate_leverage_index(
        minute: int,
        score_diff: int,
        action_xg: Optional[float] = None,
        is_goal: bool = False,
    ) -> float:
        """Calculates emotional volatility & importance of current match moment.

        Baseline = 1.0; High drama >= 3.0; Extreme clutch >= 5.0.
        """
        # Time pressure component (steep curve after minute 70)
        time_factor = 1.0 + (minute / 90.0) ** 2.2

        # Margin sensitivity
        abs_diff = abs(score_diff)
        if abs_diff == 0:
            margin_factor = 2.4
        elif abs_diff == 1:
            margin_factor = 2.0
        elif abs_diff == 2:
            margin_factor = 1.1
        else:
            margin_factor = 0.5

        # Action danger factor
        danger_factor = 1.0 + (action_xg or 0.0) * 3.5
        if is_goal:
            danger_factor *= 1.8

        leverage = time_factor * margin_factor * danger_factor
        return round(float(leverage), 2)

    def get_timeline(self, max_points: int = 50) -> List[Dict[str, float]]:
        """Returns the recent momentum timeline."""
        return self.timeline[-max_points:]
