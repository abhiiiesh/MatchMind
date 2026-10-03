"""Speech Synthesis Service for MatchMind.

Orchestrates Azure AI Speech Cognitive Services REST integration,
SSML construction, disk/memory caching, and fallback synthetic audio generation.
"""

import hashlib
import math
from pathlib import Path
import structlog
import wave
from typing import Any, Dict, Optional
import httpx

from matchmind.config import settings
from matchmind.speech.ssml_builder import SSMLBuilder

logger = structlog.get_logger(__name__)


class SpeechService:
    """Manages text-to-speech synthesis with Azure Cognitive Services and offline fallback."""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or (settings.cache_dir / "speech")
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(
        self,
        text: str,
        persona: str,
        lang: str,
        leverage_index: float,
        outcome: str,
    ) -> str:
        """Computes deterministic cache hash."""
        raw = f"{text}|{persona}|{lang}|{leverage_index:.1f}|{outcome}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def _generate_synthetic_tone(self, target_path: Path, is_goal: bool = False) -> None:
        """Generates a pleasant melodic announcement chime WAV file when offline."""
        sample_rate = 22050
        duration = 1.2 if not is_goal else 2.0
        num_samples = int(sample_rate * duration)

        # Melodic chords: A Major chord (440Hz, 554.37Hz, 659.25Hz) or Goal fanfare
        frequencies = [440.0, 554.37, 659.25, 880.0] if is_goal else [523.25, 659.25, 783.99]

        with wave.open(str(target_path), "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)

            data = bytearray()
            for i in range(num_samples):
                t = i / sample_rate
                # Decay envelope
                envelope = math.exp(-2.5 * (t / duration))
                sample_val = 0.0
                for f in frequencies:
                    sample_val += math.sin(2.0 * math.pi * f * t)
                sample_val = (sample_val / len(frequencies)) * envelope
                # Clip to 16-bit PCM
                int_val = int(sample_val * 32767.0 * 0.7)
                int_val = max(-32768, min(32767, int_val))
                data.extend(int_val.to_bytes(2, byteorder="little", signed=True))

            wav_file.writeframes(data)

    async def synthesize(
        self,
        text: str,
        persona: str = "casual_fan",
        lang: str = "en",
        leverage_index: float = 1.0,
        outcome: str = "Success",
        speaking_rate: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Synthesizes commentary text into neural speech via Azure or fallback."""
        cache_id = self._get_cache_key(text, persona, lang, leverage_index, outcome)
        mp3_path = self.cache_dir / f"{cache_id}.mp3"
        wav_path = self.cache_dir / f"{cache_id}.wav"

        voice_name = SSMLBuilder.get_voice_name(persona, lang)
        ssml = SSMLBuilder.build_ssml(
            text=text,
            persona=persona,
            lang=lang,
            leverage_index=leverage_index,
            outcome=outcome,
            speaking_rate_override=speaking_rate,
        )

        # 1. Check existing cache
        if mp3_path.exists():
            return {
                "audio_id": cache_id,
                "audio_url": f"/api/speech/audio/{cache_id}",
                "format": "mp3",
                "voice_name": voice_name,
                "is_neural_azure": True,
                "ssml": ssml,
                "cached": True,
            }
        if wav_path.exists():
            return {
                "audio_id": cache_id,
                "audio_url": f"/api/speech/audio/{cache_id}",
                "format": "wav",
                "voice_name": voice_name,
                "is_neural_azure": False,
                "ssml": ssml,
                "cached": True,
            }

        # 2. Azure Cognitive Services Speech REST call
        if settings.has_azure_speech:
            endpoint = f"https://{settings.azure_speech_region}.tts.speech.microsoft.com/cognitiveservices/v1"
            headers = {
                "Ocp-Apim-Subscription-Key": settings.azure_speech_key,
                "Content-Type": "application/ssml+xml",
                "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
                "User-Agent": "MatchMindIntelligenceEngine",
            }

            try:
                async with httpx.AsyncClient(timeout=4.0) as client:
                    response = await client.post(endpoint, headers=headers, content=ssml.encode("utf-8"))
                    if response.status_code == 200:
                        with open(mp3_path, "wb") as f:
                            f.write(response.content)
                        logger.info("Successfully synthesized neural audio via Azure Speech", voice=voice_name, bytes=len(response.content))
                        return {
                            "audio_id": cache_id,
                            "audio_url": f"/api/speech/audio/{cache_id}",
                            "format": "mp3",
                            "voice_name": voice_name,
                            "is_neural_azure": True,
                            "ssml": ssml,
                            "cached": False,
                        }
                    else:
                        logger.warning("Azure Speech API responded with error", status=response.status_code, body=response.text[:200])
            except Exception as exc:
                logger.warning("Azure Speech network call failed, switching to fallback", error=str(exc))

        # 3. High-fidelity Offline Tone Fallback
        is_goal = outcome.lower() == "goal" or "GOAAALLL" in text or "¡GOLAÇO" in text
        self._generate_synthetic_tone(wav_path, is_goal=is_goal)

        return {
            "audio_id": cache_id,
            "audio_url": f"/api/speech/audio/{cache_id}",
            "format": "wav",
            "voice_name": voice_name,
            "is_neural_azure": False,
            "ssml": ssml,
            "cached": False,
            "offline_notice": "Generated SSML ready for Azure Speech. Using local audio broadcast tone.",
        }

    def get_audio_file(self, audio_id: str) -> Optional[Path]:
        """Returns the cached audio file path if present."""
        mp3_path = self.cache_dir / f"{audio_id}.mp3"
        if mp3_path.exists():
            return mp3_path
        wav_path = self.cache_dir / f"{audio_id}.wav"
        if wav_path.exists():
            return wav_path
        return None


speech_service = SpeechService()
