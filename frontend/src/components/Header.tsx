import React from "react";
import type { LanguageCode, MatchSummary, PersonaType } from "../types";
import { apiUrl } from "../api";

interface HeaderProps {
  activePersona: PersonaType;
  onSelectPersona: (p: PersonaType) => void;
  activeLanguage: LanguageCode;
  onSelectLanguage: (l: LanguageCode) => void;
  onTriggerSimulation: (source: "synthetic" | "statsbomb") => void;
  isSimulating: boolean;
  matchId: string;
  matches: MatchSummary[];
  onSelectMatch: (matchId: string) => void;
}

export const Header: React.FC<HeaderProps> = ({
  activePersona,
  onSelectPersona,
  activeLanguage,
  onSelectLanguage,
  onTriggerSimulation,
  isSimulating,
  matchId,
  matches,
  onSelectMatch,
}) => {
  return (
    <header className="bg-slate-950/90 border-b border-slate-800/80 px-4 py-3 backdrop-blur-md sticky top-0 z-50 flex flex-wrap items-center justify-between gap-3">
      {/* Brand & Match Selector */}
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-[#38003c] to-[#00ff87] flex items-center justify-center font-black text-white text-lg shadow-lg shadow-emerald-950/50">
          M
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-base font-black tracking-tight text-white">
              MatchMind
            </h1>
            <span className="bg-[#38003c] border border-emerald-500/40 text-[#00ff87] text-[10px] font-black uppercase px-2 py-0.5 rounded-full tracking-wider">
              Premier League AI
            </span>
          </div>
          <p className="text-[11px] text-slate-400">
            Multi-Agent Explainable Football Intelligence
          </p>
        </div>

        {/* Phase B: Premier League Match Fixture Dropdown */}
        <div className="hidden sm:flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 ml-2 shadow-inner">
          <span className="text-xs">⚽</span>
          <select
            value={matchId}
            onChange={(e) => onSelectMatch(e.target.value)}
            className="bg-transparent text-xs font-bold text-slate-100 outline-none cursor-pointer max-w-[240px] truncate"
            title="Switch Premier League match fixture"
          >
            {matches.map((m) => (
              <option key={m.match_id} value={m.match_id} className="bg-slate-900 text-slate-200">
                {m.source_type === "statsbomb" ? "🏆 " : "⚡ "}
                {m.home_team} vs {m.away_team} ({m.final_score.home}-{m.final_score.away})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Middle Persona Bar */}
      <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-1 gap-1">
        <button
          onClick={() => onSelectPersona("casual_fan")}
          className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
            activePersona === "casual_fan"
              ? "bg-emerald-500 text-slate-950 shadow-md font-bold"
              : "text-slate-400 hover:text-white"
          }`}
        >
          🎉 Casual Fan
        </button>
        <button
          onClick={() => onSelectPersona("tactical_analyst")}
          className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
            activePersona === "tactical_analyst"
              ? "bg-emerald-500 text-slate-950 shadow-md font-bold"
              : "text-slate-400 hover:text-white"
          }`}
        >
          🔬 Tactical Analyst
        </button>
        <button
          onClick={() => onSelectPersona("broadcast_commentator")}
          className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
            activePersona === "broadcast_commentator"
              ? "bg-emerald-500 text-slate-950 shadow-md font-bold"
              : "text-slate-400 hover:text-white"
          }`}
        >
          🎙️ Broadcast
        </button>
        <button
          onClick={() => onSelectPersona("accessibility_audio")}
          className={`px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
            activePersona === "accessibility_audio"
              ? "bg-emerald-500 text-slate-950 shadow-md font-bold"
              : "text-slate-400 hover:text-white"
          }`}
        >
          ♿ Audio Description
        </button>
      </div>

      {/* Right Controls: Language & Simulation Triggers */}
      <div className="flex items-center gap-2.5">
        {/* Language selector */}
        <select
          value={activeLanguage}
          onChange={(e) => onSelectLanguage(e.target.value as LanguageCode)}
          className="bg-slate-900 border border-slate-800 text-xs font-semibold text-slate-200 rounded-lg px-2.5 py-1.5 outline-none focus:border-emerald-500 cursor-pointer"
        >
          <option value="en">🇬🇧 English</option>
          <option value="es">🇪🇸 Español</option>
          <option value="hi">🇮🇳 हिन्दी</option>
          <option value="ar">🇸🇦 العربية</option>
          <option value="pt">🇧🇷 Português</option>
          <option value="fr">🇫🇷 Français</option>
        </select>

        {/* Live Simulation Button */}
        <button
          onClick={() => onTriggerSimulation("synthetic")}
          disabled={isSimulating}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all shadow-md ${
            isSimulating
              ? "bg-slate-800 text-slate-500 cursor-not-allowed"
              : "bg-emerald-400 hover:bg-emerald-300 text-slate-950 shadow-emerald-950/40"
          }`}
        >
          {isSimulating ? (
            <>
              <span className="w-2 h-2 rounded-full bg-slate-500 animate-ping" />
              <span>Simulating...</span>
            </>
          ) : (
            <>
              <span>▶ Live Stream</span>
            </>
          )}
        </button>

        {/* Open OBS Overlay in new window */}
        <a
          href={apiUrl(`/overlay?match_id=${matchId}&persona=${activePersona}&lang=${activeLanguage}`)}
          target="_blank"
          rel="noreferrer"
          className="text-xs text-slate-400 hover:text-emerald-400 font-semibold border border-slate-800 hover:border-emerald-500/50 px-2.5 py-1.5 rounded-lg transition-all"
          title="Open transparent broadcast overlay for OBS Studio / CasparCG"
        >
          📺 OBS Overlay
        </a>
      </div>
    </header>
  );
};
