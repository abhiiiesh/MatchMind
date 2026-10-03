import type { MetricState } from "../types";

interface MetricsProps {
  metrics: MetricState | null;
}

export const MetricsPanel: React.FC<MetricsProps> = ({ metrics }) => {
  const homeXG = metrics?.cumulative_xg?.home ?? 0.0;
  const awayXG = metrics?.cumulative_xg?.away ?? 0.0;
  const totalXG = Math.max(0.1, homeXG + awayXG);
  const homeXGPercent = Math.round((homeXG / totalXG) * 100);

  const fieldTilt = metrics?.field_tilt ?? 50.0;
  const leverage = metrics?.current_leverage_index ?? 1.0;
  const homePpda = metrics?.rolling_ppda?.home ?? 11.5;
  const awayPpda = metrics?.rolling_ppda?.away ?? 11.5;

  const getPpdaLabel = (val: number) => {
    if (val <= 8.0) return { text: "Aggressive High Press", color: "text-rose-400" };
    if (val <= 13.0) return { text: "Active Mid-Block", color: "text-amber-400" };
    return { text: "Passive Low-Block", color: "text-blue-400" };
  };

  const homePress = getPpdaLabel(homePpda);

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-3 w-full">
      {/* 1. Score & Match State */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5 backdrop-blur-md flex flex-col justify-between">
        <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Match Score</div>
        <div className="flex items-center justify-between my-1">
          <div className="text-sm font-bold text-emerald-400 truncate max-w-[80px]">{metrics?.home_team ?? "Home"}</div>
          <div className="text-2xl font-black tracking-tight text-white px-2">
            {metrics?.score?.home ?? 0} <span className="text-slate-500 font-light">-</span> {metrics?.score?.away ?? 0}
          </div>
          <div className="text-sm font-bold text-rose-400 truncate max-w-[80px] text-right">{metrics?.away_team ?? "Away"}</div>
        </div>
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>Clock: <b className="text-emerald-400">{metrics?.minute ?? 0}'</b></span>
          <span className="capitalize text-slate-300 font-medium">{metrics?.momentum_direction?.replace("_", " ") ?? "Balanced"}</span>
        </div>
      </div>

      {/* 2. Expected Goals (xG) */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5 backdrop-blur-md flex flex-col justify-between">
        <div className="flex justify-between items-center text-xs text-slate-400 font-semibold uppercase tracking-wider">
          <span>Expected Goals (xG)</span>
          <span className="text-slate-300 font-bold">{homeXG.toFixed(2)} vs {awayXG.toFixed(2)}</span>
        </div>
        <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden flex my-2">
          <div
            style={{ width: `${homeXGPercent}%` }}
            className="bg-emerald-400 h-full transition-all duration-500"
          />
          <div
            style={{ width: `${100 - homeXGPercent}%` }}
            className="bg-rose-500 h-full transition-all duration-500"
          />
        </div>
        <div className="flex justify-between text-xs font-medium text-slate-400">
          <span className="text-emerald-400">{homeXGPercent}% threat</span>
          <span className="text-rose-400">{100 - homeXGPercent}% threat</span>
        </div>
      </div>

      {/* 3. Pressing Intensity (PPDA) */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5 backdrop-blur-md flex flex-col justify-between">
        <div className="text-xs text-slate-400 font-semibold uppercase tracking-wider">
          Pressing Intensity (PPDA)
        </div>
        <div className="flex items-baseline justify-between my-1">
          <span className="text-2xl font-black text-white">{homePpda.toFixed(1)}</span>
          <span className={`text-xs font-semibold ${homePress.color}`}>{homePress.text}</span>
        </div>
        <div className="text-xs text-slate-400 truncate">
          Away team PPDA: <b className="text-slate-200">{awayPpda.toFixed(1)}</b>
        </div>
      </div>

      {/* 4. Field Tilt & Leverage */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5 backdrop-blur-md flex flex-col justify-between">
        <div className="flex justify-between items-center text-xs text-slate-400 font-semibold uppercase tracking-wider">
          <span>Field Tilt</span>
          <span className="text-emerald-400 font-bold">{fieldTilt.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-slate-800 h-2.5 rounded-full overflow-hidden flex my-2">
          <div
            style={{ width: `${fieldTilt}%` }}
            className="bg-gradient-to-r from-emerald-500 to-teal-400 h-full transition-all duration-500"
          />
        </div>
        <div className="flex justify-between items-center text-xs text-slate-400">
          <span>Territorial Pressure</span>
          <span className={`font-bold px-1.5 py-0.5 rounded text-[11px] ${leverage >= 3.0 ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40' : 'bg-slate-800 text-slate-300'}`}>
            Lev: {leverage.toFixed(1)}x
          </span>
        </div>
      </div>
    </div>
  );
};
