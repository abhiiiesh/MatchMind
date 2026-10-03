import React from "react";
import type { MatchEvent } from "../types";

interface PitchProps {
  currentEvent: MatchEvent | null;
  homeTeamName: string;
  awayTeamName: string;
  focusedPlayer: string | null;
  onSelectPlayer: (playerName: string | null) => void;
}

export const PitchVisualization: React.FC<PitchProps> = ({
  currentEvent,
  homeTeamName,
  awayTeamName,
  focusedPlayer,
  onSelectPlayer,
}) => {
  // StatsBomb coordinates: 0..120 X, 0..80 Y
  const startX = currentEvent?.start_x ?? 60;
  const startY = currentEvent?.start_y ?? 40;
  const endX = currentEvent?.end_x;
  const endY = currentEvent?.end_y;
  const isHome = currentEvent?.team?.name === homeTeamName;
  const actorColor = isHome ? "#00ff87" : "#e90052";

  return (
    <div className="relative w-full aspect-[120/80] bg-[#1a472a] rounded-xl overflow-hidden border border-emerald-900/60 shadow-2xl">
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

        {/* Outer Boundary Line */}
        <rect
          x="3"
          y="3"
          width="114"
          height="74"
          fill="none"
          stroke="rgba(255, 255, 255, 0.45)"
          strokeWidth="0.8"
        />

        {/* Halfway Line */}
        <line
          x1="60"
          y1="3"
          x2="60"
          y2="77"
          stroke="rgba(255, 255, 255, 0.45)"
          strokeWidth="0.8"
        />

        {/* Center Circle & Spot */}
        <circle
          cx="60"
          cy="40"
          r="10"
          fill="none"
          stroke="rgba(255, 255, 255, 0.45)"
          strokeWidth="0.8"
        />
        <circle cx="60" cy="40" r="0.8" fill="rgba(255, 255, 255, 0.75)" />

        {/* Left Penalty Area (Away Box or Home Defending) */}
        <rect
          x="3"
          y="18"
          width="18"
          height="44"
          fill="none"
          stroke="rgba(255, 255, 255, 0.45)"
          strokeWidth="0.8"
        />
        {/* Left 6-Yard Box */}
        <rect
          x="3"
          y="30"
          width="6"
          height="20"
          fill="none"
          stroke="rgba(255, 255, 255, 0.45)"
          strokeWidth="0.8"
        />
        {/* Left Penalty Spot & Arc */}
        <circle cx="15" cy="40" r="0.8" fill="rgba(255, 255, 255, 0.75)" />
        <path
          d="M 21 34 A 10 10 0 0 1 21 46"
          fill="none"
          stroke="rgba(255, 255, 255, 0.45)"
          strokeWidth="0.8"
        />

        {/* Right Penalty Area (Attacking Goal) */}
        <rect
          x="99"
          y="18"
          width="18"
          height="44"
          fill="none"
          stroke="rgba(255, 255, 255, 0.45)"
          strokeWidth="0.8"
        />
        {/* Right 6-Yard Box */}
        <rect
          x="111"
          y="30"
          width="6"
          height="20"
          fill="none"
          stroke="rgba(255, 255, 255, 0.45)"
          strokeWidth="0.8"
        />
        {/* Right Penalty Spot & Arc */}
        <circle cx="105" cy="40" r="0.8" fill="rgba(255, 255, 255, 0.75)" />
        <path
          d="M 99 34 A 10 10 0 0 0 99 46"
          fill="none"
          stroke="rgba(255, 255, 255, 0.45)"
          strokeWidth="0.8"
        />

        {/* Goal Frames */}
        <rect x="0.5" y="36" width="2.5" height="8" fill="none" stroke="rgba(255,255,255,0.7)" strokeWidth="0.6" />
        <rect x="117" y="36" width="2.5" height="8" fill="none" stroke="rgba(255,255,255,0.7)" strokeWidth="0.6" />

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
            {/* Target End Point */}
            <circle
              cx={endX}
              cy={endY}
              r="1.8"
              fill={currentEvent?.event_type === "Shot" ? "#ffeb3b" : actorColor}
              opacity="0.8"
            />
          </g>
        )}

        {/* Ball Location Pulse */}
        <g className="cursor-pointer" onClick={() => onSelectPlayer(currentEvent?.player?.name ?? null)}>
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
            r="3.2"
            fill={actorColor}
            opacity="0.3"
            className="animate-ping"
          />

          {/* Core Player/Ball Node */}
          <circle
            cx={startX}
            cy={startY}
            r="2.2"
            fill="#ffffff"
            stroke={actorColor}
            strokeWidth="1"
          />

          {/* Actor Player Name Tag */}
          {currentEvent?.player?.name && (
            <g transform={`translate(${startX}, ${startY - 4})`}>
              <rect
                x="-12"
                y="-3.5"
                width="24"
                height="4.5"
                rx="1.2"
                fill="rgba(10, 15, 25, 0.85)"
                stroke={actorColor}
                strokeWidth="0.3"
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
      </svg>

      {/* Overlay Badges */}
      <div className="absolute top-3 left-4 flex items-center gap-2 bg-slate-900/80 backdrop-blur-md px-3 py-1.5 rounded-full border border-slate-700/60 text-xs font-semibold">
        <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
        <span className="text-emerald-400 font-bold">{homeTeamName}</span>
        <span className="text-slate-400">vs</span>
        <span className="text-rose-400 font-bold">{awayTeamName}</span>
      </div>

      {focusedPlayer && (
        <div className="absolute top-3 right-4 flex items-center gap-2 bg-amber-500/20 border border-amber-500/50 backdrop-blur-md px-3 py-1.5 rounded-full text-xs font-semibold text-amber-300">
          <span>⭐ Focused: {focusedPlayer}</span>
          <button
            onClick={() => onSelectPlayer(null)}
            className="text-amber-200 hover:text-white ml-1 font-bold"
          >
            ✕
          </button>
        </div>
      )}
    </div>
  );
};
