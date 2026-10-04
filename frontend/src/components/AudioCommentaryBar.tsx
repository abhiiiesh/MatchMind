import React, { useState, useEffect, useRef } from "react";
import type { LanguageCode, NarrativeOutput, PersonaType } from "../types";
import { Volume2, VolumeX, Play, Pause, Radio, Headphones, Sparkles, Code2, X } from "lucide-react";
import { apiUrl } from "../api";

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
  const [useAzureEngine, setUseAzureEngine] = useState(true);
  const [activeVoiceName, setActiveVoiceName] = useState("en-GB-RyanNeural");
  const [currentSSML, setCurrentSSML] = useState<string | null>(null);
  const [showSSMLModal, setShowSSMLModal] = useState(false);
  const [availableVoices, setAvailableVoices] = useState<SpeechSynthesisVoice[]>([]);

  const lastSpokenIdRef = useRef<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // 1. Load browser voices for native fallback
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

  // 2. Synthesize & play speech on new narrative arrival
  useEffect(() => {
    if (!isPlaying || isMuted || !latestNarrative) return;

    const speechKey = `${latestNarrative.narrative_id}-${activePersona}-${activeLanguage}-${useAccessibilityAudio}-${useAzureEngine}`;
    if (speechKey === lastSpokenIdRef.current) return;
    lastSpokenIdRef.current = speechKey;

    // Pick text based on language and persona
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

    if (useAzureEngine) {
      // Call Azure Neural Speech Backend
      fetch(apiUrl("/api/speech/synthesize"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: textToSpeak,
          persona: useAccessibilityAudio ? "accessibility_audio" : activePersona,
          lang: activeLanguage,
          leverage_index: latestNarrative.leverage_index ?? 1.0,
          outcome: "Success",
        }),
      })
        .then((res) => (res.ok ? res.json() : null))
        .then((data) => {
          if (data) {
            setActiveVoiceName(data.voice_name || "en-GB-RyanNeural");
            setCurrentSSML(data.ssml || null);

            // Play via HTML5 Audio element
            if (audioRef.current && data.audio_url) {
              audioRef.current.src = apiUrl(data.audio_url);
              audioRef.current.play().catch(() => {
                // Autoplay may be restricted in some browsers
              });
            }
          }
        })
        .catch(() => {
          // Fallback to browser voice on error
          speakWithBrowser(textToSpeak);
        });
    } else {
      // Browser Speech API
      speakWithBrowser(textToSpeak);
    }
  }, [
    latestNarrative,
    isPlaying,
    isMuted,
    activePersona,
    activeLanguage,
    useAccessibilityAudio,
    useAzureEngine,
  ]);

  const speakWithBrowser = (text: string) => {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);

    const isHighDrama = (latestNarrative?.leverage_index ?? 1.0) >= 3.0;
    utterance.rate = isHighDrama ? 1.15 : useAccessibilityAudio ? 1.0 : 1.05;
    utterance.pitch = isHighDrama ? 1.08 : useAccessibilityAudio ? 0.95 : 1.0;

    const voices = availableVoices.length > 0 ? availableVoices : window.speechSynthesis.getVoices();
    const matchedVoice =
      voices.find((v) => v.lang.toLowerCase().startsWith(activeLanguage.toLowerCase())) ||
      voices.find((v) => v.lang.startsWith("en"));

    if (matchedVoice) {
      utterance.voice = matchedVoice;
      setActiveVoiceName(matchedVoice.name);
    }

    window.speechSynthesis.speak(utterance);
  };

  const togglePlay = () => {
    if (isPlaying) {
      if (audioRef.current) audioRef.current.pause();
      window.speechSynthesis?.cancel();
      setIsPlaying(false);
    } else {
      setIsPlaying(true);
      lastSpokenIdRef.current = null; // force speech on play
    }
  };

  return (
    <>
      {/* Hidden audio element for streaming server-generated speech */}
      <audio ref={audioRef} />

      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3 shadow-lg flex items-center justify-between gap-3 text-xs backdrop-blur-md relative">
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

              {/* Neural Badge */}
              <button
                onClick={() => setUseAzureEngine(!useAzureEngine)}
                className={`flex items-center gap-1 text-[9px] px-1.5 py-0.2 rounded font-mono font-bold transition-colors ${
                  useAzureEngine
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                    : "bg-slate-800 text-slate-400"
                }`}
                title="Toggle between Azure Neural TTS and Browser WebSpeech"
              >
                <Sparkles className="w-2.5 h-2.5 text-cyan-400" />
                <span>{useAzureEngine ? "Azure Neural" : "Browser TTS"}</span>
              </button>
            </div>

            <div className="flex items-center gap-2 text-[10px] text-slate-400 mt-0.5">
              <span>
                {useAccessibilityAudio
                  ? "Spatial Audio Description (Accessible)"
                  : `Voice: ${activeVoiceName}`}
              </span>
              {latestNarrative && (
                <button
                  onClick={async () => {
                    if (!currentSSML) {
                      const text =
                        latestNarrative.commentary_by_persona?.[activePersona] ||
                        latestNarrative.why_it_matters_explanation;
                      try {
                        const res = await fetch("http://localhost:8000/api/speech/synthesize", {
                          method: "POST",
                          headers: { "Content-Type": "application/json" },
                          body: JSON.stringify({
                            text,
                            persona: useAccessibilityAudio ? "accessibility_audio" : activePersona,
                            lang: activeLanguage,
                            leverage_index: latestNarrative.leverage_index ?? 1.0,
                            outcome: "Success",
                          }),
                        });
                        const data = await res.json();
                        setCurrentSSML(data.ssml || null);
                      } catch {
                        // ignore
                      }
                    }
                    setShowSSMLModal(true);
                  }}
                  className="text-cyan-400 hover:text-cyan-300 flex items-center gap-0.5 underline text-[10px]"
                  title="View Microsoft SSML markup"
                >
                  <Code2 className="w-2.5 h-2.5" />
                  <span>SSML</span>
                </button>
              )}
            </div>
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
            className={`flex items-center gap-1 px-2 py-1 rounded-md text-[11px] font-semibold transition-colors border ${
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

      {/* SSML Inspection Modal */}
      {showSSMLModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-2xl w-full p-5 shadow-2xl relative">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
              <div className="flex items-center gap-2">
                <Code2 className="w-5 h-5 text-cyan-400" />
                <h3 className="text-sm font-bold text-white">Azure Speech Synthesis Markup (SSML)</h3>
              </div>
              <button
                onClick={() => setShowSSMLModal(false)}
                className="text-slate-400 hover:text-white p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            {currentSSML ? (
              <pre className="bg-slate-950 p-3 rounded-lg text-xs font-mono text-cyan-300 overflow-x-auto whitespace-pre-wrap leading-relaxed max-h-96">
                {currentSSML}
              </pre>
            ) : (
              <div className="py-8 text-center text-slate-400 text-xs italic">
                Generating Azure Neural SSML markup...
              </div>
            )}
            <div className="mt-3 text-right">
              <button
                onClick={() => setShowSSMLModal(false)}
                className="px-3 py-1 bg-slate-800 hover:bg-slate-700 text-white rounded text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
