import React, { useEffect, useState, useRef, useMemo } from "react";
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
import { apiUrl, wsUrl } from "./api";
import { Radio, History, PlayCircle } from "lucide-react";
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

  // Operating Mode: Explicitly separates Replay/Scrubber state from Live Simulation
  const [operatingMode, setOperatingMode] = useState<"replay" | "simulation">("replay");

  const [activePersona, setActivePersona] = useState<PersonaType>("casual_fan");
  const [activeLanguage, setActiveLanguage] = useState<LanguageCode>("en");
  const [isSimulating, setIsSimulating] = useState(false);
  const [focusedPlayer, setFocusedPlayer] = useState<string | null>(null);

  // Live and Replay telemetry state
  const [currentEvent, setCurrentEvent] = useState<MatchEvent | null>(null);
  const [metrics, setMetrics] = useState<MetricState | null>(null);
  const [latestNarrative, setLatestNarrative] = useState<NarrativeOutput | null>(null);
  const [feedMessages, setFeedMessages] = useState<VerifiedMessagePayload[]>([]);
  const [agentList, setAgentList] = useState<AgentHealth[]>([]);

  const wsRef = useRef<WebSocket | null>(null);

  // Derive unified metrics according to explicit operating mode
  const effectiveMetrics = useMemo<MetricState | null>(() => {
    if (operatingMode === "replay" && timeline) {
      const curScore = timeline.current_score || { home: 0, away: 0 };
      const curMin = timeline.current_minute || 0;
      return {
        ...(metrics || {
          match_id: matchId,
          home_team: timeline.home_team || "Arsenal",
          away_team: timeline.away_team || "Liverpool",
          score: curScore,
          cumulative_xg: { home: 0.0, away: 0.0 },
          rolling_ppda: { home: 10.5, away: 10.5 },
          field_tilt: 50.0,
          possession_pct: { home: 50.0, away: 50.0 },
          momentum_direction: "balanced",
          momentum_shift_detected: false,
          current_leverage_index: 1.0,
        }),
        match_id: matchId,
        home_team: timeline.home_team,
        away_team: timeline.away_team,
        minute: curMin,
        score: curScore,
      };
    }
    return metrics;
  }, [operatingMode, timeline, metrics, matchId]);

  // 1. Fetch available match catalog and timeline on load
  const loadMatches = async () => {
    try {
      const res = await fetch(apiUrl("/api/matches"));
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
      const res = await fetch(apiUrl(`/api/match/${id}/timeline`));
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
      const res = await fetch(apiUrl("/api/agents/status"));
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

  // 3. Manage WebSocket connection for Live Simulation
  useEffect(() => {
    const socketUrl = wsUrl(`/ws/match/${matchId}?persona=${activePersona}&lang=${activeLanguage}`);
    const ws = new WebSocket(socketUrl);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const raw = JSON.parse(event.data);
        if (raw.message_type === "VERIFIED_OUTPUT") {
          const payload = raw.payload as VerifiedMessagePayload;
          // In simulation mode, live feeds take authority
          if (operatingMode === "simulation" || isSimulating) {
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
                    current_score: payload.metric_state.score,
                  }
                : null
            );
          }
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
  }, [matchId, activePersona, activeLanguage, operatingMode, isSimulating]);

  // 4. Match Switcher Handler
  const handleSelectMatch = async (newMatchId: string) => {
    setOperatingMode("replay");
    setMatchId(newMatchId);
    setFeedMessages([]);
    setCurrentEvent(null);
    setMetrics(null);
    setLatestNarrative(null);
    setFocusedPlayer(null);
    try {
      const res = await fetch(apiUrl(`/api/match/${newMatchId}/select`), {
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
    setOperatingMode("replay");
    try {
      const res = await fetch(apiUrl(`/api/match/${matchId}/playback`), {
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
      const res = await fetch(apiUrl(`/api/match/${matchId}/playback`), {
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
    setOperatingMode("replay");
    try {
      const res = await fetch(apiUrl(`/api/match/${matchId}/playback`), {
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
    setOperatingMode("replay");
    try {
      const res = await fetch(apiUrl(`/api/match/${matchId}/playback`), {
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
    setOperatingMode("replay");
    try {
      const res = await fetch(apiUrl(`/api/match/${matchId}/seek`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_minute: minute }),
      });
      if (res.ok) {
        const data = await res.json();
        setTimeline(data.timeline);
        if (data.event) setCurrentEvent(data.event);
        if (data.metric_state) setMetrics(data.metric_state);
        if (data.narrative) {
          setLatestNarrative(data.narrative);
          setFeedMessages((prev) => [
            ...prev,
            {
              narrative: data.narrative,
              event: data.event,
              metric_state: data.metric_state,
              is_verified: true,
            },
          ]);
        }
      }
    } catch (err) {
      console.error("Failed to seek to minute", err);
    }
  };

  const handleSeekMoment = async (momentId: string) => {
    setOperatingMode("replay");
    try {
      const res = await fetch(apiUrl(`/api/match/${matchId}/seek`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ moment_id: momentId }),
      });
      if (res.ok) {
        const data = await res.json();
        setTimeline(data.timeline);
        if (data.event) setCurrentEvent(data.event);
        if (data.metric_state) setMetrics(data.metric_state);
        if (data.narrative) {
          setLatestNarrative(data.narrative);
          setFeedMessages((prev) => [
            ...prev,
            {
              narrative: data.narrative,
              event: data.event,
              metric_state: data.metric_state,
              is_verified: true,
            },
          ]);
        }
      }
    } catch (err) {
      console.error("Failed to seek to key moment", err);
    }
  };

  // 6. Trigger background simulation
  const handleTriggerSimulation = async (source: "synthetic" | "statsbomb") => {
    setOperatingMode("simulation");
    setIsSimulating(true);
    setFeedMessages([]);
    try {
      await fetch(
        apiUrl(`/api/match/${matchId}/simulate?source=${source}&events_count=35&delay_seconds=0.7`),
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
          {/* Explicit Operating Mode Banner */}
          <div className="bg-slate-950/80 border border-slate-800 rounded-xl px-3.5 py-2 flex flex-wrap items-center justify-between gap-2.5 backdrop-blur-md shadow-md">
            <div className="flex items-center gap-2">
              {operatingMode === "replay" ? (
                <span className="flex items-center gap-1.5 text-xs font-bold text-amber-400 bg-amber-950/50 border border-amber-500/30 px-2 py-0.5 rounded-md">
                  <History className="w-3.5 h-3.5" />
                  <span>REPLAY MODE</span>
                </span>
              ) : (
                <span className="flex items-center gap-1.5 text-xs font-bold text-emerald-400 bg-emerald-950/50 border border-emerald-500/30 px-2 py-0.5 rounded-md">
                  <Radio className="w-3.5 h-3.5 animate-pulse text-emerald-400" />
                  <span>LIVE SIMULATION</span>
                </span>
              )}

              <span className="text-xs text-slate-300">
                {operatingMode === "replay" ? (
                  <>
                    Timeline Cursor: <b className="text-white font-mono">{timeline?.current_minute ?? 0}'</b> • Score at this minute:{" "}
                    <b className="text-emerald-400 font-mono">
                      {timeline?.current_score?.home ?? 0} - {timeline?.current_score?.away ?? 0}
                    </b>{" "}
                    <span className="text-slate-500">(Final: {timeline?.final_score.home}-{timeline?.final_score.away})</span>
                  </>
                ) : (
                  <>
                    Active Telemetry: <b className="text-white font-mono">{effectiveMetrics?.minute ?? 0}'</b> • Live Score:{" "}
                    <b className="text-emerald-400 font-mono">
                      {effectiveMetrics?.score.home ?? 0} - {effectiveMetrics?.score.away ?? 0}
                    </b>
                  </>
                )}
              </span>
            </div>

            <div className="flex items-center gap-1.5">
              {operatingMode === "replay" ? (
                <button
                  onClick={() => handleTriggerSimulation("synthetic")}
                  className="text-xs bg-emerald-500/10 hover:bg-emerald-500/25 text-emerald-300 border border-emerald-500/30 px-2.5 py-1 rounded-md font-semibold transition-all flex items-center gap-1"
                  title="Switch to background live event simulation stream"
                >
                  <PlayCircle className="w-3 h-3" />
                  <span>Start Live Simulation</span>
                </button>
              ) : (
                <button
                  onClick={() => setOperatingMode("replay")}
                  className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 px-2.5 py-1 rounded-md font-semibold transition-all flex items-center gap-1"
                  title="Switch to interactive timeline scrubber"
                >
                  <History className="w-3 h-3" />
                  <span>Switch to Replay Scrubber</span>
                </button>
              )}
            </div>
          </div>

          <PitchVisualization
            currentEvent={currentEvent}
            homeTeamName={timeline?.home_team ?? effectiveMetrics?.home_team ?? "Arsenal"}
            awayTeamName={timeline?.away_team ?? effectiveMetrics?.away_team ?? "Liverpool"}
            focusedPlayer={focusedPlayer}
            onSelectPlayer={setFocusedPlayer}
            matchId={matchId}
          />

          {/* Interactive Timeline Scrubber & Replay Controller */}
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
              homeTeamName={timeline?.home_team ?? effectiveMetrics?.home_team ?? "Arsenal"}
              awayTeamName={timeline?.away_team ?? effectiveMetrics?.away_team ?? "Liverpool"}
              activePersona={activePersona}
            />
          )}

          <MomentumGraph
            metrics={effectiveMetrics}
            homeTeamName={timeline?.home_team ?? effectiveMetrics?.home_team ?? "Arsenal"}
            awayTeamName={timeline?.away_team ?? effectiveMetrics?.away_team ?? "Liverpool"}
          />
          <MetricsPanel metrics={effectiveMetrics} />
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
