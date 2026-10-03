"""MatchMind Multi-Agent Orchestrator and Message Bus."""

import asyncio
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
import structlog

from matchmind.agents.base_agent import BaseAgent
from matchmind.models import AgentHealth, AgentMessage, MetricState


logger = structlog.get_logger(__name__)


class AgentOrchestrator:
    """Coordinates agent lifecycle, asynchronous event dispatching,

    shared state replication, and output delivery.
    """

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.message_queue: asyncio.Queue[AgentMessage] = asyncio.Queue()
        self.dead_letter_queue: List[Dict] = []
        self.is_running = False
        self._worker_task: Optional[asyncio.Task] = None

        # Shared Match States (match_id -> MetricState)
        self.match_states: Dict[str, MetricState] = {}

        # Subscriber callbacks (e.g. WebSocket broadcasters, UI dispatchers)
        self.subscribers: List[Callable[[AgentMessage], asyncio.Future]] = []

    def register_agent(self, agent: BaseAgent) -> None:
        """Register an agent into the orchestrator."""
        self.agents[agent.agent_id] = agent
        logger.info("Agent registered", agent_id=agent.agent_id, role=agent.role_name)

    def subscribe(self, callback: Callable[[AgentMessage], asyncio.Future]) -> None:
        """Add an output listener for emitted messages."""
        self.subscribers.append(callback)

    async def publish(self, message: AgentMessage) -> None:
        """Enqueue a message onto the bus."""
        await self.message_queue.put(message)

    def get_cluster_health(self) -> List[AgentHealth]:
        """Collect real-time health data for all registered agents."""
        return [agent.get_health() for agent in self.agents.values()]

    def get_match_state(self, match_id: str) -> Optional[MetricState]:
        """Fetch current shared tactical state for a given match."""
        return self.match_states.get(match_id)

    def update_match_state(self, match_id: str, state: MetricState) -> None:
        """Update shared state."""
        self.match_states[match_id] = state

    async def start(self) -> None:
        """Start the orchestrator event loop."""
        if self.is_running:
            return
        self.is_running = True
        self._worker_task = asyncio.create_task(self._process_loop())
        logger.info("MatchMind Orchestrator started with agents", count=len(self.agents))

    async def stop(self) -> None:
        """Gracefully stop the orchestrator."""
        self.is_running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("MatchMind Orchestrator stopped")

    async def _process_loop(self) -> None:
        """Core consumer loop taking messages off the queue and routing to agents."""
        while self.is_running:
            try:
                # Wait for next incoming message with a timeout to allow graceful stop
                message = await asyncio.wait_for(self.message_queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            # Automatically replicate and maintain shared match state
            if message.payload and "metric_state" in message.payload:
                ms_data = message.payload["metric_state"]
                try:
                    if isinstance(ms_data, MetricState):
                        self.match_states[message.match_id] = ms_data
                    elif isinstance(ms_data, dict):
                        self.match_states[message.match_id] = MetricState(**ms_data)
                except Exception as exc:
                    logger.debug("Failed updating match state", match_id=message.match_id, error=str(exc))

            # Find matching agents
            active_agents = [
                agent for agent in self.agents.values() if agent.can_handle(message)
            ]

            # Notify external subscribers (e.g. WebSocket clients listening to VERIFIED_OUTPUT)
            for subscriber in self.subscribers:
                try:
                    res = subscriber(message)
                    if asyncio.iscoroutine(res):
                        asyncio.create_task(res)
                except Exception as exc:
                    logger.warning("Subscriber callback error", error=str(exc))

            if not active_agents:
                self.message_queue.task_done()
                continue

            # Execute matching agents concurrently
            async def run_agent(target_agent: BaseAgent, in_msg: AgentMessage):
                try:
                    out_messages = await target_agent.execute(in_msg)
                    for out_msg in out_messages:
                        await self.publish(out_msg)
                except Exception as err:
                    logger.error(
                        "Unhandled failure in agent execution",
                        agent_id=target_agent.agent_id,
                        error=str(err),
                    )
                    self.dead_letter_queue.append({
                        "agent_id": target_agent.agent_id,
                        "message_id": in_msg.message_id,
                        "error": str(err),
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })

            tasks = [run_agent(agent, message) for agent in active_agents]
            await asyncio.gather(*tasks, return_exceptions=True)
            self.message_queue.task_done()

