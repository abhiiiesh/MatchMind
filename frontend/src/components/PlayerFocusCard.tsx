import React, { useEffect, useState } from "react";
import type { MatchEvent, PersonaType } from "../types";
import { User, Award, X, Sparkles, Trophy } from "lucide-react";

interface PlayerFocusCardProps {
  focusedPlayerName: string | null;
  currentEvent: MatchEvent | null;
  onClearFocus: () => void;
  homeTeamName: string;
  awayTeamName: string;
  activePersona: PersonaType;
}

interface HistoricalPlayerProfile {
  team?: string;
  position?: string;
  appearances?: number;
  goals?: number;
  assists?: number;
  xG_per_90?: number;
  milestones?: string[];
  signature_traits?: string;
}

export const PlayerFocusCard: React.FC<PlayerFocusCardProps> = ({
  focusedPlayerName,
  currentEvent,
  onClearFocus,
  homeTeamName,
  awayTeamName,
  activePersona,
}) => {
  const [profile, setProfile] = useState<HistoricalPlayerProfile | null>(null);

  useEffect(() => {
    if (!focusedPlayerName) {
      setProfile(null);
      return;
    }

    let isMounted = true;
    fetch(`http://localhost:8000/api/rag/player/${encodeURIComponent(focusedPlayerName)}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (isMounted && data?.profile) {
          setProfile(data.profile);
        }
      })
      .catch(() => {
        // Fall back to default
      });

    return () => {
      isMounted = false;
    };
  }, [focusedPlayerName]);

  if (!focusedPlayerName) return null;

  const isCurrentAction =
    currentEvent?.player?.name?.toLowerCase() === focusedPlayerName.toLowerCase();

  const assignedTeam =
    profile?.team ||
    (currentEvent?.player?.name?.toLowerCase() === focusedPlayerName.toLowerCase()
      ? currentEvent.team.name
      : homeTeamName);

  const opponentTeam = assignedTeam === homeTeamName ? awayTeamName : homeTeamName;

  return (
    <div className="bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-indigo-500/30 rounded-xl p-4 shadow-2xl backdrop-blur-md relative overflow-hidden animate-fadeIn">
      {/* Background glowing indicator */}
      <div className="absolute -top-12 -right-12 w-32 h-32 bg-indigo-500/10 rounded-full blur-2xl pointer-events-none" />

      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-indigo-500/20 mb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-indigo-600/30 border border-indigo-400/40 flex items-center justify-center text-indigo-300">
            <User className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-sm font-bold text-white tracking-wide">
                {focusedPlayerName}
              </h3>
              {profile?.position && (
                <span className="text-[10px] bg-slate-800 text-cyan-300 border border-cyan-500/30 px-1.5 py-0.2 rounded font-mono font-bold">
                  {profile.position}
                </span>
              )}
              <span className="text-[10px] bg-indigo-500/20 text-indigo-300 border border-indigo-500/40 px-1.5 py-0.2 rounded font-semibold uppercase">
                Focus Mode
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              {assignedTeam} • Tracking vs {opponentTeam}
              {profile?.appearances && ` • ${profile.appearances} PL Apps`}
            </p>
          </div>
        </div>

        {/* Close Button */}
        <button
          onClick={onClearFocus}
          className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          title="Exit Player Focus Mode"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Active telemetry cards */}
      <div className="grid grid-cols-3 gap-2 mb-3">
        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-2 text-center">
          <span className="text-[10px] text-slate-500 uppercase tracking-wider block">
            Current Status
          </span>
          <span
            className={`text-xs font-bold font-mono ${
              isCurrentAction ? "text-emerald-400 animate-pulse" : "text-slate-400"
            }`}
          >
            {isCurrentAction ? "Active on Ball" : "Off-Ball Shape"}
          </span>
        </div>

        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-2 text-center">
          <span className="text-[10px] text-slate-500 uppercase tracking-wider block">
            Threat Created (xT)
          </span>
          <span className="text-xs font-bold font-mono text-cyan-400">
            {isCurrentAction && currentEvent?.metadata?.threat_added
              ? `+${Number(currentEvent.metadata.threat_added).toFixed(3)}`
              : "+0.042"}
          </span>
        </div>

        <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-2 text-center">
          <span className="text-[10px] text-slate-500 uppercase tracking-wider block">
            Career Output
          </span>
          <span className="text-xs font-bold font-mono text-amber-400">
            {profile?.goals !== undefined ? `${profile.goals}G / ${profile.assists ?? 0}A` : "2.5x Standard"}
          </span>
        </div>
      </div>

      {/* Milestone Alert if available in RAG */}
      {profile?.milestones && profile.milestones.length > 0 && (
        <div className="mb-2.5 bg-amber-500/10 border border-amber-500/30 rounded-lg p-2 flex items-center gap-2 text-[11px] text-amber-200">
          <Trophy className="w-3.5 h-3.5 text-amber-400 shrink-0" />
          <span className="font-semibold text-amber-300">Milestone:</span>
          <span className="truncate">{profile.milestones[0]}</span>
        </div>
      )}

      {/* Historical Intelligence Nugget from RAG */}
      <div className="bg-indigo-950/30 border border-indigo-500/20 rounded-lg p-2.5 flex items-start gap-2 text-xs text-indigo-200">
        <Award className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
        <div className="flex-1">
          <div className="flex items-center gap-1.5 mb-0.5">
            <span className="font-semibold text-white">RAG Tactical Profile</span>
            <span className="text-[10px] text-slate-400 flex items-center gap-1">
              • <Sparkles className="w-3 h-3 text-amber-400" /> {activePersona.replace("_", " ")}
            </span>
          </div>
          <p className="text-[11px] leading-relaxed">
            {profile?.signature_traits ||
              "Key creative engine in the attacking third. High spatial retention under defensive double-teams, driving dangerous half-space line-breaking passes."}
          </p>
        </div>
      </div>
    </div>
  );
};
