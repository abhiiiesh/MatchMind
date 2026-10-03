import React, { useEffect, useState } from "react";
import type {
  HeatmapData,
  MatchEvent,
  PassNetworkData,
  PitchOverlayMode,
  PressureZoneData,
} from "../types";

interface PitchProps {
  currentEvent: MatchEvent | null;
  homeTeamName: string;
  awayTeamName: string;
  focusedPlayer: string | null;
  onSelectPlayer: (playerName: string | null) => void;
  matchId?: string;
}

export const PitchVisualization: React.FC<PitchProps> = ({
  currentEvent,
  homeTeamName,
  awayTeamName,
  focusedPlayer,
  onSelectPlayer,
  matchId = "arsenal_liverpool_2024",
}) => {
  const [overlayMode, setOverlayMode] = useState<PitchOverlayMode>("standard");
  const [selectedTeam, setSelectedTeam] = useState<string>(homeTeamName);

  // Spatial data state
  const [heatmapData, setHeatmapData] = useState<HeatmapData | null>(null);
  const [passNetworkData, setPassNetworkData] = useState<PassNetworkData | null>(null);
  const [pressureData, setPressureData] = useState<PressureZoneData | null>(null);
  const [isLoadingSpatial, setIsLoadingSpatial] = useState<boolean>(false);

  // Sync selectedTeam if homeTeamName updates
  useEffect(() => {
    setSelectedTeam(homeTeamName);
  }, [homeTeamName]);

  // Fetch spatial data when overlay mode or team changes
  useEffect(() => {
    if (overlayMode === "standard") return;

    const fetchSpatialData = async () => {
      setIsLoadingSpatial(true);
      try {
        if (overlayMode === "heatmap") {
          const playerParam = focusedPlayer ? `&player=${encodeURIComponent(focusedPlayer)}` : "";
          const res = await fetch(
            `http://localhost:8000/api/match/${matchId}/spatial/heatmap?team=${encodeURIComponent(
              selectedTeam
            )}${playerParam}`
          );
          if (res.ok) setHeatmapData(await res.json());
        } else if (overlayMode === "pass_network") {
          const res = await fetch(
            `http://localhost:8000/api/match/${matchId}/spatial/pass_network?team=${encodeURIComponent(
              selectedTeam
            )}`
          );
          if (res.ok) setPassNetworkData(await res.json());
        } else if (overlayMode === "pressing") {
          const res = await fetch(
            `http://localhost:8000/api/match/${matchId}/spatial/pressure_zones?team=${encodeURIComponent(
              selectedTeam
            )}`
          );
          if (res.ok) setPressureData(await res.json());
        }
      } catch (err) {
        console.warn("Failed fetching spatial intelligence", err);
      } finally {
        setIsLoadingSpatial(false);
      }
    };

    fetchSpatialData();
  }, [overlayMode, selectedTeam, matchId, focusedPlayer]);

  // StatsBomb coordinates: 0..120 X, 0..80 Y
  const startX = currentEvent?.start_x ?? 60;
  const startY = currentEvent?.start_y ?? 40;
  const endX = currentEvent?.end_x;
  const endY = currentEvent?.end_y;
  const isHome = currentEvent?.team?.name === homeTeamName;
  const actorColor = isHome ? "#00ff87" : "#e90052";

  return (
    <div className="relative w-full aspect-[120/80] bg-[#1a472a] rounded-xl overflow-hidden border border-emerald-900/60 shadow-2xl flex flex-col justify-between">
      {/* Top Controls Toolbar */}
      <div className="absolute top-2.5 left-3 right-3 z-30 flex flex-wrap items-center justify-between gap-2 pointer-events-auto">
        {/* Teams Match Badge */}
        <div className="flex items-center gap-2 bg-slate-900/85 backdrop-blur-md px-2.5 py-1 rounded-full border border-slate-700/60 text-xs font-semibold shadow-lg">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-emerald-400 font-bold">{homeTeamName}</span>
          <span className="text-slate-400 text-[10px]">vs</span>
          <span className="text-rose-400 font-bold">{awayTeamName}</span>
        </div>

        {/* Tactical Layer Switcher */}
        <div className="flex items-center bg-slate-950/90 border border-slate-800 rounded-lg p-0.5 shadow-xl backdrop-blur-md gap-0.5">
          <button
            onClick={() => setOverlayMode("standard")}
            className={`px-2 py-1 rounded text-[11px] font-bold transition-all ${
              overlayMode === "standard"
                ? "bg-emerald-500 text-slate-950 shadow-md"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            🏟️ Live
          </button>
          <button
            onClick={() => setOverlayMode("heatmap")}
            className={`px-2 py-1 rounded text-[11px] font-bold transition-all ${
              overlayMode === "heatmap"
                ? "bg-amber-500 text-slate-950 shadow-md"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            🔥 Heatmap
          </button>
          <button
            onClick={() => setOverlayMode("pass_network")}
            className={`px-2 py-1 rounded text-[11px] font-bold transition-all ${
              overlayMode === "pass_network"
                ? "bg-cyan-500 text-slate-950 shadow-md"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            🕸️ Pass Network
          </button>
          <button
            onClick={() => setOverlayMode("pressing")}
            className={`px-2 py-1 rounded text-[11px] font-bold transition-all ${
              overlayMode === "pressing"
                ? "bg-rose-500 text-white shadow-md"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            🛡️ Pressing
          </button>
          {isLoadingSpatial && (
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping mx-1" title="Loading spatial intelligence..." />
          )}
        </div>

        {/* Team Filter for Tactical Layers */}
        {overlayMode !== "standard" && (
          <div className="flex items-center bg-slate-950/90 border border-slate-800 rounded-lg p-0.5 gap-1">
            <button
              onClick={() => setSelectedTeam(homeTeamName)}
              className={`px-2 py-0.5 rounded text-[10px] font-bold transition-all ${
                selectedTeam === homeTeamName
                  ? "bg-emerald-500 text-slate-950"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              {homeTeamName}
            </button>
            <button
              onClick={() => setSelectedTeam(awayTeamName)}
              className={`px-2 py-0.5 rounded text-[10px] font-bold transition-all ${
                selectedTeam === awayTeamName
                  ? "bg-rose-500 text-white"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              {awayTeamName}
            </button>
          </div>
        )}
      </div>

      {/* SVG Pitch Canvas */}
      <svg
        viewBox="0 0 120 80"
        className="w-full h-full select-none"
        preserveAspectRatio="xMidYMid meet"
      >
        <defs>
          <linearGradient id="grassGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#143d22" />
            <stop offset="100%" stopColor="#0f2e1a" />
          </linearGradient>

          {/* Grass striping */}
          <pattern id="stripes" width="12" height="80" patternUnits="userSpaceOnUse">
            <rect width="6" height="80" fill="rgba(255,255,255,0.015)" />
            <rect x="6" width="6" height="80" fill="transparent" />
          </pattern>

          {/* Arrowhead marker for progressive passes */}
          <marker
            id="passArrow"
            viewBox="0 0 10 10"
            refX="6"
            refY="5"
            markerWidth="5"
            markerHeight="5"
            orient="auto-start-reverse"
          >
            <path d="M 0 1 L 10 5 L 0 9 z" fill="#00ff87" />
          </marker>
        </defs>

        {/* Pitch Turf Background */}
        <rect width="120" height="80" fill="url(#grassGrad)" />
        <rect width="120" height="80" fill="url(#stripes)" />

        {/* Pitch Demarcations */}
        <rect
          x="3"
          y="3"
          width="114"
          height="74"
          fill="none"
          stroke="rgba(255, 255, 255, 0.45)"
          strokeWidth="0.8"
        />
        <line
          x1="60"
          y1="3"
          x2="60"
          y2="77"
          stroke="rgba(255, 255, 255, 0.45)"
          strokeWidth="0.8"
        />
        <circle
          cx="60"
          cy="40"
          r="10"
          fill="none"
          stroke="rgba(255, 255, 255, 0.45)"
          strokeWidth="0.8"
        />
        <circle cx="60" cy="40" r="0.8" fill="rgba(255, 255, 255, 0.75)" />

        {/* Penalty & 6-Yard Boxes */}
        <rect x="3" y="18" width="18" height="44" fill="none" stroke="rgba(255, 255, 255, 0.45)" strokeWidth="0.8" />
        <rect x="3" y="30" width="6" height="20" fill="none" stroke="rgba(255, 255, 255, 0.45)" strokeWidth="0.8" />
        <circle cx="15" cy="40" r="0.8" fill="rgba(255, 255, 255, 0.75)" />
        <path d="M 21 34 A 10 10 0 0 1 21 46" fill="none" stroke="rgba(255, 255, 255, 0.45)" strokeWidth="0.8" />

        <rect x="99" y="18" width="18" height="44" fill="none" stroke="rgba(255, 255, 255, 0.45)" strokeWidth="0.8" />
        <rect x="111" y="30" width="6" height="20" fill="none" stroke="rgba(255, 255, 255, 0.45)" strokeWidth="0.8" />
        <circle cx="105" cy="40" r="0.8" fill="rgba(255, 255, 255, 0.75)" />
        <path d="M 99 34 A 10 10 0 0 0 99 46" fill="none" stroke="rgba(255, 255, 255, 0.45)" strokeWidth="0.8" />

        {/* Goal Frames */}
        <rect x="0.5" y="36" width="2.5" height="8" fill="none" stroke="rgba(255,255,255,0.7)" strokeWidth="0.6" />
        <rect x="117" y="36" width="2.5" height="8" fill="none" stroke="rgba(255,255,255,0.7)" strokeWidth="0.6" />

        {/* ------------------------------------------------------------- */}
        {/* PHASE C: HEATMAP OVERLAY LAYER                                */}
        {/* ------------------------------------------------------------- */}
        {overlayMode === "heatmap" && heatmapData && (
          <g className="heatmap-layer transition-opacity duration-300">
            {heatmapData.points.map((pt, idx) => {
              const radius = 3.5 + pt.intensity * 4.0;
              const fill =
                pt.intensity > 0.65
                  ? `rgba(239, 68, 68, ${0.45 + pt.intensity * 0.4})` // Red
                  : pt.intensity > 0.35
                  ? `rgba(245, 158, 11, ${0.35 + pt.intensity * 0.35})` // Amber
                  : `rgba(16, 185, 129, ${0.25 + pt.intensity * 0.3})`; // Emerald
              return (
                <circle
                  key={`hm-${idx}`}
                  cx={pt.x}
                  cy={pt.y}
                  r={radius}
                  fill={fill}
                  filter="blur(1.5px)"
                />
              );
            })}
          </g>
        )}

        {/* ------------------------------------------------------------- */}
        {/* PHASE C: PASS NETWORK OVERLAY LAYER                           */}
        {/* ------------------------------------------------------------- */}
        {overlayMode === "pass_network" && passNetworkData && (
          <g className="pass-network-layer">
            {/* Pass Links */}
            {passNetworkData.links.map((lnk, idx) => {
              const srcNode = passNetworkData.nodes.find((n) => n.name === lnk.source);
              const tgtNode = passNetworkData.nodes.find((n) => n.name === lnk.target);
              if (!srcNode || !tgtNode) return null;
              const width = Math.max(0.6, lnk.weight * 2.6);
              const opacity = 0.35 + lnk.weight * 0.55;
              return (
                <line
                  key={`lnk-${idx}`}
                  x1={srcNode.x}
                  y1={srcNode.y}
                  x2={tgtNode.x}
                  y2={tgtNode.y}
                  stroke="#38bdf8"
                  strokeWidth={width}
                  strokeOpacity={opacity}
                  strokeLinecap="round"
                />
              );
            })}

            {/* Player Centroid Nodes */}
            {passNetworkData.nodes.map((node) => {
              const isSelected = focusedPlayer === node.name;
              return (
                <g
                  key={node.id}
                  transform={`translate(${node.x}, ${node.y})`}
                  className="cursor-pointer"
                  onClick={() => onSelectPlayer(isSelected ? null : node.name)}
                >
                  <circle
                    r="4.2"
                    fill={isSelected ? "#f59e0b" : "#0f172a"}
                    stroke={isSelected ? "#ffffff" : "#38bdf8"}
                    strokeWidth="1.2"
                    className="transition-transform hover:scale-120"
                  />
                  <text
                    y="1.2"
                    textAnchor="middle"
                    fill="#ffffff"
                    fontSize="2.8"
                    fontWeight="800"
                    fontFamily="monospace"
                  >
                    {node.jersey_number || "?"}
                  </text>
                  {/* Name Label */}
                  <text
                    y="5.8"
                    textAnchor="middle"
                    fill="#e2e8f0"
                    fontSize="2.1"
                    fontWeight="700"
                  >
                    {node.name.split(" ").slice(-1)[0]}
                  </text>
                </g>
              );
            })}
          </g>
        )}

        {/* ------------------------------------------------------------- */}
        {/* PHASE C: DEFENSIVE PRESSING ZONES LAYER                       */}
        {/* ------------------------------------------------------------- */}
        {overlayMode === "pressing" && (
          <g className="pressing-layer">
            {/* Pitch Thirds Demarcation */}
            <line x1="40" y1="3" x2="40" y2="77" stroke="#94a3b8" strokeDasharray="2,2" strokeWidth="0.6" />
            <line x1="80" y1="3" x2="80" y2="77" stroke="#ef4444" strokeDasharray="2,2" strokeWidth="0.8" />

            {/* High Press Highlight Zone */}
            <rect
              x="80"
              y="3"
              width="37"
              height="74"
              fill="rgba(239, 68, 68, 0.08)"
              stroke="none"
            />

            {/* High Press Actions Pins */}
            {pressureData?.high_press_actions.map((act, i) => (
              <g key={`pres-${i}`} transform={`translate(${act.x}, ${act.y})`}>
                <circle r="1.8" fill="#ef4444" opacity="0.8" />
                <circle r="3.2" fill="none" stroke="#ef4444" strokeWidth="0.5" opacity="0.5" />
              </g>
            ))}

            {/* Third Labels */}
            <text x="20" y="8" fill="rgba(255,255,255,0.6)" fontSize="2.6" fontWeight="700" textAnchor="middle">
              Low Block (Defensive 1/3)
            </text>
            <text x="60" y="8" fill="rgba(255,255,255,0.6)" fontSize="2.6" fontWeight="700" textAnchor="middle">
              Mid Block (Middle 1/3)
            </text>
            <text x="100" y="8" fill="#ef4444" fontSize="2.8" fontWeight="800" textAnchor="middle">
              ⚡ High Press Zone ({pressureData?.high_press_pct ?? 37.3}%)
            </text>
          </g>
        )}

        {/* ------------------------------------------------------------- */}
        {/* LIVE MATCH ACTION LAYER (STANDARD MODE)                       */}
        {/* ------------------------------------------------------------- */}
        {overlayMode === "standard" && (
          <>
            {/* Action Vector (Pass or Shot Trajectory) */}
            {endX !== undefined && endY !== undefined && (
              <g>
                <line
                  x1={startX}
                  y1={startY}
                  x2={endX}
                  y2={endY}
                  stroke={currentEvent?.event_type === "Shot" ? "#ffeb3b" : actorColor}
                  strokeWidth="1.6"
                  strokeDasharray={currentEvent?.event_type === "Shot" ? "2,1" : "none"}
                  markerEnd="url(#passArrow)"
                  className="transition-all duration-300"
                />
                <circle
                  cx={endX}
                  cy={endY}
                  r="1.8"
                  fill={currentEvent?.event_type === "Shot" ? "#ffeb3b" : actorColor}
                  opacity="0.8"
                />
              </g>
            )}

            {/* Ball Location Pulse & Expanded Click Hit Area */}
            <g
              data-testid="player-ball-node"
              className="cursor-pointer group"
              onClick={() => onSelectPlayer(currentEvent?.player?.name ?? null)}
            >
              <circle cx={startX} cy={startY} r="8" fill="transparent" pointerEvents="all" />

              {/* Pressure Ring */}
              {currentEvent?.under_pressure && (
                <circle
                  cx={startX}
                  cy={startY}
                  r="4.5"
                  fill="none"
                  stroke="#e90052"
                  strokeWidth="0.6"
                  strokeDasharray="1.5,1.5"
                  className="animate-spin origin-center"
                />
              )}

              {/* Ball Outer Glow */}
              <circle
                cx={startX}
                cy={startY}
                r="3.5"
                fill={actorColor}
                opacity="0.35"
                className="animate-ping"
              />

              {/* Core Player/Ball Node */}
              <circle
                cx={startX}
                cy={startY}
                r="2.4"
                fill="#ffffff"
                stroke={actorColor}
                strokeWidth="1.2"
              />

              {/* Actor Player Name Tag */}
              {currentEvent?.player?.name && (
                <g transform={`translate(${startX}, ${startY - 4})`}>
                  <rect
                    x="-14"
                    y="-3.8"
                    width="28"
                    height="4.8"
                    rx="1.4"
                    fill="rgba(10, 15, 25, 0.9)"
                    stroke={actorColor}
                    strokeWidth="0.4"
                  />
                  <text
                    x="0"
                    y="-0.8"
                    fill="#ffffff"
                    fontSize="2.4"
                    fontWeight="700"
                    textAnchor="middle"
                  >
                    {currentEvent.player.name.split(" ").slice(-1)[0]}
                  </text>
                </g>
              )}
            </g>
          </>
        )}
      </svg>

      {/* Focused Player Pill */}
      {focusedPlayer && (
        <div className="absolute top-12 left-3 flex items-center gap-2 bg-amber-500/20 border border-amber-500/50 backdrop-blur-md px-3 py-1 rounded-full text-xs font-semibold text-amber-300 z-20">
          <span>⭐ Focused: {focusedPlayer}</span>
          <button
            onClick={() => onSelectPlayer(null)}
            className="text-amber-200 hover:text-white ml-1 font-bold"
          >
            ✕
          </button>
        </div>
      )}

      {/* Quick Interactive Roster Bar for Player Focus Mode */}
      <div className="absolute bottom-2 left-2 right-2 bg-slate-950/85 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-800/80 flex items-center justify-between text-[11px] gap-2 z-20">
        <div className="flex items-center gap-1.5 overflow-x-auto custom-scrollbar">
          <span className="text-slate-400 font-semibold uppercase text-[10px] tracking-wider shrink-0 mr-1">
            Focus:
          </span>
          {["Bukayo Saka", "Martin Ødegaard", "Declan Rice", "Mohamed Salah", "Virgil van Dijk"].map(
            (p) => (
              <button
                key={p}
                onClick={() => onSelectPlayer(focusedPlayer === p ? null : p)}
                className={`px-2 py-0.5 rounded text-[10px] font-semibold transition-all shrink-0 ${
                  focusedPlayer === p
                    ? "bg-amber-400 text-slate-950 font-bold shadow-md shadow-amber-400/20"
                    : "bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800"
                }`}
              >
                {p}
              </button>
            )
          )}
        </div>
        <span className="text-slate-500 text-[10px] hidden sm:inline shrink-0">
          {overlayMode === "heatmap" ? "🔥 Heatmap Active" : overlayMode === "pass_network" ? "🕸️ Passing Flow" : "Click player to focus"}
        </span>
      </div>
    </div>
  );
};
