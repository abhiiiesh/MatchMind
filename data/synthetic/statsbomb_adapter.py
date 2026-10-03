"""StatsBomb Open Data Adapter and Match Event Streamer.

Fetches open match data (e.g. historic Premier League, World Cup, UEFA Champions League),
caches it locally, and generates a realistic streaming sequence of events.
"""

import json
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional
import structlog
from statsbombpy import sb

from matchmind.config import settings
from matchmind.constants import STATSBOMB_PITCH_LENGTH, STATSBOMB_PITCH_WIDTH
from matchmind.models import MatchEvent, PlayerInfo, TeamInfo

logger = structlog.get_logger(__name__)


class StatsBombStreamer:
    """Loads and streams StatsBomb match events as standardized MatchEvent instances."""

    def __init__(self, match_id: Optional[str] = None):
        self.match_id = match_id or settings.default_match_id
        self.cache_dir = settings.cache_dir
        self.cache_file = self.cache_dir / f"match_{self.match_id}.json"

    def fetch_or_load_match(self) -> List[Dict]:
        """Load match events from local cache, or fetch from StatsBomb API."""
        if self.cache_file.exists():
            logger.info("Loading match events from cache", cache_file=str(self.cache_file))
            with open(self.cache_file, "r", encoding="utf-8") as f:
                return json.load(f)

        logger.info("Fetching match events from StatsBomb Open Data", match_id=self.match_id)
        try:
            # statsbombpy returns a DataFrame
            events_df = sb.events(match_id=self.match_id)
            # Sort chronologically by period, minute, second
            events_df = events_df.sort_values(by=["period", "minute", "second", "index"])
            records = events_df.to_dict(orient="records")

            # Clean NaNs for JSON serialization
            cleaned_records = []
            for r in records:
                cleaned = {
                    k: (None if (isinstance(v, float) and v != v) else v)
                    for k, v in r.items()
                }
                cleaned_records.append(cleaned)

            # Save to cache
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(cleaned_records, f, indent=2, default=str)

            logger.info("Saved match events to local cache", count=len(cleaned_records))
            return cleaned_records
        except Exception as exc:
            logger.error("Failed to fetch match from StatsBomb API", error=str(exc))
            raise

    def parse_event(self, raw: Dict) -> MatchEvent:
        """Transform a raw StatsBomb event into a normalized MatchEvent."""
        location = raw.get("location")
        pass_end_loc = raw.get("pass_end_location")
        shot_end_loc = raw.get("shot_end_location")

        start_x = location[0] if (isinstance(location, list) and len(location) >= 1) else None
        start_y = location[1] if (isinstance(location, list) and len(location) >= 2) else None

        end_x = None
        end_y = None
        if isinstance(pass_end_loc, list) and len(pass_end_loc) >= 2:
            end_x, end_y = pass_end_loc[0], pass_end_loc[1]
        elif isinstance(shot_end_loc, list) and len(shot_end_loc) >= 2:
            end_x, end_y = shot_end_loc[0], shot_end_loc[1]

        player = None
        if raw.get("player"):
            player = PlayerInfo(
                id=int(raw.get("player_id", 0) or 0),
                name=str(raw.get("player")),
                position=str(raw.get("position")) if raw.get("position") else None,
            )

        team = TeamInfo(
            id=int(raw.get("team_id", 0) or 0),
            name=str(raw.get("team", "Unknown Team")),
        )

        outcome = "Success"
        if raw.get("pass_outcome"):
            outcome = str(raw.get("pass_outcome"))
        elif raw.get("shot_outcome"):
            outcome = str(raw.get("shot_outcome"))

        return MatchEvent(
            event_id=str(raw.get("id", "")),
            index=int(raw.get("index", 0)),
            period=int(raw.get("period", 1)),
            timestamp=str(raw.get("timestamp", "00:00:00.000")),
            minute=int(raw.get("minute", 0)),
            second=int(raw.get("second", 0)),
            match_id=str(self.match_id),
            event_type=str(raw.get("type", "Unknown")),
            team=team,
            player=player,
            start_x=start_x,
            start_y=start_y,
            end_x=end_x,
            end_y=end_y,
            outcome=outcome,
            under_pressure=bool(raw.get("under_pressure", False)),
            duration_seconds=float(raw.get("duration", 0.0) or 0.0),
            metadata={
                "shot_statsbomb_xg": raw.get("shot_statsbomb_xg"),
                "pass_length": raw.get("pass_length"),
                "pass_angle": raw.get("pass_angle"),
                "play_pattern": raw.get("play_pattern"),
                "possession_team": raw.get("possession_team"),
            },
        )

    def get_events(self) -> List[MatchEvent]:
        """Returns the full parsed sequence of match events."""
        raw_events = self.fetch_or_load_match()
        return [self.parse_event(r) for r in raw_events]


# Alias for backward compatibility with implementation plan
StatsBombAdapter = StatsBombStreamer

