# ⚽ MatchMind: Multi-Agent Explainable Football Intelligence Platform

> **Submitted to:** Microsoft Premier League Hackathon — *"Inside the Game"*  
> **Target Prize:** Grand Prize (1st Place) + Best Multi-Agent System Prize  
> **Built with:** Microsoft Azure OpenAI (GPT-4o / GPT-4o-mini), Azure AI Foundry, Azure Cosmos DB, Python 3.11, socceraction, kloppy, FastAPI, and React.

---

## 🌟 Executive Summary

Football stories do not start and end with the scoreline. **MatchMind** is an enterprise-grade multi-agent platform that transforms synthetic and real-time football match events into **explainable match intelligence, tactical narratives, and personalized experiences**.

While modern clubs invest millions in proprietary data systems, **1.87 billion Premier League fans** are left with raw box scores and unexplained statistics. MatchMind bridges this gap by answering not just **WHAT happened**, but **WHY it matters**—in real time, across multiple fan personas, and in multiple languages.

---

## 🏛️ System Architecture: The 7 Specialized Agents

MatchMind implements a decoupled multi-agent topology orchestrated via an asynchronous priority bus with shared state and failure recovery:

```
                            [ Match Event Stream ]
                          (StatsBomb / Synthetic)
                                     │
                                     ▼
                      ┌─────────────────────────────┐
                      │    1. Ingestion Agent       │
                      │  Schema & Coordinates (m/yd)│
                      └──────────────┬──────────────┘
                                     │
                                     ▼
                      ┌─────────────────────────────┐
                      │     2. Metrics Agent        │
                      │ xG, xT, PPDA, Field Tilt, LI│
                      └───────┬──────────────┬──────┘
                              │              │
                              ▼              ▼
     ┌─────────────────────────────┐   ┌─────────────────────────────┐
     │      3. Context Agent       │   │    4. Narrative Agent       │
     │ Vector RAG & Milestones     │──►│ Game Arc & Causality Logic  │
     └─────────────────────────────┘   └──────────────┬──────────────┘
                                                      │
                                                      ▼
                                       ┌─────────────────────────────┐
                                       │   5. Persona Agents         │
                                       │ Analyst / Casual / Hype     │
                                       └──────────────┬──────────────┘
                                                      │
                                                      ▼
                                       ┌─────────────────────────────┐
                                       │   6. Translator Agent       │
                                       │ Real-time Multilingual (5+) │
                                       └──────────────┬──────────────┘
                                                      │
                                                      ▼
                                       ┌─────────────────────────────┐
                                       │   7. Fact-Checker Agent     │
                                       │ Anti-Hallucination Guardrail│
                                       └──────────────┬──────────────┘
                                                      │
                                                      ▼
                                         [ Verified Delivery ]
                                     (WebSocket / REST / Broadcast)
```

---

## ⚡ 5-Stage Pipeline Mapping

| Stage | Pipeline Requirement | MatchMind Implementation |
|---|---|---|
| **1. Ingest** | Ingest match events in real-time | `IngestionAgent` + `StatsBombStreamer` with sub-millisecond parsing |
| **2. Interpret** | Aggregate into tactical statistics | `MetricsAgent`: Mathematical xG (geometric sigmoid), xT (16x12 grid), rolling PPDA, Field Tilt |
| **3. Explain** | Explain *why* a moment matters | `NarrativeAgent`: Tactical causation engine (e.g. why a defensive shape collapsed) |
| **4. Render** | Output on-screen alongside match | Broadcast overlay JSON, 2D D3.js pitch visualization, and WebSocket feed |
| **5. Personalize**| Cater to analysts, casual fans, and global languages | `PersonaAgent` (Tactical Analyst vs. Casual Fan) + `TranslatorAgent` (EN, ES, HI, AR, PT) |

---

## 🚀 Quick Start (Local Setup)

### 1. Prerequisites
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Git

### 2. Setup Virtual Environment & Install Dependencies
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/matchmind.git
cd matchmind

# Create virtual environment and install packages with uv
uv venv .venv
uv pip install -r requirements.txt --python .venv\Scripts\python.exe
```

### 3. Verify the Pipeline & Run Tests
Run the integration test suite covering all 7 micro-agents and API endpoints:
```bash
.venv\Scripts\pytest.exe tests\test_integration\test_full_pipeline.py -v
```

Or run the live 7-agent terminal simulation showing historical RAG enrichment in real-time:
```bash
.venv\Scripts\python.exe scripts\test_context_pipeline.py
```

### 4. Start the Backend API & WebSocket Server
```bash
.venv\Scripts\python.exe -m uvicorn matchmind.delivery.rest_api:app --reload --port 8000
```
- API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Agent Cluster Telemetry: [http://localhost:8000/api/agents/status](http://localhost:8000/api/agents/status)
- Transparent OBS Broadcast Overlay: [http://localhost:8000/overlay](http://localhost:8000/overlay)

### 5. Launch the React Live Dashboard
In a second terminal window:
```bash
cd frontend
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser. Click **"▶ Live Simulation"** to stream match events through the 7-agent cluster with real-time pitch animations and multilingual narratives.

---

## 📁 Repository Structure

```
├── .env.example              # Configuration variables template
├── pyproject.toml            # Project metadata and dependencies
├── requirements.txt          # Python requirements
├── data/
│   ├── cache/                # Local cache for match events
│   ├── historical/           # Player profiles, team records, rivalry database (RAG)
│   ├── schemas/              # JSON schemas for inter-agent messages
│   └── synthetic/            # Synthetic match event generators
├── docs/                     # Strategic research, MBA analysis, implementation plan
├── frontend/                 # React 18 + TypeScript + Tailwind live dashboard
│   ├── src/components/       # PitchVisualization, MetricsPanel, ExplainabilityCard, LiveFeed
├── matchmind/
│   ├── constants.py          # Coordinates, thresholds, taxonomies
│   ├── config.py             # Pydantic configuration
│   ├── models.py             # MatchEvent, MetricState, AgentMessage models
│   ├── agents/               # 7 Micro-Agents (Ingestion, Metrics, Context, Narrative, Persona, Translator, FactChecker)
│   ├── metrics/              # xG, xT, PPDA, Field Tilt analytics engines
│   ├── context/              # Historical RAG retrieval engine
│   ├── narrative/            # Story arc, local fallback, personas, prompt templates

│   ├── narrative/            # Story arc, causality explainer, persona templates
│   └── delivery/             # FastAPI REST server, WebSocket manager, OBS overlay
├── scripts/
│   ├── test_pipeline.py      # End-to-end multi-agent test script
│   ├── test_narrative_pipeline.py # Narrative & persona test script
│   └── download_statsbomb_sample.py # Open data sample downloader
└── tests/
    └── test_integration/     # Pytest end-to-end verification suite
```

---

## 📄 License
This project is licensed under the MIT License.
