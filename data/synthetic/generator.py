"""Synthetic Football Match Event Generator.

Generates realistic sequences of football match events using stochastic Markov models
and spatial physics. Supports custom scenarios (e.g. Comeback, Dominant Siege, High Pressing).
"""

import math
import random
from typing import Dict, List, Optional
from uuid import uuid4

from matchmind.constants import (
    STATSBOMB_GOAL_CENTER_Y,
    STATSBOMB_GOAL_LINE_X,
    STATSBOMB_PITCH_LENGTH,
    STATSBOMB_PITCH_WIDTH,
    EventType,
)
from matchmind.models import MatchEvent, PlayerInfo, TeamInfo


class SyntheticMatchGenerator:
    """Generates synthetic Premier League matches conforming to StatsBomb schema."""

    def __init__(
        self,
        match_id: Optional[str] = None,
        home_team_name: str = "Arsenal",
        away_team_name: str = "Liverpool",
        scenario: str = "dramatic_comeback",  # "dramatic_comeback", "dominant_siege", "balanced"
    ):
        self.match_id = match_id or f"syn_{uuid4().hex[:8]}"
        self.home_team = TeamInfo(id=1, name=home_team_name)
        self.away_team = TeamInfo(id=2, name=away_team_name)
        self.scenario = scenario

        # Squad definition
        self.home_players = self._generate_squad(self.home_team)
        self.away_players = self._generate_squad(self.away_team)

    def _generate_squad(self, team: TeamInfo) -> List[PlayerInfo]:
        positions = [
            ("GK", "Goalkeeper"),
            ("RB", "Right Back"),
            ("CB1", "Center Back"),
            ("CB2", "Center Back"),
            ("LB", "Left Back"),
            ("DM", "Defensive Midfield"),
            ("CM1", "Central Midfield"),
            ("CM2", "Central Midfield"),
            ("RW", "Right Wing"),
            ("ST", "Striker"),
            ("LW", "Left Wing"),
        ]
        squad = []
        for i, (code, pos) in enumerate(positions, start=1):
            squad.append(
                PlayerInfo(
                    id=team.id * 100 + i,
                    name=f"{team.name} {code}",
                    jersey_number=i,
                    position=pos,
                )
            )
        return squad

    def generate_match(self, total_events: int = 120) -> List[MatchEvent]:
        """Generate a sequential chain of realistic football events."""
        events: List[MatchEvent] = []
        current_time_sec = 0
        in_possession_team = self.home_team
        ball_x = 60.0
        ball_y = 40.0

        for event_idx in range(1, total_events + 1):
            minute = current_time_sec // 60
            second = current_time_sec % 60
            timestamp = f"00:{minute:02d}:{second:02d}.000"

            # Determine tactical phase & event type
            roll = random.random()
            is_near_goal = (ball_x > 95.0 and in_possession_team == self.home_team) or (
                ball_x < 25.0 and in_possession_team == self.away_team
            )

            current_players = self.home_players if in_possession_team == self.home_team else self.away_players
            acting_player = random.choice(current_players[1:])  # Exclude GK mostly

            if is_near_goal and roll < 0.40:
                # Shot attempt!
                event_type = EventType.SHOT
                end_x = STATSBOMB_GOAL_LINE_X if in_possession_team == self.home_team else 0.0
                end_y = STATSBOMB_GOAL_CENTER_Y + random.uniform(-4, 4)

                # Distance calculation for xG
                dist = math.sqrt((end_x - ball_x) ** 2 + (end_y - ball_y) ** 2)
                # Realistic exponential decay xG model
                raw_xg = min(0.92, max(0.02, math.exp(-0.11 * dist) * 0.85))

                is_goal = random.random() < raw_xg
                outcome = "Goal" if is_goal else random.choice(["Saved", "Blocked", "Off Target"])

                event = MatchEvent(
                    index=event_idx,
                    period=1 if minute < 45 else 2,
                    timestamp=timestamp,
                    minute=minute,
                    second=second,
                    match_id=self.match_id,
                    event_type=event_type,
                    team=in_possession_team,
                    player=acting_player,
                    start_x=round(ball_x, 1),
                    start_y=round(ball_y, 1),
                    end_x=round(end_x, 1),
                    end_y=round(end_y, 1),
                    outcome=outcome,
                    under_pressure=random.random() < 0.65,
                    duration_seconds=round(random.uniform(0.3, 0.8), 2),
                    metadata={"shot_statsbomb_xg": round(raw_xg, 3)},
                )
                events.append(event)

                # Reset to kickoff or goal kick
                ball_x, ball_y = 60.0, 40.0
                in_possession_team = (
                    self.away_team if in_possession_team == self.home_team else self.home_team
                )
                current_time_sec += random.randint(25, 45)
                continue

            elif roll < 0.15:
                # Turnover / Defensive Action (Tackle / Interception)
                event_type = random.choice([EventType.INTERCEPTION, EventType.DUEL, EventType.PRESSURE])
                opposing_team = (
                    self.away_team if in_possession_team == self.home_team else self.home_team
                )
                opp_players = self.away_players if opposing_team == self.away_team else self.home_players
                defending_player = random.choice(opp_players[1:8])

                event = MatchEvent(
                    index=event_idx,
                    period=1 if minute < 45 else 2,
                    timestamp=timestamp,
                    minute=minute,
                    second=second,
                    match_id=self.match_id,
                    event_type=event_type,
                    team=opposing_team,
                    player=defending_player,
                    start_x=round(ball_x, 1),
                    start_y=round(ball_y, 1),
                    outcome="Success",
                    under_pressure=True,
                    duration_seconds=round(random.uniform(0.5, 1.5), 2),
                )
                events.append(event)
                # Turnover happens
                in_possession_team = opposing_team
                current_time_sec += random.randint(3, 8)
                continue

            else:
                # Pass or Carry
                event_type = EventType.PASS
                # Move ball towards opponent goal
                direction = 1 if in_possession_team == self.home_team else -1
                delta_x = direction * random.uniform(5, 25)
                delta_y = random.uniform(-15, 15)

                next_x = max(2.0, min(118.0, ball_x + delta_x))
                next_y = max(2.0, min(78.0, ball_y + delta_y))

                event = MatchEvent(
                    index=event_idx,
                    period=1 if minute < 45 else 2,
                    timestamp=timestamp,
                    minute=minute,
                    second=second,
                    match_id=self.match_id,
                    event_type=event_type,
                    team=in_possession_team,
                    player=acting_player,
                    start_x=round(ball_x, 1),
                    start_y=round(ball_y, 1),
                    end_x=round(next_x, 1),
                    end_y=round(next_y, 1),
                    outcome="Success",
                    under_pressure=random.random() < 0.35,
                    duration_seconds=round(random.uniform(0.8, 2.2), 2),
                )
                events.append(event)

                ball_x, ball_y = next_x, next_y
                current_time_sec += random.randint(2, 6)

        return events
