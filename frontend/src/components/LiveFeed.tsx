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

  const getCommentary = (
    msg: VerifiedMessagePayload
  ): { text: string; isTranslated: boolean; langBadge: string } => {
    const narrative = msg.narrative;
    const personaText =
      narrative.commentary_by_persona?.[activePersona] ||
      narrative.commentary_by_persona?.["broadcast_commentator"] ||
      narrative.why_it_matters_explanation ||
      "";

    if (activeLanguage === "en") {
      return { text: personaText, isTranslated: true, langBadge: "EN" };
    }

    // Check persona-specific translation if available
    const personaTranslations = (narrative as any).translations_by_persona?.[activePersona];
    if (personaTranslations && personaTranslations[activeLanguage]) {
      const trans = personaTranslations[activeLanguage];
      if (trans && trans !== personaText) {
        return { text: trans, isTranslated: true, langBadge: activeLanguage.toUpperCase() };
      }
    }

    // Fall back to general translations
    if (narrative.translations && narrative.translations[activeLanguage]) {
      const trans = narrative.translations[activeLanguage];
      if (trans && trans !== personaText) {
        return { text: trans, isTranslated: true, langBadge: activeLanguage.toUpperCase() };
      }
    }

    return { text: personaText, isTranslated: false, langBadge: "EN (Pending)" };
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
        <div className="flex items-center gap-2 text-xs text-slate-400 font-medium">
          {activeLanguage !== "en" && (
            <span className="bg-slate-800 border border-slate-700 text-slate-300 px-1.5 py-0.5 rounded text-[10px] font-mono uppercase">
              Target: {activeLanguage}
            </span>
          )}
          <span>{messages.length} events logged</span>
        </div>
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
            const { text, isTranslated, langBadge } = getCommentary(msg);
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
                    {activeLanguage !== "en" && (
                      <span
                        className={`text-[9px] font-mono px-1.5 py-0.2 rounded font-bold uppercase border ${
                          isTranslated
                            ? "bg-emerald-950/60 text-emerald-300 border-emerald-500/30"
                            : "bg-amber-950/60 text-amber-300 border-amber-500/30"
                        }`}
                        title={
                          isTranslated
                            ? `Commentary translated to ${activeLanguage}`
                            : "Translation unavailable; displaying original English"
                        }
                      >
                        {langBadge}
                      </span>
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
