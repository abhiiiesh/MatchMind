"""Expected Goals (xG) Statistical Model.

Calculates scoring probability based on spatial geometry, angle, distance,
and defensive pressure context.
"""

import math
from typing import Optional
from matchmind.constants import (
    STATSBOMB_GOAL_CENTER_Y,
    STATSBOMB_GOAL_LINE_X,
    STATSBOMB_GOAL_WIDTH,
)


class ExpectedGoalsModel:
    """Mathematical Expected Goals estimator."""

    def __init__(self):
        # Calibrated weights based on Premier League historical open data
        self.w_distance = -0.098
        self.w_angle = 1.35
        self.w_pressure = -0.32
        self.intercept = -0.75

    def calculate_xg(
        self,
        x: float,
        y: float,
        under_pressure: bool = False,
        precomputed_xg: Optional[float] = None,
    ) -> float:
        """Compute the xG probability [0.0, 1.0] for a shot."""
        if precomputed_xg is not None and precomputed_xg > 0.0:
            return round(min(0.99, max(0.01, precomputed_xg)), 3)

        # Distance to center of target goal (120, 40 in StatsBomb yards)
        dx = STATSBOMB_GOAL_LINE_X - x
        dy = STATSBOMB_GOAL_CENTER_Y - y
        distance = math.sqrt(dx * dx + dy * dy)

        if distance <= 0.5:
            return 0.95

        # Visual angle subtended by the goal posts (8 yards wide)
        half_w = STATSBOMB_GOAL_WIDTH / 2.0
        angle_rad = abs(
            math.atan2(y - (STATSBOMB_GOAL_CENTER_Y - half_w), dx)
            - math.atan2(y - (STATSBOMB_GOAL_CENTER_Y + half_w), dx)
        )

        logit = (
            self.intercept
            + (self.w_distance * distance)
            + (self.w_angle * angle_rad)
            + (self.w_pressure * (1.0 if under_pressure else 0.0))
        )

        # Sigmoid activation
        xg = 1.0 / (1.0 + math.exp(-logit))
        return round(min(0.96, max(0.01, xg)), 3)
