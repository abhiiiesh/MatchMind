# 🤖 MatchMind Agent Specifications

**Document:** Formal Agent Contract & Operational Specifications  
**Version:** 1.0.0  

---

## Agent 1: IngestionAgent
- **Class:** `matchmind.agents.ingestion_agent.IngestionAgent`
- **Role:** Data Normalization & Spatial Ingestion Specialist
- **Subscribed Message Types:** `RAW_EVENT`
- **Emitted Message Types:** `NORMALIZED_EVENT`
- **Target:** `metrics_agent`
- **Core Operations:**
  1. Validates incoming payload against `MatchEvent` schema.
  2. Converts StatsBomb coordinate system ($120 \times 80$ yards) to standard FIFA pitch coordinates ($105 \times 68$ meters).
  3. Computes geometric flags: `is_attacking_third` ($x \ge 80.0$) and `is_box_entry` (crossing into $x \ge 102.0, 18.0 \le y \le 62.0$).

---

## Agent 2: MetricsAgent
- **Class:** `matchmind.agents.metrics_agent.MetricsAgent`
- **Role:** Advanced Football Metrics & Momentum Engine
- **Subscribed Message Types:** `NORMALIZED_EVENT`
- **Emitted Message Types:** `METRIC_UPDATE`
- **Target:** `context_agent`
- **Core Operations:**
  1. Computes Expected Goals ($xG$) for shots using geometric logistic regression.
  2. Computes Expected Threat ($\Delta xT$) for ball carries and progressive passes across a $16 \times 12$ pitch grid.
  3. Calculates rolling 5-minute PPDA (Passes Per Defensive Action) for pressing intensity.
  4. Maintains territorial Field Tilt percentage and continuous Momentum Curve $[-100, +100]$.
  5. Evaluates Leverage Index ($LI$) to gauge dramatic emotional volatility.

---

## Agent 3: ContextAgent
- **Class:** `matchmind.agents.context_agent.ContextAgent`
- **Role:** Historical Intelligence & RAG Retrieval Specialist
- **Subscribed Message Types:** `METRIC_UPDATE`
- **Emitted Message Types:** `CONTEXT_ENRICHED`
- **Target:** `narrative_agent`
- **Core Operations:**
  1. Intercepts event telemetry and identifies match participants (players, teams, venue).
  2. Executes vector/semantic search across Azure Cosmos DB or local knowledge bases (`player_profiles.json`, `team_records.json`, `rivalry_database.json`).
  3. Enriches event payload with milestone alerts (e.g. nearing 100th goal), historic comeback win rates, and rivalry dynamics.

---

## Agent 4: NarrativeAgent
- **Class:** `matchmind.agents.narrative_agent.NarrativeAgent`
- **Role:** Tactical Narrative & Causality Engine
- **Subscribed Message Types:** `CONTEXT_ENRICHED`, `METRIC_UPDATE`
- **Emitted Message Types:** `NARRATIVE_DRAFT`
- **Target:** `persona_agent`
- **Core Operations:**
  1. Classifies macro story arc (`Suffocation Phase`, `Desperate Climax`, `Total Territorial Control`, etc.).
  2. Formulates "Why It Matters" causality explanation explaining tactical drivers behind the moment.
  3. Integrates with Azure OpenAI GPT-4o (with zero-latency local heuristic engine fallback).

---

## Agent 5: PersonaAgent
- **Class:** `matchmind.agents.persona_agent.PersonaAgent`
- **Role:** Audience Personalization Specialist
- **Subscribed Message Types:** `NARRATIVE_DRAFT`
- **Emitted Message Types:** `PERSONA_COMMENTARY`
- **Target:** `translator_agent`
- **Core Operations:**
  1. Adapts the draft narrative into 4 distinct audience voices:
     - **Tactical Analyst**: High-IQ spatial breakdown with $xG$, $xT$, and PPDA metrics.
     - **Casual Fan**: Emotive, high-energy reactions with emojis and celebratory calls.
     - **Broadcast Commentator**: Traditional television play-by-play commentary.
     - **Accessibility Audio**: Spatial audio-descriptive commentary for visually impaired supporters.

---

## Agent 6: TranslatorAgent
- **Class:** `matchmind.agents.translator_agent.TranslatorAgent`
- **Role:** Real-Time Multilingual Localization Specialist
- **Subscribed Message Types:** `PERSONA_COMMENTARY`
- **Emitted Message Types:** `TRANSLATED_COMMENTARY`
- **Target:** `factcheck_agent`
- **Core Operations:**
  1. Translates primary commentary into 5 global target languages (Spanish, Hindi, Arabic, Portuguese, French).
  2. Integrates with Azure AI Translator with offline localized football dictionary fallback.
  3. Preserves domain terminology (e.g., $xG$, player names, tactical shapes).

---

## Agent 7: FactCheckerAgent
- **Class:** `matchmind.agents.factcheck_agent.FactCheckerAgent`
- **Role:** Compliance & Anti-Hallucination Guardrail
- **Subscribed Message Types:** `TRANSLATED_COMMENTARY`
- **Emitted Message Types:** `VERIFIED_OUTPUT`
- **Target:** External Subscribers (WebSockets, REST API, OBS Overlay)
- **Core Operations:**
  1. Cross-examines all generated commentary against ground-truth match telemetry.
  2. Verifies scorelines, preventing hallucinated score changes or false goal celebrations.
  3. Strips formations and match timestamps to eliminate false-positive flags.
  4. Certifies payload with `verified_by_factcheck = True`.
