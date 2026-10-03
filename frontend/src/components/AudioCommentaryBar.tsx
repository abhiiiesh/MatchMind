import React, { useState, useEffect, useRef } from "react";
import type { LanguageCode, NarrativeOutput, PersonaType } from "../types";
import { Volume2, VolumeX, Play, Pause, Radio, Headphones } from "lucide-react";

interface AudioCommentaryBarProps {
  latestNarrative: NarrativeOutput | null;
  activePersona: PersonaType;
  activeLanguage?: LanguageCode;
}

export const AudioCommentaryBar: React.FC<AudioCommentaryBarProps> = ({
  latestNarrative,
  activePersona,
  activeLanguage = "en",
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [useAccessibilityAudio, setUseAccessibilityAudio] = useState(false);
  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([]);
  const lastSpokenIdRef = useRef<string | null>(null);

  // Load voices reliably across Chromium and WebKit
  useEffect(() => {
    if (typeof window === "undefined" || !window.speechSynthesis) return;

    const updateVoices = () => {
      const voices = window.speechSynthesis.getVoices();
      if (voices.length > 0) {
        setAvailableVoices(voices);
      }
    };

    updateVoices();
    window.speechSynthesis.onvoiceschanged = updateVoices;

    return () => {
      if (window.speechSynthesis) {
        window.speechSynthesis.onvoiceschanged = null;
      }
    };
  }, []);

  // Read aloud commentary when new verified message arrives
  useEffect(() => {
    if (!isPlaying || isMuted || !latestNarrative || !window.speechSynthesis) return;

    const speechKey = `${latestNarrative.narrative_id}-${activePersona}-${activeLanguage}-${useAccessibilityAudio}`;
    if (speechKey === lastSpokenIdRef.current) return;
    lastSpokenIdRef.current = speechKey;

    // Pick commentary text (multilingual if selected)
    let textToSpeak = "";
    if (activeLanguage !== "en" && latestNarrative.translations?.[activeLanguage]) {
      textToSpeak = latestNarrative.translations[activeLanguage];
    } else if (useAccessibilityAudio) {
      textToSpeak =
        latestNarrative.commentary_by_persona?.accessibility_audio ||
        latestNarrative.why_it_matters_explanation;
    } else {
      textToSpeak =
        latestNarrative.commentary_by_persona?.[activePersona] ||
        latestNarrative.why_it_matters_explanation;
    }

    if (!textToSpeak) return;

    // Cancel current speech and speak new line
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(textToSpeak);

    // Dynamic pitch/rate based on emotional leverage
    const isHighDrama = (latestNarrative.leverage_index ?? 1.0) >= 3.0;
    utterance.rate = isHighDrama ? 1.15 : useAccessibilityAudio ? 1.0 : 1.05;
    utterance.pitch = isHighDrama ? 1.08 : useAccessibilityAudio ? 0.95 : 1.0;

    // Match appropriate voice for language
    const voices = availableVoices.length > 0 ? availableVoices : window.speechSynthesis.getVoices();
    const matchedVoice =
      voices.find((v) => v.lang.toLowerCase().startsWith(activeLanguage.toLowerCase())) ||
      voices.find((v) => v.lang.startsWith("en"));

    if (matchedVoice) {
      utterance.voice = matchedVoice;
    }

    window.speechSynthesis.speak(utterance);
  }, [
    latestNarrative,
    isPlaying,
    isMuted,
    activePersona,
    activeLanguage,
    useAccessibilityAudio,
    availableVoices,
  ]);

  const togglePlay = () => {
    if (isPlaying) {
      window.speechSynthesis?.cancel();
      setIsPlaying(false);
    } else {
      setIsPlaying(true);
      if (latestNarrative) {
        lastSpokenIdRef.current = null; // force speech on play
      }
    }
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3 shadow-lg flex items-center justify-between gap-3 text-xs backdrop-blur-md">
      {/* Left Status & Visualizer */}
      <div className="flex items-center gap-3">
        <button
          onClick={togglePlay}
          className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${
            isPlaying
              ? "bg-rose-500 hover:bg-rose-600 text-white shadow-lg shadow-rose-500/20"
              : "bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold shadow-lg shadow-emerald-500/20"
          }`}
          title={isPlaying ? "Pause Live Audio" : "Listen to Live AI Audio Commentary"}
        >
          {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
        </button>

        <div className="flex flex-col">
          <div className="flex items-center gap-2">
            <Radio className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
            <span className="font-bold text-slate-200 uppercase tracking-wider text-[11px]">
              AI Neural Radio
            </span>
            <span
              className={`text-[9px] px-1.5 py-0.2 rounded font-semibold uppercase ${
                isPlaying
                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                  : "bg-slate-800 text-slate-500"
              }`}
            >
              {isPlaying ? "Live Air" : "Muted"}
            </span>
          </div>
          <span className="text-[10px] text-slate-400">
            {useAccessibilityAudio
              ? "Spatial Audio Description for Visually Impaired"
              : `Voice: ${activePersona.replace("_", " ").toUpperCase()}`}
          </span>
        </div>
      </div>

      {/* Center Wave Animation */}
      {isPlaying && !isMuted && (
        <div className="hidden sm:flex items-center gap-1 h-5 px-3">
          <span className="w-1 bg-emerald-400 rounded-full animate-pulse h-3" />
          <span className="w-1 bg-emerald-400 rounded-full animate-bounce h-5" />
          <span className="w-1 bg-emerald-400 rounded-full animate-pulse h-2" />
          <span className="w-1 bg-emerald-400 rounded-full animate-bounce h-4" />
          <span className="w-1 bg-emerald-400 rounded-full animate-pulse h-3" />
        </div>
      )}

      {/* Right Controls */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => setUseAccessibilityAudio(!useAccessibilityAudio)}
          className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-semibold transition-colors border ${
            useAccessibilityAudio
              ? "bg-purple-600/30 text-purple-300 border-purple-500/40"
              : "bg-slate-800 hover:bg-slate-700 text-slate-400 border-slate-700"
          }`}
          title="Toggle Audio Description for visually impaired supporters"
        >
          <Headphones className="w-3.5 h-3.5" />
          <span className="hidden md:inline">Accessibility Audio</span>
        </button>

        <button
          onClick={() => setIsMuted(!isMuted)}
          className="p-1.5 rounded-md hover:bg-slate-800 text-slate-400 hover:text-white transition-colors"
          title={isMuted ? "Unmute" : "Mute"}
        >
          {isMuted ? <VolumeX className="w-4 h-4 text-rose-400" /> : <Volume2 className="w-4 h-4" />}
        </button>
      </div>
    </div>
  );
};
