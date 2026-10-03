import React, { useEffect, useState, useRef } from "react";
import { Header } from "./components/Header";
import { PitchVisualization } from "./components/PitchVisualization";
import { MetricsPanel } from "./components/MetricsPanel";
import { ExplainabilityCard } from "./components/ExplainabilityCard";
import { LiveFeed } from "./components/LiveFeed";
import { AgentStatusBar } from "./components/AgentStatusBar";
import { MomentumGraph } from "./components/MomentumGraph";
import { PlayerFocusCard } from "./components/PlayerFocusCard";
import { AudioCommentaryBar } from "./components/AudioCommentaryBar";
import type {

  AgentHealth,
  LanguageCode,
  MatchEvent,
  MetricState,
  NarrativeOutput,
  PersonaType,
  VerifiedMessagePayload,
} from "./types";

export const App: React.FC = () => {
  const [matchId] = useState("match_demo_01");
  const [activePersona, setActivePersona] = useState<PersonaType>("casual_fan");
  const [activeLanguage, setActiveLanguage] = useState<LanguageCode>("en");
  const [isSimulating, setIsSimulating] = useState(false);
  const [focusedPlayer, setFocusedPlayer] = useState<string | null>(null);

  // Live telemetry state
  const [currentEvent, setCurrentEvent] = useState<MatchEvent | null>(null);
  const [metrics, setMetrics] = useState<MetricState | null>(null);
  const [latestNarrative, setLatestNarrative] = useState<NarrativeOutput | null>(null);
  const [feedMessages, setFeedMessages] = useState<VerifiedMessagePayload[]>([]);
  const [agentList, setAgentList] = useState<AgentHealth[]>([]);

  const wsRef = useRef<WebSocket | null>(null);

  // 1. Fetch initial agent cluster health
  const refreshAgentHealth = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/agents/status");
      if (res.ok) {
        const data = await res.json();
        setAgentList(data.agents || []);
      }
    } catch {
      // API might be starting up
    }
  };

  useEffect(() => {
    refreshAgentHealth();
    const interval = setInterval(refreshAgentHealth, 3000);
    return () => clearInterval(interval);
  }, []);

  // 2. Manage WebSocket connection
  useEffect(() => {
    const wsUrl = `ws://localhost:8000/ws/match/${matchId}?persona=${activePersona}&lang=${activeLanguage}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const raw = JSON.parse(event.data);
        if (raw.message_type === "VERIFIED_OUTPUT") {
          const payload = raw.payload as VerifiedMessagePayload;
          setCurrentEvent(payload.event);
          setMetrics(payload.metric_state);
          setLatestNarrative(payload.narrative);
          setFeedMessages((prev) => [...prev.slice(-49), payload]);
        }
      } catch (err) {
        console.error("Failed to parse message", err);
      }
    };

    ws.onerror = (err) => {
      console.warn("WebSocket status: Connecting or server offline", err);
    };

    return () => {
      ws.close();
    };
  }, [matchId, activePersona, activeLanguage]);

  // 3. Trigger background simulation
  const handleTriggerSimulation = async (source: "synthetic" | "statsbomb") => {
    setIsSimulating(true);
    setFeedMessages([]);
    try {
      await fetch(
        `http://localhost:8000/api/match/${matchId}/simulate?source=${source}&events_count=30&delay_seconds=0.7`,
        { method: "POST" }
      );
    } catch (err) {
      console.error("Simulation failed to start", err);
    } finally {
      setTimeout(() => setIsSimulating(false), 22000);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0f1d] text-slate-100 flex flex-col font-sans selection:bg-emerald-500 selection:text-slate-950">
      {/* Top Navigation */}
      <Header
        activePersona={activePersona}
        onSelectPersona={setActivePersona}
        activeLanguage={activeLanguage}
        onSelectLanguage={setActiveLanguage}
        onTriggerSimulation={handleTriggerSimulation}
        isSimulating={isSimulating}
        matchId={matchId}
      />

      {/* Main Grid View */}
      <main className="flex-1 p-4 max-w-[1600px] mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left Column (Pitch, Focus, Momentum & Metrics): 7 Cols on desktop */}
        <div className="lg:col-span-7 flex flex-col gap-4">
          <PitchVisualization
            currentEvent={currentEvent}
            homeTeamName={metrics?.home_team ?? "Arsenal"}
            awayTeamName={metrics?.away_team ?? "Liverpool"}
            focusedPlayer={focusedPlayer}
            onSelectPlayer={setFocusedPlayer}
          />
          {focusedPlayer && (
            <PlayerFocusCard
              focusedPlayerName={focusedPlayer}
              currentEvent={currentEvent}
              onClearFocus={() => setFocusedPlayer(null)}
              homeTeamName={metrics?.home_team ?? "Arsenal"}
              awayTeamName={metrics?.away_team ?? "Liverpool"}
              activePersona={activePersona}
            />
          )}
          <MomentumGraph
            metrics={metrics}
            homeTeamName={metrics?.home_team ?? "Arsenal"}
            awayTeamName={metrics?.away_team ?? "Liverpool"}
          />
          <MetricsPanel metrics={metrics} />
        </div>

        {/* Right Column (Audio, Explainability & Live Feed): 5 Cols on desktop */}
        <div className="lg:col-span-5 flex flex-col gap-4">
          <AudioCommentaryBar
            latestNarrative={latestNarrative}
            activePersona={activePersona}
          />
          <ExplainabilityCard narrative={latestNarrative} />
          <div className="flex-1 min-h-[360px]">
            <LiveFeed
              messages={feedMessages}
              activePersona={activePersona}
              activeLanguage={activeLanguage}
            />
          </div>
        </div>
      </main>


      {/* Persistent Multi-Agent Status Bar */}
      <AgentStatusBar agents={agentList} />
    </div>
  );
};

export default App;
