# 🛠️ MatchMind — Implementation & Development Plan
## Microsoft × Premier League Hackathon: "Inside the Game"

> **Product:** MatchMind — Multi-Agent Explainable Football Intelligence Platform  
> **Target Prizes:** Best Multi-Agent System + Grand Prize (1st Place)  
> **Timeline:** Oct 2 (today) → Oct 27 (submission deadline)  
> **Team Size:** Up to 4 members

---

## 📅 Master Timeline Overview

```
Oct 2 ──────── Oct 5 ──── Oct 6 ────────────── Oct 13 ──────────── Oct 20 ──────────── Oct 27
  │  PHASE 0: PREP  │       │  PHASE 1: CORE     │  PHASE 2: INTEL    │  PHASE 3: POLISH   │
  │  (4 days)       │       │  (7 days)           │  (7 days)          │  (7 days)           │
  │                 │       │                     │                    │                     │
  │ • Env setup     │       │ • Agent framework   │ • Explainability   │ • Demo video        │
  │ • Azure infra   │       │ • Data pipeline     │ • Personalization  │ • Bug fixes         │
  │ • Data prep     │       │ • Metrics engine    │ • Multi-language   │ • Documentation     │
  │ • Repo scaffold │       │ • Basic narrative    │ • Web dashboard    │ • Submission        │
  │ • Register!     │ START │ • Agent coordination│ • Accessibility    │ • Pitch deck        │
  └─────────────────┘───────└─────────────────────┘────────────────────┘─────────────────────┘
```

---

## 🏗️ Part 1: System Architecture (What We're Building)

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                              MATCHMIND ARCHITECTURE                                     │
│                                                                                         │
│  ┌─────────────────┐    ┌──────────────────────────────────────────┐    ┌─────────────┐ │
│  │  DATA LAYER     │    │  MULTI-AGENT INTELLIGENCE CORE           │    │  DELIVERY   │ │
│  │                 │    │                                          │    │  LAYER      │ │
│  │ Synthetic Match │───►│  ┌──────────┐  ┌──────────┐             │    │             │ │
│  │ Event Simulator │    │  │ Ingestion │─►│ Metrics  │             │───►│ Web UI      │ │
│  │ (StatsBomb      │    │  │ Agent    │  │ Agent    │  ┌────────┐ │    │ (React +    │ │
│  │  Open Data)     │    │  └──────────┘  └────┬─────┘  │Context │ │    │  D3.js)     │ │
│  │                 │    │                     │        │Agent   │ │    │             │ │
│  │ Azure Event     │    │                     ▼        │(RAG)   │ │    │ WebSocket   │ │
│  │ Hubs / WebSocket│    │              ┌──────────┐    └───┬────┘ │    │ Live Feed   │ │
│  │                 │    │              │Narrative │◄───────┘      │    │             │ │
│  │ Azure Cosmos DB │    │              │ Agent    │               │    │ REST API    │ │
│  │ (State Store)   │    │              └────┬─────┘               │    │             │ │
│  │                 │    │         ┌─────────┼─────────┐           │    │ Audio       │ │
│  └─────────────────┘    │         ▼         ▼         ▼           │    │ (TTS)       │ │
│                         │  ┌──────────┐┌──────────┐┌──────────┐  │    │             │ │
│                         │  │ Analyst  ││ Casual   ││Translator│  │    └─────────────┘ │
│                         │  │ Persona  ││ Persona  ││ Agent    │  │                    │
│                         │  └────┬─────┘└────┬─────┘└────┬─────┘  │                    │
│                         │       └─────┬─────┘───────────┘        │                    │
│                         │             ▼                           │                    │
│                         │      ┌──────────┐                      │                    │
│                         │      │Fact-Check│                      │                    │
│                         │      │ Agent    │                      │                    │
│                         │      └──────────┘                      │                    │
│                         └──────────────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────────────────────────────────┘
```

### The 7 Agents & Their Roles

| # | Agent | Responsibility | Input | Output | Tech |
|---|---|---|---|---|---|
| 1 | **Ingestion Agent** | Normalize raw events into SPADL format, validate schema | Raw StatsBomb JSON | Normalized SPADL events | `kloppy`, `socceraction` |
| 2 | **Metrics Agent** | Compute xG, xT, PPDA, Field Tilt, momentum, pass quality | SPADL events stream | Computed metrics + rolling windows | `socceraction`, NumPy, custom models |
| 3 | **Context Agent** | RAG retrieval of historical context, rivalries, milestones | Current event + metrics | Enriched context (player streaks, records) | Azure Cosmos DB vector search |
| 4 | **Narrative Agent** | Detect dramatic arc, Leverage Index, game state classification | Metrics + Context | Story arc ("Dominant Siege", "Smash-and-Grab") | Azure OpenAI GPT-4o |
| 5 | **Persona Agents** (×2+) | Generate audience-specific commentary | Narrative arc + metrics | Analyst text / Casual fan text | GPT-4o-mini (fast) |
| 6 | **Translator Agent** | Multi-language output generation | English narrative | Narratives in Hindi, Spanish, Arabic, etc. | Azure OpenAI + Azure Translator |
| 7 | **Fact-Checker Agent** | Validate all claims against raw telemetry | Generated content + raw events | Verified content / flagged hallucinations | Rule-based + LLM judge |

### Agent Communication Protocol

```
┌──────────────────────────────────────────────────────────────────────┐
│                    AGENT MESSAGE BUS (Shared State)                   │
│                                                                      │
│  Message Format:                                                     │
│  {                                                                   │
│    "agent_id": "metrics_agent",                                      │
│    "timestamp": "2026-10-15T14:23:45.123Z",                         │
│    "match_id": "3857256",                                            │
│    "event_index": 1420,                                              │
│    "match_minute": 68,                                               │
│    "message_type": "METRIC_UPDATE",                                  │
│    "payload": {                                                      │
│      "cumulative_xg": {"home": 1.84, "away": 0.72},                 │
│      "rolling_ppda_5min": {"home": 7.2, "away": 14.8},              │
│      "field_tilt": 78.3,                                            │
│      "momentum_shift": true,                                        │
│      "momentum_direction": "home_dominant"                           │
│    },                                                                │
│    "requires_response_from": ["narrative_agent"]                     │
│  }                                                                   │
│                                                                      │
│  Coordination: Pub/Sub via in-memory message queue                   │
│  Failure Recovery: Dead-letter queue + retry with exponential backoff│
│  State Persistence: Azure Cosmos DB (match state document)           │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Part 2: Repository Structure

```
matchmind/
├── README.md                          # Project overview, setup, demo link
├── LICENSE                            # MIT License
├── .env.example                       # Environment variables template
├── pyproject.toml                     # Python project config (uv/pip)
├── requirements.txt                   # Python dependencies
├── Dockerfile                         # Container build
├── docker-compose.yml                 # Local multi-service orchestration
│
├── docs/
│   ├── ARCHITECTURE.md                # System architecture documentation
│   ├── AGENT_SPECS.md                 # Detailed agent specifications
│   ├── JUDGING_CRITERIA_MAPPING.md    # How we address each judging criterion
│   └── PITCH.md                       # Elevator pitch for submission
│
├── infrastructure/
│   ├── azure/
│   │   ├── deploy.sh                  # Azure resource deployment script
│   │   ├── bicep/                     # Azure Bicep IaC templates
│   │   │   ├── main.bicep             # Main infrastructure template
│   │   │   ├── eventhubs.bicep        # Event Hubs config
│   │   │   ├── cosmosdb.bicep         # Cosmos DB config
│   │   │   ├── openai.bicep           # Azure OpenAI config
│   │   │   └── containerapp.bicep     # Container Apps config
│   │   └── env/
│   │       ├── dev.parameters.json
│   │       └── prod.parameters.json
│   └── docker/
│       └── docker-compose.local.yml   # Local dev without Azure
│
├── data/
│   ├── synthetic/
│   │   ├── generator.py               # Synthetic match event generator
│   │   ├── statsbomb_adapter.py       # Load StatsBomb open data as synthetic stream
│   │   └── sample_match.json          # Sample match for testing
│   ├── historical/
│   │   ├── player_profiles.json       # Player metadata for context agent
│   │   ├── team_records.json          # Historical records & milestones
│   │   └── rivalry_database.json      # Head-to-head history
│   └── schemas/
│       ├── spadl_schema.json           # SPADL event schema
│       ├── agent_message_schema.json   # Inter-agent message format
│       └── output_schema.json         # Final output format
│
├── matchmind/                         # Core Python package
│   ├── __init__.py
│   ├── config.py                      # Configuration management
│   ├── constants.py                   # Football constants, pitch dimensions
│   │
│   ├── agents/                        # Multi-Agent Core
│   │   ├── __init__.py
│   │   ├── base_agent.py              # Abstract base agent class
│   │   ├── orchestrator.py            # Agent orchestration & message bus
│   │   ├── ingestion_agent.py         # Agent 1: Event normalization
│   │   ├── metrics_agent.py           # Agent 2: xG, xT, PPDA computation
│   │   ├── context_agent.py           # Agent 3: Historical RAG retrieval
│   │   ├── narrative_agent.py         # Agent 4: Story arc & dramatic tension
│   │   ├── persona_agent.py           # Agent 5: Audience-specific commentary
│   │   ├── translator_agent.py        # Agent 6: Multi-language generation
│   │   └── factcheck_agent.py         # Agent 7: Hallucination prevention
│   │
│   ├── metrics/                       # Football Analytics Engine
│   │   ├── __init__.py
│   │   ├── expected_goals.py          # xG model
│   │   ├── expected_threat.py         # xT grid computation
│   │   ├── pressing.py                # PPDA & pressing intensity
│   │   ├── field_tilt.py              # Territorial dominance
│   │   ├── pass_quality.py            # Pass difficulty rating
│   │   ├── momentum.py                # Match momentum & Leverage Index
│   │   └── player_ratings.py          # Live player performance ratings
│   │
│   ├── narrative/                     # Narrative Generation Engine
│   │   ├── __init__.py
│   │   ├── story_arc.py               # Game state classification
│   │   ├── leverage_index.py          # Emotional importance of moments
│   │   ├── explainer.py               # "WHY it matters" engine
│   │   ├── personas.py                # Persona definitions & prompt templates
│   │   └── templates/
│   │       ├── analyst_prompts.yaml   # Tactical analyst persona prompts
│   │       ├── casual_prompts.yaml    # Casual fan persona prompts
│   │       └── system_prompts.yaml    # System prompts for each agent
│   │
│   ├── delivery/                      # Output & Delivery Layer
│   │   ├── __init__.py
│   │   ├── websocket_server.py        # WebSocket server for real-time push
│   │   ├── rest_api.py                # REST API (FastAPI)
│   │   ├── overlay_formatter.py       # Broadcast overlay JSON formatter
│   │   └── audio_generator.py         # Azure Speech TTS integration
│   │
│   └── utils/
│       ├── __init__.py
│       ├── pitch.py                   # Pitch coordinate utilities
│       ├── azure_client.py            # Azure OpenAI & Cosmos DB client
│       └── logger.py                  # Structured logging
│
├── frontend/                          # Web Dashboard (React + D3.js)
│   ├── package.json
│   ├── src/
│   │   ├── App.tsx                    # Main application
│   │   ├── components/
│   │   │   ├── PitchVisualization.tsx # 2D football pitch with D3.js
│   │   │   ├── LiveFeed.tsx           # Real-time narrative feed
│   │   │   ├── MetricsPanel.tsx       # xG, xT, PPDA dashboard
│   │   │   ├── ExplainabilityCard.tsx # "Why This Matters" popups
│   │   │   ├── PersonaSelector.tsx    # Casual / Analyst / Language toggle
│   │   │   ├── MomentumGraph.tsx      # Match momentum visualization
│   │   │   ├── PlayerTracker.tsx      # Individual player focus mode
│   │   │   └── AgentStatusBar.tsx     # Shows which agents are processing
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts        # WebSocket connection hook
│   │   ├── utils/
│   │   │   └── pitchCoordinates.ts    # Coordinate system conversion
│   │   └── styles/
│   │       └── matchmind.css          # Custom styling
│   └── public/
│       └── index.html
│
├── tests/
│   ├── test_agents/
│   │   ├── test_ingestion_agent.py
│   │   ├── test_metrics_agent.py
│   │   ├── test_narrative_agent.py
│   │   └── test_factcheck_agent.py
│   ├── test_metrics/
│   │   ├── test_xg.py
│   │   ├── test_xt.py
│   │   └── test_ppda.py
│   ├── test_integration/
│   │   └── test_full_pipeline.py      # End-to-end agent pipeline test
│   └── fixtures/
│       └── sample_events.json         # Test data fixtures
│
└── scripts/
    ├── setup_azure.sh                 # One-click Azure setup
    ├── run_demo.py                    # Run full demo with sample match
    ├── simulate_live_match.py         # Stream events at real-time pace
    └── generate_synthetic_data.py     # Generate custom synthetic matches
```

---

## 🔧 Part 3: Technology Stack

### Backend (Python 3.11+)

| Component | Technology | Why This Choice |
|---|---|---|
| **Agent Framework** | `autogen` or custom (LangGraph-style) | Microsoft's own agent framework — direct alignment with judging criteria |
| **Football Data** | `statsbombpy`, `kloppy`, `socceraction` | Industry-standard open-source football analytics |
| **Metrics Engine** | `socceraction` + custom NumPy | SPADL conversion, xT/VAEP computation |
| **Visualization** | `mplsoccer` (backend charts) | Standard football pitch plots |
| **API Server** | `FastAPI` + `uvicorn` | Async, WebSocket support, fast |
| **WebSocket** | `websockets` / FastAPI WebSocket | Real-time push to frontend |
| **LLM Client** | `openai` (Azure OpenAI SDK) | Official SDK for Azure OpenAI |
| **Data Storage** | `azure-cosmos` | State store + vector search |
| **Containerization** | Docker + Docker Compose | Local dev + Azure Container Apps |
| **Package Manager** | `uv` | Fast Python dependency management |

### Frontend (React + TypeScript)

| Component | Technology | Why |
|---|---|---|
| **Framework** | React 18 + TypeScript | Industry standard, fast development |
| **Pitch Visualization** | D3.js + custom SVG | Full control over football pitch rendering |
| **Charts** | Recharts / D3.js | Momentum graphs, xG timelines |
| **Styling** | Tailwind CSS | Rapid UI development |
| **WebSocket** | Native WebSocket API | Real-time updates |
| **Build Tool** | Vite | Fast dev server and builds |

### Azure Services

| Service | Purpose | Tier |
|---|---|---|
| **Azure OpenAI Service** | GPT-4o (narratives), GPT-4o-mini (classification) | Standard S0 |
| **Azure AI Foundry** | Prompt management, model catalog, evaluations | Free tier |
| **Azure Cosmos DB** | Match state store + vector search for RAG | Serverless |
| **Azure Container Apps** | Host backend agents | Consumption plan |
| **Azure Static Web Apps** | Host React frontend | Free tier |
| **Azure AI Speech** | Text-to-speech for audio commentary | Standard S0 |
| **Azure AI Translator** | Multi-language text translation | Free tier (2M chars/mo) |

---

## 📋 Part 4: Day-by-Day Development Sprint Plan

### PHASE 0: PREPARATION (Oct 2–5, 4 days)

#### Day 1 — Oct 2 (Today): Strategy & Planning ✅ DONE
- [x] Fetch and analyze hackathon requirements
- [x] Deep market research (sports-tech landscape)
- [x] VC-grade strategic analysis
- [x] Category selection (Best Multi-Agent System + Grand Prize)
- [x] Product vision definition ("MatchMind")
- [ ] **TODO:** Create this implementation plan

#### Day 2 — Oct 3: Environment Setup & Data Preparation
**Morning (3-4 hours):**
- [ ] Create GitHub repository (`matchmind`)
- [ ] Initialize Python project with `uv` and `pyproject.toml`
- [ ] Install core dependencies:
  ```
  statsbombpy kloppy socceraction mplsoccer
  fastapi uvicorn websockets
  openai azure-cosmos azure-identity
  numpy pandas scikit-learn
  ```
- [ ] Set up `.env.example` with all config variables
- [ ] Create base project directory structure (as above)

**Afternoon (3-4 hours):**
- [ ] Download and explore StatsBomb open data
- [ ] Write `data/synthetic/statsbomb_adapter.py`:
  - Load a full match event stream from StatsBomb
  - Convert to streaming format (yield events one-by-one with timestamps)
  - Simulate real-time pacing (1 event per 1-3 seconds)
- [ ] Write `data/synthetic/generator.py`:
  - Generate custom synthetic events following StatsBomb schema
  - Configurable match scenarios (dominant team, comeback, tight draw)
- [ ] Validate event schemas against SPADL format using `kloppy`
- [ ] Create `data/schemas/` with JSON schemas for validation

**Evening (2 hours):**
- [ ] Write test fixtures (`tests/fixtures/sample_events.json`)
- [ ] Run basic smoke tests: load data → convert to SPADL → print stats
- [ ] Commit: "feat: project scaffold and data pipeline foundation"

#### Day 3 — Oct 4: Azure Infrastructure & Agent Base Classes
**Morning (3-4 hours):**
- [ ] Create Azure resource group: `rg-matchmind-hack`
- [ ] Deploy Azure OpenAI Service:
  - Deploy `gpt-4o` model (for deep narratives)
  - Deploy `gpt-4o-mini` model (for classification/fast tasks)
- [ ] Deploy Azure Cosmos DB (serverless, NoSQL API):
  - Create database: `matchmind`
  - Create containers: `match_state`, `historical_context`, `agent_logs`
  - Enable vector search on `historical_context` container
- [ ] Deploy Azure AI Speech (Standard S0)
- [ ] Test all Azure connections from Python

**Afternoon (4 hours):**
- [ ] Write `matchmind/agents/base_agent.py`:
  ```python
  class BaseAgent(ABC):
      """Abstract base for all MatchMind agents."""
      agent_id: str
      agent_role: str
      
      async def process(self, message: AgentMessage) -> AgentMessage
      async def handle_error(self, error: Exception) -> AgentMessage
      def get_status(self) -> AgentStatus
  ```
- [ ] Write `matchmind/agents/orchestrator.py`:
  - Message bus (async pub/sub using `asyncio.Queue`)
  - Agent registration and lifecycle management
  - Pipeline definition (which agent feeds which)
  - Error recovery: retry logic, dead-letter queue
  - Shared state management (match state document)
  - Logging: which agent is processing what, latency tracking
- [ ] Write `matchmind/config.py`: load from env vars
- [ ] Write `matchmind/utils/azure_client.py`: Azure OpenAI + Cosmos DB clients
- [ ] Commit: "feat: agent framework foundation and Azure infrastructure"

**Evening (2 hours):**
- [ ] Write unit tests for orchestrator message passing
- [ ] Test: 2 dummy agents passing messages through the bus
- [ ] Verify Azure OpenAI responds correctly with test prompts

#### Day 4 — Oct 5: Ingestion Agent + Metrics Engine Foundation
**Morning (4 hours):**
- [ ] Write `matchmind/agents/ingestion_agent.py`:
  - Accept raw StatsBomb JSON events
  - Validate against schema
  - Convert to SPADL using `kloppy` / `socceraction`
  - Emit normalized events to message bus
  - Handle malformed events gracefully (log + skip)
- [ ] Write `matchmind/metrics/expected_goals.py`:
  - Implement xG model using logistic regression
  - Features: shot distance, angle, body part, play pattern, under_pressure
  - Train on StatsBomb open data (pre-train, save model weights)
- [ ] Write `matchmind/metrics/pressing.py`:
  - PPDA computation with configurable pitch zone
  - Rolling 5-minute window calculation
- [ ] Write `matchmind/metrics/field_tilt.py`:
  - Final-third pass ratio computation

**Afternoon (3 hours):**
- [ ] Write `matchmind/agents/metrics_agent.py`:
  - Receives normalized SPADL events from Ingestion Agent
  - Maintains rolling match state (cumulative xG, possession %, etc.)
  - Computes metrics on each event arrival
  - Emits `METRIC_UPDATE` messages
- [ ] Integration test: StatsBomb data → Ingestion Agent → Metrics Agent
- [ ] Verify xG, PPDA, Field Tilt computations against known match data
- [ ] Commit: "feat: ingestion agent and metrics engine with xG, PPDA, field tilt"

**Evening (2 hours):**
- [ ] Register for the hackathon (if not already done)
- [ ] Review: all foundation components ready for Phase 1
- [ ] Create `scripts/run_demo.py`: basic CLI that streams a match through agents

---

### PHASE 1: CORE AGENTS (Oct 6–12, 7 days)

> [!IMPORTANT]
> **Submission period officially starts Oct 6.** From here, every commit counts.

#### Day 5 — Oct 6: Expected Threat (xT) + Momentum Engine
- [ ] Write `matchmind/metrics/expected_threat.py`:
  - 16×12 pitch grid
  - Transition matrix from StatsBomb data
  - Value iteration solver
  - ΔxT per action computation
- [ ] Write `matchmind/metrics/momentum.py`:
  - Match momentum curve (rolling xT accumulation)
  - Momentum shift detection (threshold-based)
  - Leverage Index computation (how important is this moment?)
- [ ] Write `matchmind/metrics/pass_quality.py`:
  - Pass distance, angle, completion probability
  - Pass difficulty rating (based on defensive pressure + distance)
- [ ] Integrate all metrics into `metrics_agent.py`
- [ ] Test full metrics pipeline with 3 different matches
- [ ] Commit: "feat: xT model, momentum engine, pass quality metrics"

#### Day 6 — Oct 7: Context Agent (RAG)
- [ ] Populate Cosmos DB `historical_context` container:
  - Player career stats and milestones
  - Team head-to-head records
  - Record/milestone triggers ("most goals in a season", "100th PL appearance")
  - Historical tactical patterns ("teams that trail at halftime equalize X% of the time")
- [ ] Write `matchmind/agents/context_agent.py`:
  - Receives events + metrics from bus
  - Queries Cosmos DB vector search for relevant historical context
  - Formats context as enrichment payload
  - Triggers on "significant events" (goals, red cards, momentum shifts)
- [ ] Test: verify correct context retrieval for known player milestones
- [ ] Commit: "feat: context agent with historical RAG and milestone detection"

#### Day 7 — Oct 8: Narrative Agent (The Brain)
- [ ] Write `matchmind/narrative/story_arc.py`:
  - Game state classifier: "Dominant Siege", "Counter-Attack Battle", "Frustrated Build-Up", "Smash-and-Grab", "Tense Stalemate"
  - State transitions based on metrics thresholds
- [ ] Write `matchmind/narrative/leverage_index.py`:
  - Emotional weight of each event
  - High leverage: late equalizer, penalty, red card
  - Low leverage: routine pass in 4-0 blowout
- [ ] Write `matchmind/narrative/explainer.py`:
  - The "WHY it matters" engine
  - Takes raw metric + context → generates explanation
  - Example: "xG was 0.72 BECAUSE the center-back was dragged out of position by Díaz's run, opening a shooting lane that occurs in only 12% of PL attacks"
- [ ] Write `matchmind/agents/narrative_agent.py`:
  - Receives metrics + context
  - Classifies current game state / story arc
  - Calculates leverage index
  - Calls Azure OpenAI GPT-4o with structured prompt
  - Outputs narrative with embedded explanations
- [ ] Write prompt templates in `matchmind/narrative/templates/system_prompts.yaml`
- [ ] Test: full pipeline StatsBomb → Ingestion → Metrics → Context → Narrative
- [ ] Commit: "feat: narrative agent with story arc, leverage index, explainability"

#### Day 8 — Oct 9: Persona Agents (Personalization)
- [ ] Write `matchmind/narrative/personas.py`:
  - Define persona profiles:
    ```python
    PERSONAS = {
        "tactical_analyst": {
            "name": "The Analyst",
            "tone": "precise, data-rich, tactical terminology",
            "depth": "deep",
            "uses_metrics": True,
            "example": "Liverpool's PPDA dropped from 7.2 to 14.8..."
        },
        "casual_fan": {
            "name": "The Fan",
            "tone": "excited, simple language, emoji, relatable",
            "depth": "surface",
            "uses_metrics": False,
            "example": "🔥 WHAT A GOAL! Salah just did it again!"
        },
        "broadcast_commentator": {
            "name": "The Commentator",
            "tone": "professional, measured, building tension",
            "depth": "medium",
            "uses_metrics": True,
            "example": "And Salah strikes with precision..."
        }
    }
    ```
- [ ] Write `matchmind/agents/persona_agent.py`:
  - Receives narrative arc from Narrative Agent
  - Generates persona-specific commentary using GPT-4o-mini (fast!)
  - Each persona is a separate agent instance with distinct system prompt
  - Supports "Player Focus Mode" (all commentary centered on one player)
- [ ] Write persona prompt templates (`analyst_prompts.yaml`, `casual_prompts.yaml`)
- [ ] Test: same event → 3 different outputs for 3 personas
- [ ] Commit: "feat: persona agents for analyst, casual fan, and commentator modes"

#### Day 9 — Oct 10: Translator Agent + Fact-Checker Agent
- [ ] Write `matchmind/agents/translator_agent.py`:
  - Receives English narratives from Persona Agents
  - Translates to configured target languages
  - Uses Azure AI Translator for text
  - Preserves football terminology (don't translate "xG", "PPDA", player names)
  - Initial languages: English, Hindi, Spanish, Arabic, Portuguese
- [ ] Write `matchmind/agents/factcheck_agent.py`:
  - **The Anti-Hallucination Guard**
  - Receives generated narratives + raw event data
  - Validates:
    - Score mentions match actual scoreline
    - Player names match event data
    - Card counts are accurate
    - Metric values match computed values (within tolerance)
  - Flags violations → requests regeneration from persona agent
  - Rule-based checks (fast) + LLM verification (for nuanced claims)
- [ ] Write unit tests for fact-checker with intentionally wrong narratives
- [ ] Test: full 7-agent pipeline end-to-end
- [ ] Commit: "feat: translator and fact-checker agents completing the pipeline"

#### Day 10 — Oct 11: WebSocket Server + REST API
- [ ] Write `matchmind/delivery/websocket_server.py`:
  - FastAPI WebSocket endpoint
  - Client subscription to match feeds
  - Client can specify: persona, language, player focus
  - Server pushes events as they flow through agent pipeline
- [ ] Write `matchmind/delivery/rest_api.py`:
  - `GET /api/match/{match_id}/state` — current match state
  - `GET /api/match/{match_id}/timeline` — all events with narratives
  - `GET /api/match/{match_id}/metrics` — current metrics snapshot
  - `POST /api/match/{match_id}/start` — start processing a match
  - `GET /api/agents/status` — status of all agents
- [ ] Write `matchmind/delivery/overlay_formatter.py`:
  - Format metrics + narratives as broadcast-ready JSON
  - Compatible with OBS Browser Source overlay format
- [ ] Test WebSocket with a simple HTML client
- [ ] Commit: "feat: WebSocket server, REST API, and broadcast overlay formatter"

#### Day 11 — Oct 12: Frontend Foundation (React)
- [ ] Initialize React project with Vite + TypeScript + Tailwind
- [ ] Write `frontend/src/components/PitchVisualization.tsx`:
  - D3.js SVG football pitch (120×80 coordinate system)
  - Player dots with name labels
  - Ball position indicator
  - Event markers (shots, passes, tackles)
  - Color-coded by team
- [ ] Write `frontend/src/hooks/useWebSocket.ts`:
  - Connect to backend WebSocket
  - Parse incoming messages
  - Update React state
- [ ] Write `frontend/src/components/LiveFeed.tsx`:
  - Scrolling narrative feed (latest events at top)
  - Color-coded by event importance (goal = red, momentum shift = orange)
- [ ] Write `frontend/src/App.tsx`:
  - Layout: Pitch (left) + Narrative Feed (right) + Metrics (bottom)
- [ ] Test: frontend connected to backend, showing live events
- [ ] Commit: "feat: React frontend with live pitch visualization and narrative feed"

---

### PHASE 2: INTELLIGENCE & POLISH (Oct 13–19, 7 days)

#### Day 12 — Oct 13: Metrics Dashboard & Explainability UI
- [ ] Write `frontend/src/components/MetricsPanel.tsx`:
  - Live xG progression chart (Recharts line chart)
  - PPDA gauge (pressing intensity indicator)
  - Field Tilt bar chart
  - Possession pie chart
  - Pass accuracy comparison
- [ ] Write `frontend/src/components/ExplainabilityCard.tsx`:
  - "Why This Moment Matters" popup cards
  - Shows explainability text from the Narrative Agent
  - Includes supporting metrics (mini charts)
  - Appears on significant events (goals, momentum shifts, key passes)
- [ ] Write `frontend/src/components/MomentumGraph.tsx`:
  - Rolling momentum curve (D3.js area chart)
  - Highlights momentum shifts with markers
- [ ] Style everything with Tailwind (dark theme, broadcast-quality look)
- [ ] Commit: "feat: metrics dashboard with xG charts, explainability cards, momentum graph"

#### Day 13 — Oct 14: Persona Selector & Player Focus Mode
- [ ] Write `frontend/src/components/PersonaSelector.tsx`:
  - Toggle between: 🔬 Analyst | 🎉 Casual Fan | 🎙️ Commentator
  - Language selector dropdown (English, Hindi, Spanish, Arabic, Portuguese)
  - Changes narrative feed content in real-time via WebSocket message
- [ ] Write `frontend/src/components/PlayerTracker.tsx`:
  - Click on any player dot on pitch to enter "Player Focus Mode"
  - All narratives rewrite to center on that player
  - Shows player-specific heatmap, pass map, involvement stats
- [ ] Write `frontend/src/components/AgentStatusBar.tsx`:
  - Bottom bar showing all 7 agents
  - Green/yellow/red status indicators
  - Shows what each agent is currently processing
  - Demonstrates the multi-agent coordination to judges
- [ ] Commit: "feat: persona selector, player focus mode, agent status visualization"

#### Day 14 — Oct 15: Audio Commentary (Azure Speech)
- [ ] Write `matchmind/delivery/audio_generator.py`:
  - Azure AI Speech integration
  - Neural TTS with SSML for emotional styles:
    - `style="excited"` for goals
    - `style="serious"` for tactical analysis
    - `style="calm"` for routine updates
  - Generate audio for narrative text in real-time
  - Serve audio stream via API endpoint
- [ ] Add audio player to frontend:
  - Play/pause button for AI commentary
  - Volume control
  - Persona voice selection
- [ ] **Accessibility mode**: 
  - Enhanced audio-descriptive commentary for visually impaired fans
  - Describes spatial context: "ball on the left wing, 25 meters from goal"
  - Describes player positioning and defensive gaps
- [ ] Commit: "feat: AI audio commentary with emotional TTS and accessibility mode"

#### Day 15 — Oct 16: Broadcast Overlay Mode
- [ ] Write broadcast overlay HTML page:
  - Transparent background (for OBS/CasparCG overlay)
  - Lower-third: match score + current narrative
  - Side panel: live xG, PPDA, Field Tilt
  - "Why This Matters" popup (appears for 8 seconds on key events)
  - Pure HTML5/CSS3 animations, no framework needed
- [ ] Add OBS-compatible endpoint: `GET /overlay?match_id=X&persona=analyst`
- [ ] Test with OBS Studio Browser Source
- [ ] Commit: "feat: broadcast overlay mode compatible with OBS and streaming platforms"

#### Day 16 — Oct 17: End-to-End Testing & Bug Fixes
- [ ] Run full end-to-end test: 
  - Stream an entire StatsBomb match (90 minutes compressed to 5 minutes)
  - Verify all 7 agents process correctly
  - Check narrative quality across all 3 personas
  - Verify translations in all 5 languages
  - Test fact-checker catches injected errors
- [ ] Fix all bugs found during E2E testing
- [ ] Performance optimization:
  - Ensure total pipeline latency < 2 seconds per event
  - Optimize Azure OpenAI calls (batch where possible)
  - Add caching for repeated context queries
- [ ] Commit: "fix: end-to-end testing and performance optimization"

#### Day 17 — Oct 18: Error Handling, Logging & Agent Resilience
- [ ] Add structured logging throughout all agents
- [ ] Implement graceful degradation:
  - If Azure OpenAI times out → fallback to template-based narrative
  - If Context Agent fails → Narrative Agent works without context
  - If Translator fails → serve English only
  - If Fact-Checker flags → regenerate max 2 times, then serve with disclaimer
- [ ] Add agent health monitoring dashboard data
- [ ] Add match state recovery (resume from Cosmos DB if backend restarts)
- [ ] Commit: "feat: agent resilience, graceful degradation, and structured logging"

#### Day 18 — Oct 19: Docker & Deployment
- [ ] Write `Dockerfile` for backend (multi-stage build, slim image)
- [ ] Write `docker-compose.yml` for local development:
  - Backend service (FastAPI + agents)
  - Frontend service (React dev server)
  - (Optional) Local Cosmos DB emulator
- [ ] Test: `docker compose up` → everything works
- [ ] Deploy to Azure Container Apps (if demo requires cloud hosting)
- [ ] Deploy frontend to Azure Static Web Apps
- [ ] Commit: "feat: Docker containerization and Azure deployment"

---

### PHASE 3: DEMO & SUBMISSION (Oct 20–27, 7 days)

#### Day 19 — Oct 20: Documentation
- [ ] Write comprehensive `README.md`:
  - Project overview & demo link
  - Architecture diagram
  - Setup instructions (< 5 minutes to run locally)
  - Tech stack summary
  - How it maps to the 5-stage pipeline (Ingest → Interpret → Explain → Render → Personalize)
  - Screenshots
- [ ] Write `docs/ARCHITECTURE.md`: detailed system design
- [ ] Write `docs/AGENT_SPECS.md`: each agent's purpose, I/O, and decision logic
- [ ] Write `docs/JUDGING_CRITERIA_MAPPING.md`:
  - Explicitly map every judging criterion to our implementation
  - For "Best Multi-Agent System": show distinct roles, shared state, handoffs, failure recovery
  - For "Grand Prize": show real-world impact, Microsoft platform innovation

#### Day 20 — Oct 21: Demo Script & Rehearsal
- [ ] Write demo script (exactly what to show in 2 minutes):
  ```
  0:00-0:15  — "MatchMind: making every fan a tactical genius"
  0:15-0:30  — Show match starting, events streaming in, agents activating
  0:30-0:50  — Show a goal with xG explainability: "WHY this goal was remarkable"
  0:50-1:10  — Toggle between Analyst and Casual Fan personas (same event, different narrative)
  1:10-1:25  — Switch language to Hindi/Spanish — show multi-language narratives
  1:25-1:40  — Show agent status bar — all 7 agents working in coordination
  1:40-1:55  — Show broadcast overlay mode — ready for real production
  1:55-2:00  — Close with impact: "1.87B fans. 190 countries. One intelligence layer."
  ```
- [ ] Create `scripts/simulate_live_match.py`:
  - Pre-selected match with dramatic moments
  - Events streamed at configurable speed (real-time or accelerated)
  - Pre-seeded with milestone triggers for context agent

#### Day 21-22 — Oct 22-23: Demo Video Production
- [ ] Record screen capture of the full demo flow
- [ ] Tools: OBS Studio for screen recording, DaVinci Resolve / CapCut for editing
- [ ] Structure:
  - Hook (3 sec): Problem statement
  - Demo (90 sec): Live system walkthrough
  - Tech (15 sec): Architecture diagram flash
  - Impact (12 sec): "3.5B fans deserve better"
- [ ] Add captions/subtitles
- [ ] Upload to YouTube (unlisted or public)
- [ ] Test video link accessibility

#### Day 23-24 — Oct 24-25: Final Polish & Edge Cases
- [ ] Run with 5 different matches — verify consistency
- [ ] Test with adversarial scenarios:
  - Match with 0 goals (can the system still tell a story?)
  - Match with 5+ goals (can it keep up?)
  - Red card scenario
  - Penalty shootout (if applicable)
- [ ] UI polish: animations, transitions, responsive design
- [ ] Performance: verify < 2 sec latency for full pipeline
- [ ] Security: ensure no API keys in code, all via env vars

#### Day 25 — Oct 26: Submission Preparation
- [ ] Write elevator pitch (200-300 words):
  - What you built
  - Which Microsoft and Azure technologies used
  - What problem it solves
  - Why it matters
- [ ] Prepare project page on hackathon website:
  - Title: "MatchMind: Multi-Agent Explainable Football Intelligence"
  - Description
  - Demo video URL
  - GitHub repository URL
  - Technologies used (tag all Azure services)
  - Category: Best Multi-Agent System
- [ ] Final code review — clean up any debug code, comments, TODOs
- [ ] Verify README has clear setup instructions

#### Day 26 — Oct 27: SUBMISSION DAY
- [ ] Final testing: one complete demo run
- [ ] Submit on hackathon website before 11:59 PM PT
- [ ] Double-check all required fields
- [ ] Verify demo video is accessible (public/unlisted YouTube)
- [ ] 🎉 Celebrate!

---

## 🎯 Part 5: Judging Criteria Mapping

### How MatchMind Addresses Every Criterion

#### For "Best Multi-Agent System" Prize:

| Criterion | How We Address It |
|---|---|
| **Specialized agents with distinct roles** | 7 agents, each with a single responsibility (Ingestion, Metrics, Context, Narrative, Persona, Translator, Fact-Checker) |
| **Coordinate through shared state** | Shared match state document in Cosmos DB + async message bus |
| **Effective handoffs** | Pipeline topology: Ingestion → Metrics → Context → Narrative → Persona → Translator → Fact-Check. Each handoff is a structured message |
| **Recover from failures** | Dead-letter queue, retry with backoff, graceful degradation (if Translator fails → serve English) |
| **End-to-end outcome a single agent could not achieve** | A single LLM cannot simultaneously: normalize data, compute xT, retrieve historical context, detect story arcs, generate 3 persona voices, translate to 5 languages, AND fact-check. The pipeline decomposition is essential |

#### For "Grand Prize" (Best Overall):

| Criterion | How We Address It |
|---|---|
| **5-stage pipeline (Ingest → Interpret → Explain → Render → Personalize)** | Directly implemented: Ingestion Agent → Metrics Agent → Narrative Agent (explain) → Web UI (render) → Persona Agent (personalize) |
| **Real-time match intelligence** | Sub-2-second latency from event to rendered output |
| **Narrative generation** | GPT-4o powered narratives with story arc detection and Leverage Index |
| **Explainability** | "Why This Matters" engine explains the tactical reasoning behind every metric |
| **Multi-language** | 5 languages (English, Hindi, Spanish, Arabic, Portuguese) |
| **Personalization** | 3 personas + player focus mode + language selection |
| **Innovative use of Microsoft platform** | Azure OpenAI, AI Foundry, Cosmos DB, Container Apps, AI Speech, AI Translator |

---

## 📦 Part 6: Dependencies & Setup Commands

### Quick Start (Local Development)

```bash
# 1. Clone repository
git clone https://github.com/YOUR_USERNAME/matchmind.git
cd matchmind

# 2. Install Python dependencies
pip install uv
uv sync

# 3. Set up environment variables
cp .env.example .env
# Edit .env with your Azure credentials:
#   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
#   AZURE_OPENAI_API_KEY=your-key
#   AZURE_OPENAI_GPT4O_DEPLOYMENT=gpt-4o
#   AZURE_OPENAI_GPT4O_MINI_DEPLOYMENT=gpt-4o-mini
#   AZURE_COSMOS_ENDPOINT=https://your-cosmos.documents.azure.com:443/
#   AZURE_COSMOS_KEY=your-key
#   AZURE_SPEECH_KEY=your-key
#   AZURE_SPEECH_REGION=eastus

# 4. Download StatsBomb open data
python scripts/generate_synthetic_data.py

# 5. Start backend
uvicorn matchmind.delivery.rest_api:app --reload --port 8000

# 6. Start frontend (separate terminal)
cd frontend
npm install
npm run dev

# 7. Open browser → http://localhost:5173
# 8. Start a demo match → POST http://localhost:8000/api/match/demo/start
```

### Key Python Dependencies

```toml
[project]
name = "matchmind"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    # Football Analytics
    "statsbombpy>=1.12.0",
    "kloppy>=3.15.0",
    "socceraction>=1.5.0",
    "mplsoccer>=1.3.0",
    
    # API & WebSocket
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "websockets>=12.0",
    
    # Azure AI
    "openai>=1.40.0",
    "azure-cosmos>=4.7.0",
    "azure-identity>=1.17.0",
    "azure-cognitiveservices-speech>=1.40.0",
    
    # Data & ML
    "numpy>=1.26.0",
    "pandas>=2.2.0",
    "scikit-learn>=1.5.0",
    
    # Utilities
    "pydantic>=2.9.0",
    "python-dotenv>=1.0.0",
    "structlog>=24.4.0",
]
```

---

## 🎬 Part 7: Demo Video Storyboard (≤ 2 Minutes)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ MATCHMIND DEMO VIDEO STORYBOARD (2:00)                                 │
├──────────┬──────────────────────────────────────────────────────────────┤
│ 0:00     │ 🎬 HOOK: Dark screen → "3.5 billion football fans."        │
│          │ "But only 0.001% understand WHY things happen on the pitch."│
│          │ → "MatchMind changes that."                                 │
├──────────┼──────────────────────────────────────────────────────────────┤
│ 0:12     │ 📊 SHOW: Match starts. Events streaming into dashboard.    │
│          │ Agent Status Bar lights up: Ingestion ✅ → Metrics ✅       │
│          │ Pitch visualization populates with player positions.        │
├──────────┼──────────────────────────────────────────────────────────────┤
│ 0:25     │ ⚽ MOMENT: A goal is scored. xG explainability card pops up.│
│          │ "xG = 0.72 because the CB was 6.2m out of position after   │
│          │ Díaz's decoy run. This angle opens in only 12% of attacks." │
│          │ Agent pipeline visible: Metrics → Context → Narrative → ✅  │
├──────────┼──────────────────────────────────────────────────────────────┤
│ 0:48     │ 🔄 PERSONALIZE: Toggle "Casual Fan" mode.                  │
│          │ Same goal → "🔥 WHAT A STRIKE! Salah smashes it in!"       │
│          │ Toggle "Analyst" → Full tactical breakdown with xT map      │
├──────────┼──────────────────────────────────────────────────────────────┤
│ 1:05     │ 🌍 LANGUAGE: Switch to Hindi → narrative updates instantly  │
│          │ Switch to Spanish → updates again. Same intelligence,       │
│          │ culturally adapted. Show Translator Agent processing.       │
├──────────┼──────────────────────────────────────────────────────────────┤
│ 1:20     │ 📈 METRICS: Show momentum shift detection.                 │
│          │ "MOMENTUM SHIFT: PPDA dropped from 7.2 to 14.8.            │
│          │ This pressing collapse historically leads to an equalizer   │
│          │ within 12 minutes in 34% of similar PL sequences."         │
├──────────┼──────────────────────────────────────────────────────────────┤
│ 1:35     │ 🤖 MULTI-AGENT: Zoom into Agent Status Bar.                │
│          │ Show 7 agents with distinct roles, shared state, handoffs.  │
│          │ "Kill" one agent → system gracefully degrades, recovers.    │
├──────────┼──────────────────────────────────────────────────────────────┤
│ 1:48     │ 💡 CLOSE: "Built on Azure OpenAI, AI Foundry, Cosmos DB."  │
│          │ "1.87 billion fans. 190 countries. Every language."         │
│          │ "MatchMind: Making every fan a tactical genius."            │
│          │ → Logo + GitHub URL                                        │
└──────────┴──────────────────────────────────────────────────────────────┘
```

---

## 👥 Part 8: Team Role Allocation (4 Members)

| Role | Responsibilities | Key Deliverables | Phase Focus |
|---|---|---|---|
| **🏗️ Agent Architect** (Lead) | Multi-agent orchestration, message bus, orchestrator, error recovery, Azure infra | `orchestrator.py`, `base_agent.py`, Azure Bicep templates, Docker | Phase 0-1 heavy |
| **📊 Metrics Engineer** | xG/xT/PPDA models, data pipeline, ingestion agent, metrics agent, synthetic data | All `metrics/` modules, `ingestion_agent.py`, `metrics_agent.py` | Phase 0-1 heavy |
| **🧠 Narrative & AI Engineer** | Narrative agent, persona agents, translator, fact-checker, prompt engineering, Azure OpenAI | All agents in `agents/` (narrative, persona, translator, factcheck), prompt templates | Phase 1-2 heavy |
| **🎨 Frontend & Demo Lead** | React dashboard, D3.js visualizations, broadcast overlay, demo video, documentation | All `frontend/` code, overlay HTML, video production, README | Phase 2-3 heavy |

### Solo Developer Adjustment

If working solo, prioritize in this order:
1. **Must-Have:** Ingestion + Metrics + Narrative + Fact-Check agents (4 agents minimum)
2. **Should-Have:** Persona agents + basic web UI
3. **Nice-to-Have:** Translator agent, audio commentary, broadcast overlay, player focus mode

---

## ✅ Part 9: Submission Checklist

### Required by Hackathon Rules:

- [ ] **New project** (built after Sep 29, 2026)
- [ ] **Project pitch/description** (elevator pitch with Microsoft/Azure tech listed)
- [ ] **Demo video** (≤ 2 minutes, public YouTube/Vimeo URL)
- [ ] **Working project** (must install and run consistently)
- [ ] **GitHub repository** (public, with clear README)

### Our Additions for Maximum Impact:

- [ ] Architecture diagram in README
- [ ] Agent specification document
- [ ] Judging criteria mapping document
- [ ] One-command local setup (`docker compose up`)
- [ ] Live demo URL (Azure-hosted)
- [ ] Accessibility features highlighted
- [ ] Unit tests passing
- [ ] Performance benchmarks documented

---

## 🏁 Part 10: Success Metrics (How We Know We've Nailed It)

| Metric | Target | How to Measure |
|---|---|---|
| **Pipeline latency** | < 2 seconds (event → rendered output) | Structured logging timestamps |
| **Agents operational** | All 7 agents running simultaneously | Agent status dashboard |
| **Narrative quality** | Judges find explanations insightful, not generic | Manual review + blind test |
| **Fact-check accuracy** | 0 hallucinated scores, cards, or player names | Automated test suite |
| **Multi-language** | 5 languages with correct football terminology | Manual review per language |
| **Persona differentiation** | 3 clearly distinct voices for same event | Side-by-side comparison |
| **Failure recovery** | System continues when 1 agent goes down | Kill-test during demo |
| **Demo video** | Compelling 2-minute story with clear value prop | Team review + external feedback |

---

*Implementation plan created October 2, 2026. Subject to daily adjustments based on progress.*
*Remember: This is Day 1 of a company, not a weekend project.* 🚀
