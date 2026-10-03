import React from "react";
import type { MetricState } from "../types";
import { Activity, Flame } from "lucide-react";


interface MomentumGraphProps {
  metrics: MetricState | null;
  homeTeamName: string;
  awayTeamName: string;
}

export const MomentumGraph: React.FC<MomentumGraphProps> = ({
  metrics,
  homeTeamName,
  awayTeamName,
}) => {
  const timeline = metrics?.momentum_timeline || [];
  const currentValue = metrics?.momentum_value ?? 0;
  const isShift = metrics?.momentum_shift_detected ?? false;

  // Generate SVG area points
  const width = 600;
  const height = 120;
  const centerY = height / 2;

  // If empty timeline, generate baseline
  const dataPoints =
    timeline.length > 0
      ? timeline
      : [
          { minute: 0, value: 0, is_shift: false, event_type: "Start" },
          { minute: metrics?.minute || 1, value: currentValue, is_shift: false, event_type: "Live" },
        ];

  const minMinute = Math.min(...dataPoints.map((d) => d.minute), 0);
  const maxMinute = Math.max(...dataPoints.map((d) => d.minute), 15);
  const minuteSpan = Math.max(1, maxMinute - minMinute);

  const getX = (min: number) => {
    return 30 + ((min - minMinute) / minuteSpan) * (width - 60);
  };

  const getY = (val: number) => {
    // val is [-100, 100], top is +100 (y = 10), bottom is -100 (y = height - 10)
    const normalized = -val / 100; // -1 to +1
    return centerY + normalized * (centerY - 14);
  };

  // Build path strings
  let pathD = "";
  let areaD = `M ${getX(dataPoints[0].minute)} ${centerY} `;

  dataPoints.forEach((pt, i) => {
    const x = getX(pt.minute);
    const y = getY(pt.value);
    if (i === 0) {
      pathD = `M ${x} ${y}`;
    } else {
      pathD += ` L ${x} ${y}`;
    }
    areaD += `L ${x} ${y} `;
  });

  const lastPoint = dataPoints[dataPoints.length - 1];
  areaD += `L ${getX(lastPoint.minute)} ${centerY} Z`;

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-xl backdrop-blur-md">
      {/* Header Bar */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-emerald-400 animate-pulse" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">
            Live Match Momentum Curve
          </h3>
          {isShift && (
            <span className="flex items-center gap-1 bg-amber-500/20 text-amber-300 border border-amber-500/30 text-[10px] px-2 py-0.5 rounded-full font-bold animate-pulse">
              <Flame className="w-3 h-3" /> Momentum Shift
            </span>
          )}
        </div>

        {/* Current Value Pill */}
        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-400 text-[11px]">Pressure Balance:</span>
          <span
            className={`font-mono font-bold px-2 py-0.5 rounded text-[11px] ${
              currentValue > 15
                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                : currentValue < -15
                ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                : "bg-slate-800 text-slate-300 border border-slate-700"
            }`}
          >
            {currentValue > 0
              ? `+${currentValue.toFixed(1)} ${homeTeamName}`
              : currentValue < 0
              ? `${currentValue.toFixed(1)} ${awayTeamName}`
              : "0.0 Neutral"}
          </span>
        </div>
      </div>

      {/* SVG Canvas */}
      <div className="relative w-full h-28 bg-slate-950/60 rounded-lg border border-slate-800/60 overflow-hidden">
        {/* Team Labels on Canvas */}
        <div className="absolute top-1.5 left-2 text-[10px] font-bold text-emerald-400/80 uppercase tracking-wider flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          {homeTeamName} Dominance (+100)
        </div>
        <div className="absolute bottom-1.5 left-2 text-[10px] font-bold text-rose-400/80 uppercase tracking-wider flex items-center gap-1">
          <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
          {awayTeamName} Dominance (-100)
        </div>

        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="w-full h-full overflow-visible"
          preserveAspectRatio="none"
        >
          <defs>
            {/* Gradient for Home Dominance */}
            <linearGradient id="momentumGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.45" />
              <stop offset="50%" stopColor="#10b981" stopOpacity="0.05" />
              <stop offset="50%" stopColor="#f43f5e" stopOpacity="0.05" />
              <stop offset="100%" stopColor="#f43f5e" stopOpacity="0.45" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          <line
            x1="30"
            y1={centerY}
            x2={width - 30}
            y2={centerY}
            stroke="#334155"
            strokeDasharray="3 3"
            strokeWidth="1"
          />

          {/* Area Fill */}
          <path d={areaD} fill="url(#momentumGradient)" />

          {/* Momentum Line */}
          <path
            d={pathD}
            fill="none"
            stroke={currentValue >= 0 ? "#10b981" : "#f43f5e"}
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />

          {/* Event markers on timeline */}
          {dataPoints.map((pt, idx) => {
            const cx = getX(pt.minute);
            const cy = getY(pt.value);
            const isLatest = idx === dataPoints.length - 1;

            if (!pt.is_shift && !isLatest) return null;

            return (
              <g key={idx}>
                {pt.is_shift && (
                  <circle
                    cx={cx}
                    cy={cy}
                    r="6"
                    className="animate-ping"
                    fill="#f59e0b"
                    opacity="0.7"
                  />
                )}
                <circle
                  cx={cx}
                  cy={cy}
                  r={isLatest ? "4.5" : "3.5"}
                  fill={pt.is_shift ? "#f59e0b" : isLatest ? "#38bdf8" : "#94a3b8"}
                  stroke="#0f172a"
                  strokeWidth="1.5"
                />
              </g>
            );
          })}
        </svg>
      </div>

      {/* Footer Subtext */}
      <div className="flex items-center justify-between text-[10px] text-slate-500 mt-2 font-mono">
        <span>Min {minMinute}'</span>
        <span>Centre Line: Tactical Neutral Equilibrium (0.0)</span>
        <span>Min {maxMinute}'</span>
      </div>
    </div>
  );
};
