"""Base class for all MatchMind autonomous agents."""

import abc
import time
from datetime import datetime, timezone
from typing import List, Optional
import structlog

from matchmind.models import AgentHealth, AgentMessage

logger = structlog.get_logger(__name__)


class BaseAgent(abc.ABC):
    """Abstract Base Class for all MatchMind micro-agents.

    Provides standardized lifecycle hooks, message processing,
    error recovery, telemetry, and health reporting.
    """

    def __init__(self, agent_id: str, role_name: str, supported_message_types: Optional[List[str]] = None):
        self.agent_id = agent_id
        self.role_name = role_name
        self.supported_message_types = supported_message_types or ["*"]
        self.processed_count = 0
        self.error_count = 0
        self.total_processing_time_ms = 0.0
        self.current_task = "Idle"
        self.status = "healthy"
        self.last_active = datetime.now(timezone.utc)
        self.log = logger.bind(agent_id=self.agent_id, role=self.role_name)

    def can_handle(self, message: AgentMessage) -> bool:
        """Verify if this agent should consume the given message."""
        # Check target agent addressing
        if "*" not in message.target_agents and self.agent_id not in message.target_agents:
            return False

        # Check message type filtering
        if "*" in self.supported_message_types:
            return True

        return message.message_type in self.supported_message_types

    async def execute(self, message: AgentMessage) -> List[AgentMessage]:
        """Wrapper around process that tracks metrics, handles errors, and updates status."""
        start_time = time.perf_counter()
        self.current_task = f"Processing {message.message_type} (#{message.event_index})"
        self.status = "processing"
        self.last_active = datetime.now(timezone.utc)


        try:
            results = await self.process(message)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            self.total_processing_time_ms += elapsed_ms
            self.processed_count += 1
            self.status = "healthy"
            self.current_task = "Idle"

            return results or []
        except Exception as exc:
            self.error_count += 1
            self.status = "degraded"
            self.log.error("Agent error during execution", error=str(exc), event_index=message.event_index)
            recovery_msg = await self.handle_error(exc, message)
            self.current_task = "Recovered from Error"
            if recovery_msg:
                return [recovery_msg]
            return []

    @abc.abstractmethod
    async def process(self, message: AgentMessage) -> List[AgentMessage]:
        """Core domain logic to be implemented by each specialized agent."""
        pass

    async def handle_error(self, error: Exception, message: AgentMessage) -> Optional[AgentMessage]:
        """Default error recovery strategy. Specialized agents can override."""
        self.log.warning("Applying default fallback recovery", error=str(exc) if (exc := str(error)) else "Unknown")
        return None

    def get_health(self) -> AgentHealth:
        """Returns the current health status of this agent."""
        avg_latency = (
            self.total_processing_time_ms / self.processed_count
            if self.processed_count > 0
            else 0.0
        )
        return AgentHealth(
            agent_id=self.agent_id,
            role_name=self.role_name,
            status=self.status,
            last_active=self.last_active,
            processed_count=self.processed_count,
            error_count=self.error_count,
            average_latency_ms=round(avg_latency, 2),
            current_task=self.current_task,
        )
