"""Ingestion Agent: Stage 1 of the MatchMind Intelligence Pipeline.

Validates incoming synthetic and raw match events, sanitizes coordinates,
and emits standardized NORMALIZED_EVENT envelopes to the multi-agent bus.
"""

from typing import List
from matchmind.agents.base_agent import BaseAgent
from matchmind.constants import (
    SPADL_PITCH_LENGTH,
    SPADL_PITCH_WIDTH,
    STATSBOMB_PITCH_LENGTH,
    STATSBOMB_PITCH_WIDTH,
)
from matchmind.models import AgentMessage, MatchEvent


class IngestionAgent(BaseAgent):
    """Validates schemas and standardizes spatial coordinates."""

    def __init__(self):
        super().__init__(
            agent_id="ingestion_agent",
            role_name="Data Normalization & Ingestion Specialist",
            supported_message_types=["RAW_EVENT"],
        )

    def _statsbomb_to_meters(self, x: float, y: float) -> tuple[float, float]:
        """Convert StatsBomb coordinates (yards) to standard FIFA / SPADL meters."""
        x_m = (x / STATSBOMB_PITCH_LENGTH) * SPADL_PITCH_LENGTH
        y_m = (y / STATSBOMB_PITCH_WIDTH) * SPADL_PITCH_WIDTH
        return round(x_m, 2), round(y_m, 2)

    async def process(self, message: AgentMessage) -> List[AgentMessage]:
        payload = message.payload
        event_dict = payload.get("event")
        if not event_dict:
            self.log.warning("Received RAW_EVENT message without event payload")
            return []

        # Parse or validate into MatchEvent model
        if isinstance(event_dict, MatchEvent):
            event = event_dict
        else:
            event = MatchEvent(**event_dict)

        # Sanitize and augment coordinates (meters conversion)
        meters_start = None
        meters_end = None
        if event.start_x is not None and event.start_y is not None:
            meters_start = self._statsbomb_to_meters(event.start_x, event.start_y)
        if event.end_x is not None and event.end_y is not None:
            meters_end = self._statsbomb_to_meters(event.end_x, event.end_y)

        # Check penalty box entry (transitioning into StatsBomb 18-yard box: x >= 102, 18 <= y <= 62)
        is_box_entry = False
        if event.end_x is not None and event.end_y is not None:
            in_box_end = event.end_x >= 102.0 and 18.0 <= event.end_y <= 62.0
            in_box_start = (event.start_x or 0.0) >= 102.0 and 18.0 <= (event.start_y or 0.0) <= 62.0
            is_box_entry = in_box_end and not in_box_start
        elif event.start_x is not None and event.start_y is not None:
            is_box_entry = event.start_x >= 102.0 and 18.0 <= event.start_y <= 62.0

        replay_score = message.payload.get("replay_score") or (message.metadata.get("replay_score") if message.metadata else None)
        normalized_payload = {
            "event": event.model_dump(),
            "coordinates_meters": {
                "start": meters_start,
                "end": meters_end,
            },
            "is_attacking_third": (event.start_x or 0.0) >= 80.0,
            "is_box_entry": is_box_entry,
        }
        if replay_score is not None:
            normalized_payload["replay_score"] = replay_score

        out_metadata = dict(message.metadata or {})
        out_metadata["ingested_at_ms"] = message.timestamp.isoformat()
        if replay_score is not None:
            out_metadata["replay_score"] = replay_score

        out_message = AgentMessage(
            source_agent=self.agent_id,
            target_agents=["metrics_agent"],
            match_id=event.match_id,
            event_index=event.index,
            match_minute=event.minute,
            message_type="NORMALIZED_EVENT",
            payload=normalized_payload,
            metadata=out_metadata,
        )

        return [out_message]
