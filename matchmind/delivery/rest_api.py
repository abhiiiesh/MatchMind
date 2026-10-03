"""FastAPI REST & WebSocket Server for MatchMind Intelligence Platform."""

import asyncio
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
import structlog

from matchmind.speech.speech_service import speech_service

from data.synthetic.generator import SyntheticMatchGenerator
from data.synthetic.statsbomb_adapter import StatsBombStreamer
from matchmind.agents.factcheck_agent import FactCheckerAgent
from matchmind.agents.ingestion_agent import IngestionAgent
from matchmind.agents.metrics_agent import MetricsAgent
from matchmind.agents.context_agent import ContextAgent
from matchmind.agents.narrative_agent import NarrativeAgent

from matchmind.agents.orchestrator import AgentOrchestrator
from matchmind.agents.persona_agent import PersonaAgent
from matchmind.agents.translator_agent import TranslatorAgent
from matchmind.config import settings
from matchmind.delivery.overlay_formatter import BroadcastOverlayFormatter
from matchmind.delivery.websocket_server import manager
from matchmind.models import AgentMessage

logger = structlog.get_logger(__name__)

# Global Multi-Agent Orchestrator
orchestrator = AgentOrchestrator()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes and registers the full multi-agent cluster on startup."""
    logger.info("Initializing MatchMind Multi-Agent Cluster...")

    # Register all 7 specialized agents
    orchestrator.register_agent(IngestionAgent())
    orchestrator.register_agent(MetricsAgent())
    orchestrator.register_agent(ContextAgent())
    orchestrator.register_agent(NarrativeAgent())
    orchestrator.register_agent(PersonaAgent())
    orchestrator.register_agent(TranslatorAgent())
    orchestrator.register_agent(FactCheckerAgent())


    # Subscribe WebSocket broadcaster to verified outputs
    def on_verified_output(message: AgentMessage):
        if message.message_type == "VERIFIED_OUTPUT":
            return manager.broadcast_message(message)

    orchestrator.subscribe(on_verified_output)
    await orchestrator.start()
    logger.info("MatchMind Multi-Agent Cluster is online and ready")

    yield

    logger.info("Shutting down MatchMind Multi-Agent Cluster...")
    await orchestrator.stop()


app = FastAPI(
    title="MatchMind Football Intelligence API",
    description="Multi-Agent Explainable Football Intelligence Platform for Microsoft Premier League Hackathon",
    version="0.1.0",
    lifespan=lifespan,
)

# Enable CORS for frontend and external dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check and platform status."""
    return {
        "platform": "MatchMind Football Intelligence",
        "hackathon": "Microsoft Premier League - Inside the Game",
        "status": "online",
        "active_agents": len(orchestrator.agents),
        "docs_url": "/docs",
    }


@app.get("/api/agents/status")
async def get_agent_status():
    """Returns real-time health and latency telemetry for all micro-agents."""
    return {
        "cluster_status": "healthy" if orchestrator.is_running else "stopped",
        "agent_count": len(orchestrator.agents),
        "agents": [h.model_dump() for h in orchestrator.get_cluster_health()],
    }


@app.get("/api/match/{match_id}/state")
async def get_match_state(match_id: str):
    """Returns the current rolling tactical metrics for a match."""
    state = orchestrator.get_match_state(match_id)
    if not state:
        return JSONResponse(status_code=404, content={"error": f"No active state found for match {match_id}"})
    return state.model_dump()


@app.get("/api/rag/player/{player_name}")
async def get_player_profile(player_name: str):
    """Retrieves deep historical profile and career milestones for a player."""
    context_agent = orchestrator.agents.get("context_agent")
    if not context_agent or not hasattr(context_agent, "rag_engine"):
        return JSONResponse(status_code=503, content={"error": "ContextAgent not ready"})
    profile = context_agent.rag_engine.find_player(player_name)
    if not profile:
        return JSONResponse(status_code=404, content={"error": f"Player '{player_name}' not found in historical database"})
    return {"player_name": player_name, "profile": profile}


@app.get("/api/rag/rivalry/{home_team}/{away_team}")
async def get_rivalry_profile(home_team: str, away_team: str):
    """Retrieves head-to-head historical rivalry stats and narratives."""
    context_agent = orchestrator.agents.get("context_agent")
    if not context_agent or not hasattr(context_agent, "rag_engine"):
        return JSONResponse(status_code=503, content={"error": "ContextAgent not ready"})
    rivalry = context_agent.rag_engine.find_rivalry(home_team, away_team)
    if not rivalry:
        return JSONResponse(status_code=404, content={"error": f"No rivalry record found for {home_team} vs {away_team}"})
    return {"home_team": home_team, "away_team": away_team, "rivalry": rivalry}


class SynthesizeRequest(BaseModel):
    text: str = Field(..., description="Commentary text to synthesize")
    persona: str = Field("casual_fan", description="Audience persona")
    lang: str = Field("en", description="Language code (en, es, hi, ar, fr, pt)")
    leverage_index: float = Field(1.0, description="Match leverage index for emotional prosody")
    outcome: str = Field("Success", description="Action outcome (Goal, Shot, Pass, etc.)")
    speaking_rate: Optional[float] = Field(None, description="Optional speaking rate multiplier (0.8 - 1.5)")


@app.post("/api/speech/synthesize")
async def synthesize_speech(req: SynthesizeRequest):
    """Synthesizes commentary text into neural voice audio via Azure AI Speech with SSML inflection."""
    result = await speech_service.synthesize(
        text=req.text,
        persona=req.persona,
        lang=req.lang,
        leverage_index=req.leverage_index,
        outcome=req.outcome,
        speaking_rate=req.speaking_rate,
    )
    return result


@app.get("/api/speech/audio/{audio_id}")
async def get_audio_stream(audio_id: str):
    """Streams cached WAV or MP3 audio file."""
    audio_path = speech_service.get_audio_file(audio_id)
    if not audio_path or not audio_path.exists():
        return JSONResponse(status_code=404, content={"error": f"Audio file '{audio_id}' not found"})
    media_type = "audio/mpeg" if audio_path.suffix == ".mp3" else "audio/wav"
    return FileResponse(path=str(audio_path), media_type=media_type)


@app.post("/api/match/{match_id}/simulate")
async def start_simulation(
    match_id: str,
    source: str = Query("synthetic", enum=["synthetic", "statsbomb"]),
    events_count: int = Query(25, ge=5, le=100),
    delay_seconds: float = Query(0.5, ge=0.05, le=3.0),
):
    """Streams a sequence of match events through the multi-agent bus in the background."""

    async def run_sim():
        logger.info("Starting match simulation", match_id=match_id, source=source, count=events_count)
        if source == "statsbomb":
            try:
                streamer = StatsBombStreamer(match_id=match_id)
                events = streamer.get_events()[:events_count]
            except Exception:
                generator = SyntheticMatchGenerator(match_id=match_id)
                events = generator.generate_match(total_events=events_count)
        else:
            generator = SyntheticMatchGenerator(match_id=match_id)
            events = generator.generate_match(total_events=events_count)

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
            await asyncio.sleep(delay_seconds)
        logger.info("Completed simulation stream", match_id=match_id)

    asyncio.create_task(run_sim())
    return {
        "status": "simulation_started",
        "match_id": match_id,
        "source": source,
        "events_count": events_count,
        "delay_seconds": delay_seconds,
    }


@app.get("/overlay", response_class=HTMLResponse)
async def get_overlay(
    match_id: str = "demo_match",
    persona: str = "casual_fan",
    lang: str = "en",
):
    """Serves the transparent broadcast overlay page for OBS Studio Browser Source."""
    return HTMLResponse(content=BroadcastOverlayFormatter.render_overlay_html(match_id, persona, lang))


@app.websocket("/ws/match/{match_id}")
async def websocket_match_feed(
    websocket: WebSocket,
    match_id: str,
    persona: str = "casual_fan",
    lang: str = "en",
):
    """WebSocket stream dispatching verified match narratives to connected viewers."""
    await manager.connect(websocket, match_id=match_id, persona=persona, lang=lang)
    try:
        while True:
            # Keep connection alive & listen for client preferences or pings
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, match_id=match_id)
