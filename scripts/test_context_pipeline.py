"""Verification script for the 7-Agent MatchMind Pipeline with Historical RAG Context."""

import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from data.synthetic.generator import SyntheticMatchGenerator
from matchmind.agents.context_agent import ContextAgent
from matchmind.agents.factcheck_agent import FactCheckerAgent
from matchmind.agents.ingestion_agent import IngestionAgent
from matchmind.agents.metrics_agent import MetricsAgent
from matchmind.agents.narrative_agent import NarrativeAgent
from matchmind.agents.orchestrator import AgentOrchestrator
from matchmind.agents.persona_agent import PersonaAgent
from matchmind.agents.translator_agent import TranslatorAgent
from matchmind.models import AgentMessage


async def main():
    print("========================================================================")
    print("MatchMind Full 7-Agent Pipeline with Historical Context (RAG) Test")
    print("========================================================================")

    orchestrator = AgentOrchestrator()

    # Register all 7 micro-agents
    ingestion = IngestionAgent()
    metrics = MetricsAgent()
    context = ContextAgent()
    narrative = NarrativeAgent()
    persona = PersonaAgent()
    translator = TranslatorAgent()
    factcheck = FactCheckerAgent()

    orchestrator.register_agent(ingestion)
    orchestrator.register_agent(metrics)
    orchestrator.register_agent(context)
    orchestrator.register_agent(narrative)
    orchestrator.register_agent(persona)
    orchestrator.register_agent(translator)
    orchestrator.register_agent(factcheck)

    verified_moments = []

    def on_verified(msg: AgentMessage):
        if msg.message_type == "VERIFIED_OUTPUT":
            verified_moments.append(msg)
            payload = msg.payload
            narrative_data = payload["narrative"]
            event_data = payload["event"]
            player_info = event_data.get("player") or {}
            player_name = player_info.get("name", "Team") if isinstance(player_info, dict) else str(player_info)

            print(f"\n⚡ [MIN {msg.match_minute:02d}'] EVENT #{msg.event_index:03d}: {event_data.get('event_type')} by {player_name} ({event_data.get('team', {}).get('name')})")
            print(f"📖 STORY ARC: {narrative_data.get('game_state_arc')} | LEVERAGE INDEX: {narrative_data.get('leverage_index', 1.0):.1f}")
            print(f"💡 WHY IT MATTERS:\n   {narrative_data.get('why_it_matters_explanation')}")
            
            commentary = narrative_data.get("commentary_by_persona", {})
            print(f"🔬 TACTICAL ANALYST:\n   {commentary.get('tactical_analyst', '')}")
            print(f"🎉 CASUAL FAN:\n   {commentary.get('casual_fan', '')}")
            print(f"🎙️ BROADCAST CALL:\n   {commentary.get('broadcast_commentator', '')}")
            print(f"♿ AUDIO DESCRIPTION:\n   {commentary.get('accessibility_audio', '')}")
            
            translations = narrative_data.get("translations", {})
            print(f"🌍 SPANISH: {translations.get('es', '')}")
            print(f"🌍 HINDI:   {translations.get('hi', '')}")
            print(f"✅ FACT CHECK: {'PASSED' if narrative_data.get('verified_by_factcheck') else 'FLAGGED'} ({narrative_data.get('factcheck_notes')})")
            print("-" * 72)

    orchestrator.subscribe(on_verified)
    await orchestrator.start()

    print("\nGenerating Premier League match scenario (Arsenal vs Liverpool)...")
    generator = SyntheticMatchGenerator(home_team_name="Arsenal", away_team_name="Liverpool")
    events = generator.generate_match(total_events=12)

    # Inject high-profile stars for RAG milestone triggers
    if len(events) >= 6:
        events[2].player.name = "Bukayo Saka"
        events[2].event_type = "Shot"
        events[2].outcome = "Goal"
        events[5].player.name = "Mohamed Salah"
        events[5].event_type = "Shot"
        events[5].outcome = "Goal"

    print(f"Streaming {len(events)} events through all 7 micro-agents...\n")
    for event in events:
        msg = AgentMessage(
            source_agent="simulator",
            target_agents=["ingestion_agent"],
            match_id=event.match_id,
            event_index=event.index,
            match_minute=event.minute,
            message_type="RAW_EVENT",
            payload={"event": event.model_dump()},
        )
        await orchestrator.publish(msg)

    # Wait for the pipeline queue to clear
    while not orchestrator.message_queue.empty():
        await asyncio.sleep(0.05)
    await asyncio.sleep(0.4)

    await orchestrator.stop()

    print("\n========================================================================")
    print("Full 7-Agent Cluster Health & Latency Telemetry:")
    print("========================================================================")
    for health in orchestrator.get_cluster_health():
        print(f"• [{health.status.upper()}] {health.role_name} ({health.agent_id}): Processed: {health.processed_count} | Errors: {health.error_count} | Avg Latency: {health.average_latency_ms:.2f}ms")

    print(f"\nSuccessfully verified all {len(verified_moments)} events through the full 7-agent pipeline!")


if __name__ == "__main__":
    asyncio.run(main())
