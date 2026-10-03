"""Comprehensive End-to-End Test for Narrative and Persona Intelligence Pipeline."""

import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from data.synthetic.generator import SyntheticMatchGenerator
from matchmind.agents.ingestion_agent import IngestionAgent
from matchmind.agents.metrics_agent import MetricsAgent
from matchmind.agents.narrative_agent import NarrativeAgent
from matchmind.agents.orchestrator import AgentOrchestrator
from matchmind.agents.persona_agent import PersonaAgent
from matchmind.models import AgentMessage


async def main():
    print("========================================================================")
    print("MatchMind End-to-End Narrative & Personalization Pipeline Test")
    print("========================================================================")

    orchestrator = AgentOrchestrator()

    # Instantiate all 4 agents in the current pipeline
    ingestion = IngestionAgent()
    metrics = MetricsAgent()
    narrative = NarrativeAgent()
    persona = PersonaAgent()

    orchestrator.register_agent(ingestion)
    orchestrator.register_agent(metrics)
    orchestrator.register_agent(narrative)
    orchestrator.register_agent(persona)

    captured_outputs = []

    def handle_broadcast(msg: AgentMessage):
        if msg.message_type == "PERSONA_COMMENTARY":
            captured_outputs.append(msg)
            narrative_data = msg.payload["narrative"]
            event_data = msg.payload["event"]
            minute = msg.match_minute

            print(f"\n⚡ [MINUTE {minute:02d}] EVENT #{msg.event_index:03d}: {event_data['event_type']} by {event_data['team']['name']}")
            print(f"📖 STORY ARC: {narrative_data['game_state_arc']} | LEVERAGE INDEX: {narrative_data['leverage_index']:.1f}")
            print(f"🔍 WHY IT MATTERS:\n   {narrative_data['why_it_matters_explanation']}")
            print(f"🔬 TACTICAL ANALYST:\n   {narrative_data['commentary_by_persona']['tactical_analyst']}")
            print(f"🎉 CASUAL FAN:\n   {narrative_data['commentary_by_persona']['casual_fan']}")
            print(f"🎙️ BROADCAST CALL:\n   {narrative_data['commentary_by_persona']['broadcast_commentator']}")
            print("-" * 72)

    orchestrator.subscribe(handle_broadcast)
    await orchestrator.start()

    print("\nGenerating simulated match scenario (Arsenal vs Liverpool)...")
    generator = SyntheticMatchGenerator(
        home_team_name="Arsenal",
        away_team_name="Liverpool",
        scenario="dramatic_comeback",
    )
    # Generate 15 events to observe progressive tactical narrative evolution
    events = generator.generate_match(total_events=15)

    print(f"Streaming {len(events)} events through the 4-agent cluster...\n")
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
        await asyncio.sleep(0.02)

    # Wait for all message queues to drain
    while not orchestrator.message_queue.empty():
        await asyncio.sleep(0.05)

    await asyncio.sleep(0.3)
    await orchestrator.stop()

    print("\n========================================================================")
    print("Multi-Agent Cluster Performance & Health Telemetry:")
    print("========================================================================")
    for health in orchestrator.get_cluster_health():
        print(
            f"• [{health.status.upper()}] {health.role_name} ({health.agent_id}): "
            f"Processed: {health.processed_count} messages | "
            f"Errors: {health.error_count} | Avg Latency: {health.average_latency_ms:.2f}ms"
        )

    print(f"\nSuccessfully generated {len(captured_outputs)} persona-adapted narrative moments!")


if __name__ == "__main__":
    asyncio.run(main())
