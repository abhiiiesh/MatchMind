"""Expected Threat (xT) Grid Model.

Implements Karun Singh's spatial pitch value grid to value progressive
passes and ball carries into threatening zones.
"""

from typing import Tuple
import numpy as np
from matchmind.constants import STATSBOMB_PITCH_LENGTH, STATSBOMB_PITCH_WIDTH


class ExpectedThreatGrid:
    """16x12 Expected Threat lookup and delta calculation."""

    def __init__(self, cols: int = 16, rows: int = 12):
        self.cols = cols
        self.rows = rows
        self.grid = self._initialize_xt_surface()

    def _initialize_xt_surface(self) -> np.ndarray:
        """Construct synthetic xT surface representing probability of scoring within 5 actions.

        Values range from 0.005 in defensive third to 0.35+ in opponent 6-yard box.
        """
        grid = np.zeros((self.rows, self.cols))
        for r in range(self.rows):
            for c in range(self.cols):
                # Normalized distance to goal (col 15, row 5.5 is goal center)
                col_prog = c / (self.cols - 1)  # 0 to 1
                row_centrality = 1.0 - abs(r - (self.rows - 1) / 2.0) / ((self.rows - 1) / 2.0)

                base_threat = 0.005 + 0.28 * (col_prog ** 2.4)
                central_multiplier = 0.6 + 0.4 * row_centrality
                grid[r, c] = base_threat * central_multiplier
        return grid

    def get_cell_coordinates(self, x: float, y: float) -> Tuple[int, int]:
        """Convert StatsBomb yards (0-120, 0-80) to grid row/col index."""
        col = int((x / STATSBOMB_PITCH_LENGTH) * self.cols)
        row = int((y / STATSBOMB_PITCH_WIDTH) * self.rows)
        col = max(0, min(self.cols - 1, col))
        row = max(0, min(self.rows - 1, row))
        return row, col

    def value_action(self, start_x: float, start_y: float, end_x: float, end_y: float) -> float:
        """Calculate the delta in Expected Threat (ΔxT) for ball movement."""
        r_start, c_start = self.get_cell_coordinates(start_x, start_y)
        r_end, c_end = self.get_cell_coordinates(end_x, end_y)

        start_val = self.grid[r_start, c_start]
        end_val = self.grid[r_end, c_end]

        delta_xt = end_val - start_val
        return round(float(delta_xt), 4)


# Alias for backward compatibility
ExpectedThreatModel = ExpectedThreatGrid

