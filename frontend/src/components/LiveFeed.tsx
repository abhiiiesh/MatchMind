import React, { useEffect, useRef } from "react";
import type { LanguageCode, PersonaType, VerifiedMessagePayload } from "../types";

interface LiveFeedProps {
  messages: VerifiedMessagePayload[];
  activePersona: PersonaType;
  activeLanguage: LanguageCode;
  onSelectPlayer?: (playerName: string) => void;
}

export const LiveFeed: React.FC<LiveFeedProps> = ({
  messages,
  activePersona,
  activeLanguage,
  onSelectPlayer,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTo({
        top: containerRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages]);

  const getCommentaryText = (msg: VerifiedMessagePayload): string => {
    const narrative = msg.narrative;
    if (activeLanguage !== "en" && narrative.translations && narrative.translations[activeLanguage]) {
      return narrative.translations[activeLanguage];
    }
    return (
      narrative.commentary_by_persona[activePersona] ||
      narrative.commentary_by_persona["broadcast_commentator"] ||
      ""
    );
  };

  return (
    <div className="flex flex-col h-full bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden backdrop-blur-md">
      {/* Header */}
      <div className="p-3.5 border-b border-slate-800/80 flex items-center justify-between bg-slate-950/40">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          <span className="text-xs font-bold uppercase tracking-wider text-slate-200">
            Live Intelligence Stream
          </span>
        </div>
        <span className="text-xs text-slate-400 font-medium">
          {messages.length} events logged
        </span>
      </div>

      {/* Scrolling Content */}
      <div ref={containerRef} className="flex-1 overflow-y-auto p-3.5 space-y-3 custom-scrollbar max-h-[460px]">
        {messages.length === 0 ? (
          <div className="text-center py-12 text-slate-500 text-sm italic">
            Connecting to multi-agent stream... Trigger simulation to see live narratives.
          </div>
        ) : (
          messages.map((msg, idx) => {
            const isGoal = msg.event.outcome === "Goal";
            const text = getCommentaryText(msg);
            const playerName = msg.event.player?.name;

            return (
              <div
                key={`${msg.event.event_id}-${idx}`}
                className={`p-3 rounded-lg border transition-all duration-200 ${
                  isGoal
                    ? "bg-rose-950/40 border-rose-500/60 shadow-lg shadow-rose-950/30"
                    : "bg-slate-950/40 border-slate-800/60 hover:border-slate-700"
                }`}
              >
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="font-bold text-emerald-400 bg-emerald-950/50 px-1.5 py-0.5 rounded text-[11px]">
                      {msg.metric_state.minute}'
                    </span>
                    <span className="font-semibold text-slate-300">
                      {msg.event.team.name}
                    </span>
                    <span className="text-slate-500">•</span>
                    <span className="text-slate-400 capitalize">
                      {msg.event.event_type}
                    </span>
                    {playerName && (
                      <button
                        onClick={() => onSelectPlayer?.(playerName)}
                        className="text-[11px] bg-indigo-500/10 hover:bg-indigo-500/30 text-indigo-300 border border-indigo-500/30 px-1.5 py-0.2 rounded transition-colors ml-1 font-medium"
                        title={`Click to focus on ${playerName}`}
                      >
                        👤 {playerName}
                      </button>
                    )}
                  </div>

                  {isGoal && (
                    <span className="bg-rose-500 text-white font-extrabold text-[10px] px-2 py-0.5 rounded-full uppercase tracking-wider animate-bounce">
                      GOAL!
                    </span>
                  )}
                </div>

                <p className="text-xs md:text-sm text-slate-200 leading-relaxed font-normal">
                  {text}
                </p>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
