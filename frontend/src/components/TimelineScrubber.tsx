import React, { useState } from "react";
import type { KeyMoment, MatchTimelineInfo } from "../types";

interface TimelineScrubberProps {
  timeline: MatchTimelineInfo | null;
  onPlay: (speed: number) => void;
  onPause: () => void;
  onReset: () => void;
  onSeekMinute: (minute: number) => void;
  onSeekMoment: (momentId: string) => void;
  onStep: (forward: boolean) => void;
}

export const TimelineScrubber: React.FC<TimelineScrubberProps> = ({
  timeline,
  onPlay,
  onPause,
  onReset,
  onSeekMinute,
  onSeekMoment,
  onStep,
}) => {
  const [hoveredMoment, setHoveredMoment] = useState<KeyMoment | null>(null);
  const [tooltipPos, setTooltipPos] = useState<{ x: number; y: number } | null>(null);

  const duration = timeline?.duration_minutes || 95;
  const currentMinute = timeline?.current_minute || 0;
  const currentSecond = timeline?.current_second || 0;
  const isPlaying = timeline?.is_playing || false;
  const currentSpeed = timeline?.speed || 1.0;
  const keyMoments = timeline?.key_moments || [];

  const progressPct = Math.min(100, Math.max(0, (currentMinute / duration) * 100));

  const handleTrackClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const clickRatio = Math.max(0, Math.min(1, clickX / rect.width));
    const targetMinute = Math.round(clickRatio * duration);
    onSeekMinute(targetMinute);
  };

  const getMomentIcon = (type: string) => {
    switch (type) {
      case "GOAL":
        return "⚽";
      case "RED_CARD":
        return "🟥";
      case "YELLOW_CARD":
        return "🟨";
      case "BIG_CHANCE":
        return "⚡";
      default:
        return "📌";
    }
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800/90 rounded-xl p-3.5 backdrop-blur-md shadow-xl flex flex-col gap-3 relative">
      {/* Top Status & Controls Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2.5">
        {/* Left: Live Match Clock */}
        <div className="flex items-center gap-2.5">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-950 border border-slate-800">
            <span
              className={`w-2 h-2 rounded-full ${
                isPlaying ? "bg-emerald-400 animate-pulse shadow-sm shadow-emerald-400" : "bg-slate-500"
              }`}
            />
            <span className="font-mono text-xs font-black tracking-wider text-white">
              {String(currentMinute).padStart(2, "0")}:{String(currentSecond).padStart(2, "0")}
            </span>
            <span className="text-[10px] uppercase font-bold text-slate-400 border-l border-slate-800 pl-1.5">
              {currentMinute < 45 ? "1st Half" : currentMinute < 90 ? "2nd Half" : "Stoppage"}
            </span>
          </div>

          {timeline && (
            <div className="text-xs font-bold text-slate-300 bg-slate-950/80 border border-slate-800/80 px-2.5 py-1 rounded-md flex items-center gap-2">
              <span className="text-slate-300">{timeline.home_team}</span>
              <span className="text-emerald-400 font-mono font-black text-sm">
                {timeline.current_score?.home ?? 0} - {timeline.current_score?.away ?? 0}
              </span>
              <span className="text-slate-300">{timeline.away_team}</span>
              <span
                className="text-[10px] text-slate-500 font-semibold bg-slate-900 px-1.5 py-0.5 rounded border border-slate-800"
                title="Full-time fixture outcome"
              >
                FT {timeline.final_score.home}-{timeline.final_score.away}
              </span>
            </div>
          )}
        </div>

        {/* Center: Playback Buttons */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={onReset}
            title="Reset to minute 0"
            className="px-2 py-1 bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-md transition-all"
          >
            ↺ 0'
          </button>
          <button
            onClick={() => onStep(false)}
            title="Step 1 event backward"
            className="px-2 py-1 bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-md transition-all"
          >
            ⏮ Step
          </button>
          <button
            onClick={() => (isPlaying ? onPause() : onPlay(currentSpeed))}
            className={`px-3.5 py-1 rounded-md text-xs font-black tracking-wide flex items-center gap-1.5 shadow-md transition-all ${
              isPlaying
                ? "bg-amber-500 hover:bg-amber-400 text-slate-950"
                : "bg-emerald-500 hover:bg-emerald-400 text-slate-950 shadow-emerald-950/50"
            }`}
          >
            {isPlaying ? "⏸ Pause" : "▶ Play"}
          </button>
          <button
            onClick={() => onStep(true)}
            title="Step 1 event forward"
            className="px-2 py-1 bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-xs font-semibold rounded-md transition-all"
          >
            Step ⏭
          </button>
        </div>

        {/* Right: Playback Speed Selector */}
        <div className="flex items-center bg-slate-950 border border-slate-800 rounded-md p-0.5 gap-0.5">
          {[1.0, 2.0, 5.0].map((spd) => (
            <button
              key={spd}
              onClick={() => onPlay(spd)}
              className={`px-2 py-0.5 rounded text-[11px] font-bold transition-all ${
                currentSpeed === spd && isPlaying
                  ? "bg-emerald-500 text-slate-950"
                  : "text-slate-400 hover:text-slate-200"
              }`}
            >
              {spd}x
            </button>
          ))}
        </div>
      </div>

      {/* Middle Interactive Track */}
      <div className="flex flex-col gap-1 select-none pt-1">
        <div
          onClick={handleTrackClick}
          className="relative h-6 bg-slate-950 border border-slate-800 rounded-lg cursor-pointer overflow-visible group"
        >
          {/* Pitch grass subtle pattern */}
          <div className="absolute inset-0 opacity-20 bg-[linear-gradient(90deg,transparent_49%,rgba(255,255,255,0.05)_50%,transparent_51%)] bg-[length:10%_100%]" />

          {/* Filled progress bar */}
          <div
            className="absolute top-0 left-0 bottom-0 bg-gradient-to-r from-emerald-600 via-emerald-500 to-teal-400 rounded-l-lg opacity-80 transition-all duration-150"
            style={{ width: `${progressPct}%` }}
          />

          {/* Scrubber thumb cursor */}
          <div
            className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 w-4 h-7 bg-white rounded border-2 border-emerald-500 shadow-lg shadow-emerald-500/50 pointer-events-none z-20 transition-all duration-150 flex items-center justify-center"
            style={{ left: `${progressPct}%` }}
          >
            <div className="w-0.5 h-3 bg-slate-600 rounded" />
          </div>

          {/* Key moment highlight pins */}
          {keyMoments.map((m) => {
            const mPct = (m.minute / duration) * 100;
            const isGoal = m.moment_type === "GOAL";
            const isRedCard = m.moment_type === "RED_CARD";
            return (
              <div
                key={m.id}
                onClick={(e) => {
                  e.stopPropagation();
                  onSeekMoment(m.id);
                }}
                onMouseEnter={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect();
                  setHoveredMoment(m);
                  setTooltipPos({ x: rect.left, y: rect.top - 8 });
                }}
                onMouseLeave={() => setHoveredMoment(null)}
                className={`absolute top-1/2 -translate-y-1/2 -translate-x-1/2 z-10 w-5 h-5 rounded-full flex items-center justify-center text-[10px] cursor-pointer transition-transform hover:scale-130 ${
                  isGoal
                    ? "bg-emerald-500 text-white ring-2 ring-emerald-300 shadow-md shadow-emerald-500/50"
                    : isRedCard
                    ? "bg-red-600 text-white ring-2 ring-red-400 shadow-md shadow-red-500/50"
                    : "bg-amber-400 text-slate-950 ring-2 ring-amber-200"
                }`}
                style={{ left: `${mPct}%` }}
              >
                {getMomentIcon(m.moment_type)}
              </div>
            );
          })}
        </div>

        {/* Timeline Minute Ticks */}
        <div className="flex justify-between text-[10px] font-mono text-slate-500 px-1">
          <span>0'</span>
          <span>15'</span>
          <span>30'</span>
          <span className="text-slate-400 font-bold">HT 45'</span>
          <span>60'</span>
          <span>75'</span>
          <span>90'</span>
          <span>{duration}'</span>
        </div>
      </div>

      {/* Quick-Jump Highlight Pills */}
      {keyMoments.length > 0 && (
        <div className="flex items-center gap-1.5 overflow-x-auto pb-0.5 pt-0.5 scrollbar-thin scrollbar-thumb-slate-800">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex-shrink-0">
            ⚡ Highlights:
          </span>
          {keyMoments.map((m) => (
            <button
              key={m.id}
              onClick={() => onSeekMoment(m.id)}
              className="flex-shrink-0 text-[11px] font-semibold bg-slate-950/80 hover:bg-slate-800 border border-slate-800 hover:border-emerald-500/60 text-slate-200 px-2 py-1 rounded-md transition-all flex items-center gap-1"
            >
              <span>{getMomentIcon(m.moment_type)}</span>
              <span className="font-mono text-emerald-400">{m.minute}'</span>
              <span>{m.player}</span>
              <span className="text-slate-400 text-[10px]">({m.score_after})</span>
            </button>
          ))}
        </div>
      )}

      {/* Floating Hover Tooltip */}
      {hoveredMoment && tooltipPos && (
        <div
          className="fixed z-50 -translate-x-1/2 -translate-y-full bg-slate-950 border border-emerald-500/80 rounded-lg p-2 shadow-2xl shadow-emerald-950/80 text-xs w-60 pointer-events-none backdrop-blur-md"
          style={{ left: tooltipPos.x, top: tooltipPos.y }}
        >
          <div className="flex items-center justify-between text-[11px] font-bold border-b border-slate-800 pb-1 mb-1">
            <span className="text-emerald-400">
              {hoveredMoment.minute}' {getMomentIcon(hoveredMoment.moment_type)} {hoveredMoment.moment_type}
            </span>
            <span className="text-white font-mono">{hoveredMoment.score_after}</span>
          </div>
          <p className="text-slate-200 text-[11px] leading-snug">{hoveredMoment.description}</p>
          <div className="flex items-center justify-between text-[10px] text-slate-400 mt-1.5 pt-1 border-t border-slate-900">
            <span>Player: {hoveredMoment.player}</span>
            {hoveredMoment.xg && <span>xG: {hoveredMoment.xg}</span>}
          </div>
        </div>
      )}
    </div>
  );
};
