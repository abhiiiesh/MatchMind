"""MatchMind Interactive Replay Session and Timeline Controller.

Provides scrubbable timeline playback, pause/resume, playback speed modulation,
and direct jumping to key Premier League highlights.
"""

import asyncio
import math
import random
from typing import Dict, List, Optional
import structlog

from matchmind.constants import (
    STATSBOMB_GOAL_CENTER_Y,
    STATSBOMB_GOAL_LINE_X,
    EventType,
)
from matchmind.models import AgentMessage, MatchEvent, PlayerInfo, TeamInfo
from matchmind.playback.match_catalog import (
    KeyMoment,
    MatchSummary,
    get_match,
)
from data.synthetic.statsbomb_adapter import StatsBombStreamer

logger = structlog.get_logger(__name__)


class ReplaySession:
    """Manages active match event replay, timeline seeking, and playback state."""

    def __init__(self, orchestrator=None):
        self.orchestrator = orchestrator
        self.active_match_id: Optional[str] = None
        self.summary: Optional[MatchSummary] = None
        self.events: List[MatchEvent] = []
        self.current_index: int = 0
        self.is_playing: bool = False
        self.speed: float = 1.0
        self._playback_task: Optional[asyncio.Task] = None

    def get_summary(self) -> Optional[MatchSummary]:
        return self.summary

    def load_match(self, match_id: str) -> MatchSummary:
        """Loads a match from catalog and generates/fetches its timeline event stream."""
        summary = get_match(match_id)
        if not summary:
            raise ValueError(f"Match '{match_id}' not found in catalog")

        # Stop any existing playback
        self.pause()

        self.active_match_id = match_id
        self.summary = summary
        self.current_index = 0

        # Load events
        if summary.source_type == "statsbomb" and summary.statsbomb_match_id:
            logger.info("Loading StatsBomb match for replay", match_id=match_id)
            streamer = StatsBombStreamer(match_id=summary.statsbomb_match_id)
            self.events = streamer.get_events()
        else:
            logger.info("Synthesizing curated fixture timeline", match_id=match_id)
            self.events = self._generate_curated_events(summary)

        logger.info(
            "Replay match loaded",
            match_id=match_id,
            total_events=len(self.events),
            key_moments=len(summary.key_moments),
        )
        return summary

    def _generate_curated_events(self, summary: MatchSummary) -> List[MatchEvent]:
        """Generates a realistic 90-minute sequence of events with exact key moments embedded."""
        events: List[MatchEvent] = []
        home_team = TeamInfo(id=1, name=summary.home_team)
        away_team = TeamInfo(id=2, name=summary.away_team)

        home_squad = summary.home_squad or [
            PlayerInfo(id=100 + i, name=f"{summary.home_team} Player {i}") for i in range(1, 12)
        ]
        away_squad = summary.away_squad or [
            PlayerInfo(id=200 + i, name=f"{summary.away_team} Player {i}") for i in range(1, 12)
        ]

        def find_player(team_name: str, player_name: str) -> PlayerInfo:
            squad = home_squad if team_name == summary.home_team else away_squad
            for p in squad:
                if player_name.lower() in p.name.lower() or p.name.lower() in player_name.lower():
                    return p
            return squad[random.randint(1, len(squad) - 1)]

        # Map key moments by minute for deterministic embedding
        moments_by_min: Dict[int, KeyMoment] = {m.minute: m for m in summary.key_moments}

        event_idx = 1
        current_time_sec = 0
        ball_x, ball_y = 60.0, 40.0
        in_possession = home_team

        # Generate roughly 1 event per 40-60 game seconds across 95 minutes
        while current_time_sec <= summary.duration_minutes * 60:
            minute = current_time_sec // 60
            second = current_time_sec % 60
            period = 1 if minute < 45 else 2
            timestamp = f"00:{minute:02d}:{second:02d}.000"

            # Check if this minute has an embedded key moment
            if minute in moments_by_min:
                km = moments_by_min.pop(minute)
                km_team = home_team if km.team == summary.home_team else away_team
                km_player = find_player(km.team, km.player)

                if km.moment_type == "GOAL":
                    goal_x = STATSBOMB_GOAL_LINE_X if km_team == home_team else 0.0
                    goal_y = STATSBOMB_GOAL_CENTER_Y + random.uniform(-2, 2)
                    ev = MatchEvent(
                        index=event_idx,
                        period=period,
                        timestamp=timestamp,
                        minute=minute,
                        second=second,
                        match_id=summary.match_id,
                        event_type=EventType.SHOT,
                        team=km_team,
                        player=km_player,
                        start_x=round(ball_x, 1),
                        start_y=round(ball_y, 1),
                        end_x=round(goal_x, 1),
                        end_y=round(goal_y, 1),
                        outcome="Goal",
                        under_pressure=True,
                        duration_seconds=1.2,
                        metadata={
                            "shot_statsbomb_xg": km.xg or 0.65,
                            "key_moment_id": km.id,
                            "description": km.description,
                            "score_after": km.score_after,
                            "leverage_index": km.leverage_index,
                        },
                    )
                    events.append(ev)
                    event_idx += 1
                    ball_x, ball_y = 60.0, 40.0
                    in_possession = away_team if km_team == home_team else home_team
                    current_time_sec += random.randint(45, 75)
                    continue

                elif km.moment_type == "RED_CARD":
                    ev = MatchEvent(
                        index=event_idx,
                        period=period,
                        timestamp=timestamp,
                        minute=minute,
                        second=second,
                        match_id=summary.match_id,
                        event_type=EventType.FOUL_COMMITTED,
                        team=km_team,
                        player=km_player,
                        start_x=round(ball_x, 1),
                        start_y=round(ball_y, 1),
                        outcome="Red Card",
                        under_pressure=True,
                        duration_seconds=2.0,
                        metadata={
                            "card": "Red Card",
                            "key_moment_id": km.id,
                            "description": km.description,
                            "leverage_index": km.leverage_index,
                        },
                    )
                    events.append(ev)
                    event_idx += 1
                    current_time_sec += random.randint(30, 60)
                    continue

                elif km.moment_type == "BIG_CHANCE":
                    goal_x = STATSBOMB_GOAL_LINE_X if km_team == home_team else 0.0
                    ev = MatchEvent(
                        index=event_idx,
                        period=period,
                        timestamp=timestamp,
                        minute=minute,
                        second=second,
                        match_id=summary.match_id,
                        event_type=EventType.SHOT,
                        team=km_team,
                        player=km_player,
                        start_x=round(ball_x, 1),
                        start_y=round(ball_y, 1),
                        end_x=round(goal_x, 1),
                        end_y=round(STATSBOMB_GOAL_CENTER_Y + 4.5, 1),
                        outcome="Off Target",
                        under_pressure=True,
                        duration_seconds=0.9,
                        metadata={
                            "shot_statsbomb_xg": km.xg or 0.45,
                            "key_moment_id": km.id,
                            "description": km.description,
                            "leverage_index": km.leverage_index,
                        },
                    )
                    events.append(ev)
                    event_idx += 1
                    current_time_sec += random.randint(25, 45)
                    continue

            # Standard Flow: Pass, Carry, or Turnover
            current_squad = home_squad if in_possession == home_team else away_squad
            actor = random.choice(current_squad[1:])  # exclude GK mostly

            roll = random.random()
            if roll < 0.20:
                # Defensive duel or pressure
                opp_team = away_team if in_possession == home_team else home_team
                opp_squad = away_squad if opp_team == away_team else home_squad
                defender = random.choice(opp_squad[1:7])
                ev = MatchEvent(
                    index=event_idx,
                    period=period,
                    timestamp=timestamp,
                    minute=minute,
                    second=second,
                    match_id=summary.match_id,
                    event_type=random.choice([EventType.PRESSURE, EventType.INTERCEPTION, EventType.DUEL]),
                    team=opp_team,
                    player=defender,
                    start_x=round(ball_x, 1),
                    start_y=round(ball_y, 1),
                    outcome="Success",
                    under_pressure=True,
                    duration_seconds=1.0,
                )
                events.append(ev)
                event_idx += 1
                in_possession = opp_team
                current_time_sec += random.randint(10, 25)
            else:
                # Pass or Carry
                direction = 1 if in_possession == home_team else -1
                next_x = max(5.0, min(115.0, ball_x + direction * random.uniform(8, 28)))
                next_y = max(5.0, min(75.0, ball_y + random.uniform(-18, 18)))
                ev = MatchEvent(
                    index=event_idx,
                    period=period,
                    timestamp=timestamp,
                    minute=minute,
                    second=second,
                    match_id=summary.match_id,
                    event_type=EventType.PASS,
                    team=in_possession,
                    player=actor,
                    start_x=round(ball_x, 1),
                    start_y=round(ball_y, 1),
                    end_x=round(next_x, 1),
                    end_y=round(next_y, 1),
                    outcome="Success",
                    under_pressure=random.random() < 0.35,
                    duration_seconds=round(random.uniform(1.0, 2.5), 1),
                )
                events.append(ev)
                event_idx += 1
                ball_x, ball_y = next_x, next_y
                current_time_sec += random.randint(15, 35)

        return events

    def get_timeline_info(self) -> Dict:
        """Returns metadata for frontend scrubber timeline."""
        if not self.summary or not self.events:
            return {
                "match_id": self.active_match_id,
                "total_events": 0,
                "current_index": 0,
                "current_minute": 0,
                "duration_minutes": 90,
                "is_playing": self.is_playing,
                "speed": self.speed,
                "key_moments": [],
            }

        cur_ev = self.events[self.current_index] if 0 <= self.current_index < len(self.events) else None
        cur_min = cur_ev.minute if cur_ev else 0

        # Accurately compute score at the current replay minute
        cur_home = 0
        cur_away = 0
        if self.summary:
            for km in self.summary.key_moments:
                if km.moment_type == "GOAL" and km.minute <= cur_min:
                    if km.team == self.summary.home_team:
                        cur_home += 1
                    else:
                        cur_away += 1

        return {
            "match_id": self.summary.match_id,
            "title": self.summary.title,
            "competition": self.summary.competition,
            "home_team": self.summary.home_team,
            "away_team": self.summary.away_team,
            "home_badge_color": self.summary.home_badge_color,
            "away_badge_color": self.summary.away_badge_color,
            "final_score": self.summary.final_score,
            "current_score": {"home": cur_home, "away": cur_away},
            "duration_minutes": self.summary.duration_minutes,
            "total_events": len(self.events),
            "current_index": self.current_index,
            "current_minute": cur_min,
            "current_second": cur_ev.second if cur_ev else 0,
            "is_playing": self.is_playing,
            "speed": self.speed,
            "key_moments": [m.model_dump() for m in self.summary.key_moments],
        }

    async def seek_to_minute(self, target_minute: int) -> Optional[MatchEvent]:
        """Fast-forwards or rewinds timeline to the closest event to target_minute."""
        if not self.events:
            return None

        # Find closest event index
        best_idx = 0
        min_diff = 999
        for i, ev in enumerate(self.events):
            diff = abs(ev.minute - target_minute)
            if diff < min_diff:
                min_diff = diff
                best_idx = i

        self.current_index = best_idx
        target_event = self.events[self.current_index]

        # Re-broadcast state by publishing to orchestrator
        if self.orchestrator:
            await self._dispatch_event(target_event)

        logger.info("Seeked replay timeline", target_minute=target_minute, event_idx=best_idx)
        return target_event

    async def seek_to_moment(self, moment_id: str) -> Optional[MatchEvent]:
        """Jumps directly to a designated key moment highlight."""
        if not self.summary:
            return None

        target_km = next((m for m in self.summary.key_moments if m.id == moment_id), None)
        if not target_km:
            return None

        return await self.seek_to_minute(target_km.minute)

    async def step(self, forward: bool = True) -> Optional[MatchEvent]:
        """Step one event forward or backward."""
        if not self.events:
            return None

        if forward:
            if self.current_index < len(self.events) - 1:
                self.current_index += 1
        else:
            if self.current_index > 0:
                self.current_index -= 1

        ev = self.events[self.current_index]
        if self.orchestrator:
            await self._dispatch_event(ev)
        return ev

    def play(self, speed: float = 1.0) -> None:
        """Starts asynchronous playback of events along the timeline."""
        if not self.events:
            return

        self.speed = speed
        self.is_playing = True

        if self._playback_task and not self._playback_task.done():
            self._playback_task.cancel()

        self._playback_task = asyncio.create_task(self._playback_loop())
        logger.info("Replay playback started", speed=speed)

    def pause(self) -> None:
        """Pauses timeline playback."""
        self.is_playing = False
        if self._playback_task and not self._playback_task.done():
            self._playback_task.cancel()
        logger.info("Replay playback paused")

    async def _playback_loop(self) -> None:
        """Continuous event publishing loop."""
        base_delay = 1.2
        try:
            while self.is_playing and self.current_index < len(self.events) - 1:
                self.current_index += 1
                ev = self.events[self.current_index]
                if self.orchestrator:
                    await self._dispatch_event(ev)

                # Delay scaled by speed
                delay = max(0.1, base_delay / self.speed)
                await asyncio.sleep(delay)

            self.is_playing = False
            logger.info("Playback reached end of match events")
        except asyncio.CancelledError:
            self.is_playing = False

    async def _dispatch_event(self, event: MatchEvent) -> None:
        """Publishes RAW_EVENT to orchestrator."""
        raw_msg = AgentMessage(
            source_agent="replay_engine",
            target_agents=["ingestion_agent"],
            match_id=event.match_id,
            event_index=event.index,
            match_minute=event.minute,
            message_type="RAW_EVENT",
            payload={"event": event.model_dump()},
        )
        await self.orchestrator.publish(raw_msg)


# Global replay session singleton
replay_session = ReplaySession()
