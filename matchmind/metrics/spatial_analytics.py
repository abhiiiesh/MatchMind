"""Spatial Analytics Engine for MatchMind.

Computes 2D tactical heatmaps, pass networks with centroid positions,
and defensive pressing zones across the 120x80 StatsBomb coordinate space.
"""

from collections import defaultdict
import math
from typing import Dict, List, Optional
from matchmind.constants import (
    STATSBOMB_PITCH_LENGTH,
    STATSBOMB_PITCH_WIDTH,
    EventType,
)
from matchmind.models import MatchEvent


class SpatialAnalyticsEngine:
    """Computes advanced spatial intelligence models for tactical visualization."""

    def __init__(
        self,
        pitch_length: float = STATSBOMB_PITCH_LENGTH,
        pitch_width: float = STATSBOMB_PITCH_WIDTH,
    ):
        self.pitch_length = pitch_length
        self.pitch_width = pitch_width

    def compute_heatmap(
        self,
        events: List[MatchEvent],
        team: Optional[str] = None,
        player: Optional[str] = None,
        num_cols: int = 24,
        num_rows: int = 16,
    ) -> Dict:
        """Computes a smoothed 2D spatial action density matrix.

        Returns normalized cell intensity (0.0 to 1.0) across the pitch.
        """
        # Filter relevant events with start coordinates
        filtered: List[MatchEvent] = []
        for ev in events:
            if ev.start_x is None or ev.start_y is None:
                continue
            if team:
                ev_team = ev.team.name if ev.team else ""
                if team.lower() not in ev_team.lower():
                    continue
            if player:
                ev_player = ev.player.name if ev.player else ""
                if player.lower() not in ev_player.lower():
                    continue
            filtered.append(ev)

        # Initialize raw counts grid
        col_width = self.pitch_length / num_cols
        row_height = self.pitch_width / num_rows
        raw_grid = [[0.0 for _ in range(num_cols)] for _ in range(num_rows)]

        for ev in filtered:
            c = min(num_cols - 1, max(0, int(ev.start_x / col_width)))
            r = min(num_rows - 1, max(0, int(ev.start_y / row_height)))
            raw_grid[r][c] += 1.0

        # Apply simple 3x3 Gaussian smoothing kernel
        smoothed_grid = [[0.0 for _ in range(num_cols)] for _ in range(num_rows)]
        kernel = [
            [0.05, 0.1, 0.05],
            [0.1,  0.4, 0.1 ],
            [0.05, 0.1, 0.05],
        ]

        for r in range(num_rows):
            for c in range(num_cols):
                accum = 0.0
                for kr in range(-1, 2):
                    for kc in range(-1, 2):
                        nr, nc = r + kr, c + kc
                        if 0 <= nr < num_rows and 0 <= nc < num_cols:
                            accum += raw_grid[nr][nc] * kernel[kr + 1][kc + 1]
                smoothed_grid[r][c] = accum

        # Find max intensity for normalization
        max_val = max((max(row) for row in smoothed_grid), default=0.0)
        points = []
        for r in range(num_rows):
            for c in range(num_cols):
                val = smoothed_grid[r][c]
                raw_cnt = int(raw_grid[r][c])
                intensity = round(val / max_val, 3) if max_val > 0 else 0.0
                if intensity > 0.03:  # Only export points with notable presence
                    center_x = round((c + 0.5) * col_width, 1)
                    center_y = round((r + 0.5) * row_height, 1)
                    points.append({
                        "x": center_x,
                        "y": center_y,
                        "intensity": intensity,
                        "count": raw_cnt,
                    })

        return {
            "pitch_length": self.pitch_length,
            "pitch_width": self.pitch_width,
            "num_cols": num_cols,
            "num_rows": num_rows,
            "total_actions": len(filtered),
            "max_intensity": 1.0 if max_val > 0 else 0.0,
            "points": points,
        }

    def compute_pass_network(
        self,
        events: List[MatchEvent],
        team: Optional[str] = None,
    ) -> Dict:
        """Computes player average centroid positions and pass volume links."""
        player_coords: Dict[str, List[tuple]] = defaultdict(list)
        player_info_map: Dict[str, dict] = {}
        pass_links: Dict[tuple, int] = defaultdict(int)

        # 1. Track player positions from all involvements
        for ev in events:
            if ev.player and ev.start_x is not None and ev.start_y is not None:
                p_team = ev.team.name if ev.team else ""
                if team and team.lower() not in p_team.lower():
                    continue

                p_name = ev.player.name
                player_coords[p_name].append((ev.start_x, ev.start_y))
                if p_name not in player_info_map:
                    player_info_map[p_name] = {
                        "id": p_name,
                        "name": p_name,
                        "jersey_number": ev.player.jersey_number or 0,
                        "position": ev.player.position or "Player",
                        "team": p_team,
                    }

        # 2. Track successful pass connections between consecutive actions
        for i in range(len(events) - 1):
            cur = events[i]
            nxt = events[i + 1]

            if (
                cur.player
                and nxt.player
                and cur.team
                and nxt.team
                and cur.team.name == nxt.team.name
                and cur.player.name != nxt.player.name
            ):
                if team and team.lower() not in cur.team.name.lower():
                    continue
                if cur.event_type.lower() in ["pass", "carry"] or nxt.event_type.lower() in ["pass", "shot"]:
                    pair = tuple(sorted([cur.player.name, nxt.player.name]))
                    pass_links[pair] += 1

        # 3. Calculate average centroids for top 11 most active players
        sorted_players = sorted(
            player_coords.keys(),
            key=lambda p: len(player_coords[p]),
            reverse=True,
        )[:11]

        nodes = []
        for p_name in sorted_players:
            coords = player_coords[p_name]
            avg_x = round(sum(c[0] for c in coords) / len(coords), 1)
            avg_y = round(sum(c[1] for c in coords) / len(coords), 1)
            meta = player_info_map[p_name]
            nodes.append({
                "id": p_name,
                "name": p_name,
                "jersey_number": meta["jersey_number"],
                "position": meta["position"],
                "x": avg_x,
                "y": avg_y,
                "touch_count": len(coords),
            })

        active_player_set = set(sorted_players)
        links = []
        max_link_count = max(pass_links.values(), default=1)
        for (p1, p2), count in pass_links.items():
            if p1 in active_player_set and p2 in active_player_set and count >= 2:
                weight = round(count / max_link_count, 2)
                links.append({
                    "source": p1,
                    "target": p2,
                    "count": count,
                    "weight": weight,
                })

        return {
            "team": team or (nodes[0]["team"] if nodes else "Team"),
            "nodes": nodes,
            "links": links,
            "total_links": len(links),
        }

    def compute_pressure_zones(
        self,
        events: List[MatchEvent],
        team: Optional[str] = None,
    ) -> Dict:
        """Categorizes authentic defensive pressing actions into pitch thirds.

        Definitions:
        - total_pressures: Count of genuine defensive actions (Pressure, Tackle, Interception, Duel, Recovery, Block).
        - high_press_attacking_third: Defensive actions with start_x >= 80.0 (opponent defensive 1/3).
        - mid_block_middle_third: Defensive actions with 40.0 <= start_x < 80.0 (middle 1/3).
        - low_block_defensive_third: Defensive actions with start_x < 40.0 (own defensive 1/3).
        - high_press_actions: Explicit list of defensive actions executed at start_x >= 80.0.
          (Ordinary passes or shots under pressure are strictly excluded).
        """
        defensive_types = {
            "pressure",
            "tackle",
            "interception",
            "foul committed",
            "duel",
            "ball recovery",
            "block",
            "counterpress",
        }

        attacking_third = 0  # x >= 80 (High Press)
        middle_third = 0     # 40 <= x < 80 (Mid Block)
        defensive_third = 0  # x < 40 (Low Block)
        high_press_points = []
        under_pressure_possession_actions = 0

        for ev in events:
            if ev.start_x is None or ev.start_y is None:
                continue
            p_team = ev.team.name if ev.team else ""
            if team and team.lower() not in p_team.lower():
                continue

            # Track possession under pressure separately
            if ev.under_pressure:
                under_pressure_possession_actions += 1

            ev_type = ev.event_type.lower()
            # Strictly defensive actions apply to pressure zones
            if ev_type in defensive_types:
                x = ev.start_x
                y = ev.start_y
                if x >= 80.0:
                    attacking_third += 1
                    high_press_points.append({
                        "x": round(x, 1),
                        "y": round(y, 1),
                        "player": ev.player.name if ev.player else "Unknown",
                        "type": ev.event_type,
                        "outcome": ev.outcome or "Success",
                    })
                elif x >= 40.0:
                    middle_third += 1
                else:
                    defensive_third += 1

        total = attacking_third + middle_third + defensive_third
        high_press_pct = round((attacking_third / total) * 100, 1) if total > 0 else 0.0

        # Response-level consistency checks
        assert attacking_third + middle_third + defensive_third == total, "Pressure zone breakdown sum must match total"
        assert all(p["x"] >= 80.0 for p in high_press_points), "High press actions must have x >= 80.0"
        assert all(p["type"].lower() in defensive_types for p in high_press_points), "High press actions must be defensive events"

        return {
            "team": team or "All",
            "total_pressures": total,
            "high_press_pct": high_press_pct,
            "actions_under_pressure_faced": under_pressure_possession_actions,
            "breakdown": {
                "high_press_attacking_third": attacking_third,
                "mid_block_middle_third": middle_third,
                "low_block_defensive_third": defensive_third,
            },
            "high_press_actions": high_press_points[:25],
        }


# Global singleton engine
spatial_analytics = SpatialAnalyticsEngine()
