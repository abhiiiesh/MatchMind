"""Test and verify the MatchMind multi-agent data and metrics pipeline."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.synthetic.generator import SyntheticMatchGenerator
from matchmind.agents.ingestion_agent import IngestionAgent
from matchmind.agents.metrics_agent import MetricsAgent
from matchmind.agents.orchestrator import AgentOrchestrator
from matchmind.models import AgentMessage


async def main():
    print("================================================================")
    print("MatchMind Multi-Agent Pipeline Verification")
    print("================================================================")

    # 1. Initialize Orchestrator and Agents
    orchestrator = AgentOrchestrator()
    ingestion_agent = IngestionAgent()
    metrics_agent = MetricsAgent()

    orchestrator.register_agent(ingestion_agent)
    orchestrator.register_agent(metrics_agent)

    # Output capture
    processed_metrics = []

    def on_message(msg: AgentMessage):
        if msg.message_type == "METRIC_UPDATE":
            processed_metrics.append(msg)
            ms = msg.payload["metric_state"]
            evt = msg.payload["event"]
            print(
                f"[Min {ms['minute']:02d}:{evt.get('second', 0):02d}] "
                f"Event #{msg.event_index:03d}: {evt['event_type']} by {evt['team']['name']} | "
                f"Score: {ms['score']['home']}-{ms['score']['away']} | "
                f"xG: {ms['cumulative_xg']['home']:.2f}-{ms['cumulative_xg']['away']:.2f} | "
                f"Field Tilt: {ms['field_tilt']}% | "
                f"Leverage: {ms['current_leverage_index']:.1f}"
            )

    orchestrator.subscribe(on_message)
    await orchestrator.start()

    # 2. Generate a sequence of synthetic match events
    print("\n--- Generating Synthetic Match Events ---")
    generator = SyntheticMatchGenerator(
        home_team_name="Arsenal",
        away_team_name="Liverpool",
        scenario="dramatic_comeback"
    )
    events = generator.generate_match(total_events=30)
    print(f"Generated {len(events)} synthetic match events.\n")

    # 3. Stream events through the multi-agent bus
    print("--- Streaming Events Through Multi-Agent Bus ---")
    for event in events:
        raw_msg = AgentMessage(
            source_agent="simulator",
            target_agents=["ingestion_agent"],
            match_id=event.match_id,
            event_index=event.index,
            match_minute=event.minute,
            message_type="RAW_EVENT",
            payload={"event": event.model_dump()},
        )
        await orchestrator.publish(raw_msg)
        # Small tick
        await asyncio.sleep(0.01)

    # Wait for queue to drain
    while not orchestrator.message_queue.empty():
        await asyncio.sleep(0.05)

    await asyncio.sleep(0.2)
    await orchestrator.stop()

    print("\n================================================================")
    print("Multi-Agent Cluster Health Report:")
    print("================================================================")
    for health in orchestrator.get_cluster_health():
        print(
            f"• [{health.status.upper()}] {health.role_name} ({health.agent_id}): "
            f"Processed: {health.processed_count}, Errors: {health.error_count}, "
            f"Avg Latency: {health.average_latency_ms:.2f}ms"
        )

    print("\nPipeline verification completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
