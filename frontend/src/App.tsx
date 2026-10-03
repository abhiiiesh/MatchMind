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
import { TimelineScrubber } from "./components/TimelineScrubber";
import type {
  AgentHealth,
  LanguageCode,
  MatchEvent,
  MatchSummary,
  MatchTimelineInfo,
  MetricState,
  NarrativeOutput,
  PersonaType,
  VerifiedMessagePayload,
} from "./types";

export const App: React.FC = () => {
  const [matchId, setMatchId] = useState("arsenal_liverpool_2024");
  const [matches, setMatches] = useState<MatchSummary[]>([]);
  const [timeline, setTimeline] = useState<MatchTimelineInfo | null>(null);

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

  // 1. Fetch available match catalog and timeline on load
  const loadMatches = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/matches");
      if (res.ok) {
        const data = await res.json();
        setMatches(data.matches || []);
      }
    } catch (err) {
      console.warn("Could not load match catalog", err);
    }
  };

  const loadTimeline = async (id: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/match/${id}/timeline`);
      if (res.ok) {
        const data = await res.json();
        setTimeline(data);
      }
    } catch (err) {
      console.warn("Could not load timeline", err);
    }
  };

  // 2. Fetch initial agent cluster health
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
    loadMatches();
    loadTimeline(matchId);
    refreshAgentHealth();
    const interval = setInterval(refreshAgentHealth, 3000);
    return () => clearInterval(interval);
  }, []);

  // 3. Manage WebSocket connection
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

          // Keep timeline minute aligned with incoming event
          setTimeline((prev) =>
            prev
              ? {
                  ...prev,
                  current_minute: payload.event.minute,
                  current_second: payload.event.second,
                  current_index: payload.event.index,
                }
              : null
          );
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

  // 4. Match Switcher Handler
  const handleSelectMatch = async (newMatchId: string) => {
    setMatchId(newMatchId);
    setFeedMessages([]);
    setCurrentEvent(null);
    setLatestNarrative(null);
    setFocusedPlayer(null);
    try {
      const res = await fetch(`http://localhost:8000/api/match/${newMatchId}/select`, {
        method: "POST",
      });
      if (res.ok) {
        const data = await res.json();
        setTimeline(data.timeline);
      }
    } catch (err) {
      console.error("Failed to switch match", err);
    }
  };

  // 5. Interactive Replay Controls
  const handlePlay = async (speed: number) => {
    try {
      const res = await fetch(`http://localhost:8000/api/match/${matchId}/playback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "play", speed }),
      });
      if (res.ok) {
        const updated = await res.json();
        setTimeline(updated);
      }
    } catch (err) {
      console.error("Failed to start replay playback", err);
    }
  };

  const handlePause = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/match/${matchId}/playback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "pause" }),
      });
      if (res.ok) {
        const updated = await res.json();
        setTimeline(updated);
      }
    } catch (err) {
      console.error("Failed to pause playback", err);
    }
  };

  const handleReset = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/match/${matchId}/playback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "reset" }),
      });
      if (res.ok) {
        const updated = await res.json();
        setTimeline(updated);
      }
    } catch (err) {
      console.error("Failed to reset timeline", err);
    }
  };

  const handleStep = async (forward: boolean) => {
    try {
      const res = await fetch(`http://localhost:8000/api/match/${matchId}/playback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: forward ? "step_forward" : "step_backward" }),
      });
      if (res.ok) {
        const updated = await res.json();
        setTimeline(updated);
      }
    } catch (err) {
      console.error("Failed to step event", err);
    }
  };

  const handleSeekMinute = async (minute: number) => {
    try {
      const res = await fetch(`http://localhost:8000/api/match/${matchId}/seek`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_minute: minute }),
      });
      if (res.ok) {
        const data = await res.json();
        setTimeline(data.timeline);
      }
    } catch (err) {
      console.error("Failed to seek to minute", err);
    }
  };

  const handleSeekMoment = async (momentId: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/match/${matchId}/seek`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ moment_id: momentId }),
      });
      if (res.ok) {
        const data = await res.json();
        setTimeline(data.timeline);
      }
    } catch (err) {
      console.error("Failed to seek to key moment", err);
    }
  };

  // 6. Trigger background simulation
  const handleTriggerSimulation = async (source: "synthetic" | "statsbomb") => {
    setIsSimulating(true);
    setFeedMessages([]);
    try {
      await fetch(
        `http://localhost:8000/api/match/${matchId}/simulate?source=${source}&events_count=35&delay_seconds=0.7`,
        { method: "POST" }
      );
    } catch (err) {
      console.error("Simulation failed to start", err);
    } finally {
      setTimeout(() => setIsSimulating(false), 26000);
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
        matches={matches}
        onSelectMatch={handleSelectMatch}
      />

      {/* Main Grid View */}
      <main className="flex-1 p-4 max-w-[1600px] mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Left Column (Pitch, Timeline Scrubber, Focus, Momentum & Metrics): 7 Cols on desktop */}
        <div className="lg:col-span-7 flex flex-col gap-4">
          <PitchVisualization
            currentEvent={currentEvent}
            homeTeamName={metrics?.home_team ?? timeline?.home_team ?? "Arsenal"}
            awayTeamName={metrics?.away_team ?? timeline?.away_team ?? "Liverpool"}
            focusedPlayer={focusedPlayer}
            onSelectPlayer={setFocusedPlayer}
            matchId={matchId}
          />

          {/* Phase B: Interactive Timeline Scrubber & Replay Controller */}
          <TimelineScrubber
            timeline={timeline}
            onPlay={handlePlay}
            onPause={handlePause}
            onReset={handleReset}
            onSeekMinute={handleSeekMinute}
            onSeekMoment={handleSeekMoment}
            onStep={handleStep}
          />

          {focusedPlayer && (
            <PlayerFocusCard
              focusedPlayerName={focusedPlayer}
              currentEvent={currentEvent}
              onClearFocus={() => setFocusedPlayer(null)}
              homeTeamName={metrics?.home_team ?? timeline?.home_team ?? "Arsenal"}
              awayTeamName={metrics?.away_team ?? timeline?.away_team ?? "Liverpool"}
              activePersona={activePersona}
            />
          )}

          <MomentumGraph
            metrics={metrics}
            homeTeamName={metrics?.home_team ?? timeline?.home_team ?? "Arsenal"}
            awayTeamName={metrics?.away_team ?? timeline?.away_team ?? "Liverpool"}
          />
          <MetricsPanel metrics={metrics} />
        </div>

        {/* Right Column (Audio, Explainability & Live Feed): 5 Cols on desktop */}
        <div className="lg:col-span-5 flex flex-col gap-4">
          <AudioCommentaryBar
            latestNarrative={latestNarrative}
            activePersona={activePersona}
            activeLanguage={activeLanguage}
          />
          <ExplainabilityCard
            narrative={latestNarrative}
            onSelectPlayer={setFocusedPlayer}
            currentEventPlayerName={currentEvent?.player?.name}
          />
          <div className="flex-1 min-h-[360px]">
            <LiveFeed
              messages={feedMessages}
              activePersona={activePersona}
              activeLanguage={activeLanguage}
              onSelectPlayer={setFocusedPlayer}
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
