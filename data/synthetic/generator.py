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

    REAL_SQUADS: Dict[str, List[tuple]] = {
        "Arsenal": [
            ("David Raya", 22, "Goalkeeper"),
            ("Ben White", 4, "Right Back"),
            ("William Saliba", 2, "Center Back"),
            ("Gabriel Magalhães", 6, "Center Back"),
            ("Oleksandr Zinchenko", 35, "Left Back"),
            ("Declan Rice", 41, "Defensive Midfield"),
            ("Martin Ødegaard", 8, "Central Midfield"),
            ("Kai Havertz", 29, "Central Midfield"),
            ("Bukayo Saka", 7, "Right Wing"),
            ("Gabriel Jesus", 9, "Striker"),
            ("Gabriel Martinelli", 11, "Left Wing"),
        ],
        "Liverpool": [
            ("Alisson Becker", 1, "Goalkeeper"),
            ("Trent Alexander-Arnold", 66, "Right Back"),
            ("Ibrahima Konaté", 5, "Center Back"),
            ("Virgil van Dijk", 4, "Center Back"),
            ("Andrew Robertson", 26, "Left Back"),
            ("Wataru Endo", 3, "Defensive Midfield"),
            ("Alexis Mac Allister", 10, "Central Midfield"),
            ("Dominik Szoboszlai", 8, "Central Midfield"),
            ("Mohamed Salah", 11, "Right Wing"),
            ("Darwin Núñez", 9, "Striker"),
            ("Luis Díaz", 7, "Left Wing"),
        ],
        "Manchester City": [
            ("Ederson", 31, "Goalkeeper"),
            ("Kyle Walker", 2, "Right Back"),
            ("Rúben Dias", 3, "Center Back"),
            ("Manuel Akanji", 25, "Center Back"),
            ("Joško Gvardiol", 24, "Left Back"),
            ("Rodri", 16, "Defensive Midfield"),
            ("Kevin De Bruyne", 17, "Central Midfield"),
            ("Bernardo Silva", 20, "Central Midfield"),
            ("Phil Foden", 47, "Right Wing"),
            ("Erling Haaland", 9, "Striker"),
            ("Jack Grealish", 10, "Left Wing"),
        ],
        "Chelsea": [
            ("Robert Sánchez", 1, "Goalkeeper"),
            ("Reece James", 24, "Right Back"),
            ("Axel Disasi", 2, "Center Back"),
            ("Levi Colwill", 26, "Center Back"),
            ("Ben Chilwell", 21, "Left Back"),
            ("Moisés Caicedo", 25, "Defensive Midfield"),
            ("Enzo Fernández", 8, "Central Midfield"),
            ("Conor Gallagher", 23, "Central Midfield"),
            ("Cole Palmer", 20, "Right Wing"),
            ("Nicolas Jackson", 15, "Striker"),
            ("Raheem Sterling", 7, "Left Wing"),
        ],
        "Tottenham Hotspur": [
            ("Guglielmo Vicario", 13, "Goalkeeper"),
            ("Pedro Porro", 23, "Right Back"),
            ("Cristian Romero", 17, "Center Back"),
            ("Micky van de Ven", 37, "Center Back"),
            ("Destiny Udogie", 38, "Left Back"),
            ("Yves Bissouma", 8, "Defensive Midfield"),
            ("Pape Matar Sarr", 29, "Central Midfield"),
            ("James Maddison", 10, "Central Midfield"),
            ("Dejan Kulusevski", 21, "Right Wing"),
            ("Son Heung-min", 7, "Striker"),
            ("Brennan Johnson", 22, "Left Wing"),
        ],
        "Newcastle United": [
            ("Nick Pope", 22, "Goalkeeper"),
            ("Kieran Trippier", 2, "Right Back"),
            ("Fabian Schär", 5, "Center Back"),
            ("Sven Botman", 4, "Center Back"),
            ("Dan Burn", 33, "Left Back"),
            ("Bruno Guimarães", 39, "Defensive Midfield"),
            ("Sean Longstaff", 36, "Central Midfield"),
            ("Joelinton", 7, "Central Midfield"),
            ("Miguel Almirón", 24, "Right Wing"),
            ("Alexander Isak", 14, "Striker"),
            ("Anthony Gordon", 10, "Left Wing"),
        ],
    }

    def _generate_squad(self, team: TeamInfo) -> List[PlayerInfo]:
        # Check if known Premier League squad exists
        for team_key, roster in self.REAL_SQUADS.items():
            if team_key.lower() in team.name.lower() or team.name.lower() in team_key.lower():
                squad = []
                for idx, (p_name, jersey, pos) in enumerate(roster, start=1):
                    squad.append(
                        PlayerInfo(
                            id=team.id * 100 + idx,
                            name=p_name,
                            jersey_number=jersey,
                            position=pos,
                        )
                    )
                return squad

        # Positional fallback for custom/synthetic club names
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
