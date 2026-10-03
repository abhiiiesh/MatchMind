import type { NarrativeOutput } from "../types";

interface ExplainabilityProps {
  narrative: NarrativeOutput | null;
}

export const ExplainabilityCard: React.FC<ExplainabilityProps> = ({ narrative }) => {
  if (!narrative) {
    return (
      <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4 text-center text-sm text-slate-500 italic">
        Awaiting live tactical sequence...
      </div>
    );
  }

  const isHighDrama = narrative.leverage_index >= 3.0;

  return (
    <div className="bg-gradient-to-br from-slate-900/95 to-slate-950/95 border border-emerald-500/30 rounded-xl p-4 shadow-xl backdrop-blur-md relative overflow-hidden transition-all duration-300">
      {/* Decorative gradient beam */}
      <div className="absolute -top-12 -right-12 w-36 h-36 bg-emerald-500/10 rounded-full blur-2xl pointer-events-none" />

      {/* Top Meta Bar */}
      <div className="flex items-center justify-between gap-2 mb-2.5">
        <div className="flex items-center gap-2">
          <span className="text-base">💡</span>
          <span className="text-xs font-bold uppercase tracking-wider text-emerald-400">
            Why This Moment Matters
          </span>
        </div>
        <div className="flex items-center gap-1.5 bg-emerald-950/60 border border-emerald-500/30 px-2 py-0.5 rounded-full text-[11px] font-semibold text-emerald-300">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          <span>Verified Telemetry</span>
        </div>
      </div>

      {/* Story Arc */}
      <div className="text-xs font-semibold text-slate-400 mb-1.5">
        Tactical Phase:{" "}
        <span className="text-slate-100 font-bold">{narrative.game_state_arc}</span>
      </div>

      {/* Core Explanation */}
      <p className="text-sm text-slate-200 leading-relaxed font-normal">
        {narrative.why_it_matters_explanation}
      </p>

      {/* Leverage & Timing Footer */}
      <div className="mt-3 pt-2.5 border-t border-slate-800/80 flex items-center justify-between text-xs text-slate-400">
        <span className="font-medium">
          Match Minute: <b className="text-slate-200">{narrative.minute}'</b>
        </span>
        <div className="flex items-center gap-1">
          <span>Emotional Leverage:</span>
          <span
            className={`font-black px-1.5 py-0.5 rounded text-[11px] ${
              isHighDrama
                ? "bg-rose-500/20 text-rose-300 border border-rose-500/50 animate-pulse"
                : "bg-slate-800 text-slate-300"
            }`}
          >
            {narrative.leverage_index.toFixed(1)}x
          </span>
        </div>
      </div>
    </div>
  );
};
