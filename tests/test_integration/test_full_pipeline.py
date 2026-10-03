"""Comprehensive Integration Test Suite for MatchMind Multi-Agent Platform."""

import asyncio
import pytest
from httpx import ASGITransport, AsyncClient

from data.synthetic.generator import SyntheticMatchGenerator
from matchmind.agents.factcheck_agent import FactCheckerAgent
from matchmind.agents.ingestion_agent import IngestionAgent
from matchmind.agents.metrics_agent import MetricsAgent
from matchmind.agents.context_agent import ContextAgent
from matchmind.agents.narrative_agent import NarrativeAgent
from matchmind.agents.orchestrator import AgentOrchestrator
from matchmind.agents.persona_agent import PersonaAgent
from matchmind.agents.translator_agent import TranslatorAgent
from matchmind.delivery.rest_api import app
from matchmind.models import AgentMessage


@pytest.mark.asyncio
async def test_full_7_agent_pipeline():
    """Verify that events cascade through all 7 specialized agents to VERIFIED_OUTPUT."""
    orchestrator = AgentOrchestrator()

    # Register all 7 specialized agents
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


    verified_outputs = []

    def on_verified(msg: AgentMessage):
        if msg.message_type == "VERIFIED_OUTPUT":
            verified_outputs.append(msg)

    orchestrator.subscribe(on_verified)
    await orchestrator.start()

    # Generate 5 test match events
    generator = SyntheticMatchGenerator(home_team_name="Arsenal", away_team_name="Liverpool")
    events = generator.generate_match(total_events=5)

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

    # Allow pipeline to process
    await asyncio.sleep(0.5)
    await orchestrator.stop()

    assert len(verified_outputs) == 5, f"Expected 5 verified outputs, got {len(verified_outputs)}"

    # Check sample verified output contents
    sample = verified_outputs[0]
    payload = sample.payload
    narrative = payload["narrative"]

    # 1. Personas present
    commentary = narrative["commentary_by_persona"]
    assert "tactical_analyst" in commentary
    assert "casual_fan" in commentary
    assert "broadcast_commentator" in commentary
    assert "accessibility_audio" in commentary

    # 2. Translations present
    translations = narrative["translations"]
    assert "en" in translations
    assert "es" in translations
    assert "hi" in translations

    # 3. Fact check verification passed
    assert narrative["verified_by_factcheck"] is True


@pytest.mark.asyncio
async def test_rest_api_endpoints():
    """Verify that FastAPI endpoints return valid status and telemetry."""
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Root health check
            res_root = await client.get("/")
            assert res_root.status_code == 200
            data = res_root.json()
            assert data["status"] == "online"

            # 2. Agents status endpoint
            res_agents = await client.get("/api/agents/status")
            assert res_agents.status_code == 200
            agents_data = res_agents.json()
            assert "agents" in agents_data
            assert agents_data["agent_count"] >= 7


            # 3. Broadcast overlay endpoint
            res_overlay = await client.get("/overlay?match_id=test_match")
            assert res_overlay.status_code == 200
            assert "MatchMind Broadcast Overlay" in res_overlay.text

            # 4. Trigger simulation and verify match state replication
            res_sim = await client.post("/api/match/sim_test/simulate?source=synthetic&events_count=5&delay_seconds=0.05")
            assert res_sim.status_code == 200
            await asyncio.sleep(0.6)
            # 5. Player RAG lookup endpoint
            res_player = await client.get("/api/rag/player/Bukayo%20Saka")
            assert res_player.status_code == 200
            player_data = res_player.json()
            assert player_data["player_name"] == "Bukayo Saka"
            assert "profile" in player_data
            assert player_data["profile"]["team"] == "Arsenal"

            # 6. Rivalry RAG lookup endpoint
            res_rivalry = await client.get("/api/rag/rivalry/Arsenal/Liverpool")
            assert res_rivalry.status_code == 200
            rivalry_data = res_rivalry.json()
            assert "rivalry" in rivalry_data

            # 7. Speech synthesis endpoint
            res_speech = await client.post(
                "/api/speech/synthesize",
                json={
                    "text": "What a stunning goal by Bukayo Saka!",
                    "persona": "casual_fan",
                    "lang": "en",
                    "leverage_index": 4.5,
                    "outcome": "Goal",
                },
            )
            assert res_speech.status_code == 200
            speech_data = res_speech.json()
            assert "audio_id" in speech_data
            assert "audio_url" in speech_data
            assert "ssml" in speech_data
            assert speech_data["voice_name"] == "en-GB-AlfieNeural"

            # 8. Audio stream playback endpoint
            audio_id = speech_data["audio_id"]
            res_audio = await client.get(f"/api/speech/audio/{audio_id}")
            assert res_audio.status_code == 200
            assert "audio" in res_audio.headers.get("content-type", "")
            assert len(res_audio.content) > 0




