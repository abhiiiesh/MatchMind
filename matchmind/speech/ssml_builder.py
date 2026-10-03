"""Dynamic SSML Builder for Azure AI Speech Neural Audio Synthesis.

Tailors voice selection, pitch, rate, emotional inflection, and pauses
based on viewer persona, language, and real-time match leverage.
"""

import html
from typing import Optional
from matchmind.constants import FanPersona


class SSMLBuilder:
    """Builds valid W3C/Microsoft SSML with mstts expressive extensions."""

    # Azure AI Neural Voice Registry
    VOICE_REGISTRY = {
        "en": {
            FanPersona.CASUAL_FAN: "en-GB-AlfieNeural",
            FanPersona.TACTICAL_ANALYST: "en-GB-RyanNeural",
            FanPersona.BROADCAST_COMMENTATOR: "en-GB-OliverNeural",
            FanPersona.ACCESSIBILITY_AUDIO: "en-GB-SoniaNeural",
            "default": "en-GB-RyanNeural",
        },
        "es": {
            FanPersona.CASUAL_FAN: "es-ES-AlvaroNeural",
            FanPersona.TACTICAL_ANALYST: "es-ES-ElviraNeural",
            FanPersona.BROADCAST_COMMENTATOR: "es-ES-AlvaroNeural",
            FanPersona.ACCESSIBILITY_AUDIO: "es-ES-ElviraNeural",
            "default": "es-ES-AlvaroNeural",
        },
        "hi": {
            FanPersona.CASUAL_FAN: "hi-IN-MadhurNeural",
            FanPersona.TACTICAL_ANALYST: "hi-IN-SwaraNeural",
            FanPersona.BROADCAST_COMMENTATOR: "hi-IN-MadhurNeural",
            FanPersona.ACCESSIBILITY_AUDIO: "hi-IN-SwaraNeural",
            "default": "hi-IN-MadhurNeural",
        },
        "ar": {
            FanPersona.CASUAL_FAN: "ar-SA-HamedNeural",
            FanPersona.TACTICAL_ANALYST: "ar-SA-ZariyahNeural",
            FanPersona.BROADCAST_COMMENTATOR: "ar-SA-HamedNeural",
            FanPersona.ACCESSIBILITY_AUDIO: "ar-SA-ZariyahNeural",
            "default": "ar-SA-HamedNeural",
        },
        "fr": {
            FanPersona.CASUAL_FAN: "fr-FR-HenriNeural",
            FanPersona.TACTICAL_ANALYST: "fr-FR-DeniseNeural",
            FanPersona.BROADCAST_COMMENTATOR: "fr-FR-HenriNeural",
            FanPersona.ACCESSIBILITY_AUDIO: "fr-FR-DeniseNeural",
            "default": "fr-FR-HenriNeural",
        },
        "pt": {
            FanPersona.CASUAL_FAN: "pt-BR-AntonioNeural",
            FanPersona.TACTICAL_ANALYST: "pt-BR-FranciscaNeural",
            FanPersona.BROADCAST_COMMENTATOR: "pt-BR-AntonioNeural",
            FanPersona.ACCESSIBILITY_AUDIO: "pt-BR-FranciscaNeural",
            "default": "pt-BR-AntonioNeural",
        },
    }

    # Locale mappings for xml:lang
    LOCALE_MAP = {
        "en": "en-GB",
        "es": "es-ES",
        "hi": "hi-IN",
        "ar": "ar-SA",
        "fr": "fr-FR",
        "pt": "pt-BR",
    }

    @classmethod
    def get_voice_name(cls, persona: str, lang: str = "en") -> str:
        """Resolves the most appropriate Azure neural voice."""
        lang_group = cls.VOICE_REGISTRY.get(lang.lower(), cls.VOICE_REGISTRY["en"])
        try:
            enum_persona = FanPersona(persona)
            return lang_group.get(enum_persona, lang_group["default"])
        except ValueError:
            for k, v in lang_group.items():
                if isinstance(k, FanPersona) and k.value == persona:
                    return v
            return lang_group["default"]

    @classmethod
    def build_ssml(
        cls,
        text: str,
        persona: str = "casual_fan",
        lang: str = "en",
        leverage_index: float = 1.0,
        outcome: str = "Success",
        speaking_rate_override: Optional[float] = None,
    ) -> str:
        """Constructs rich SSML string with emotional inflection and pauses."""
        clean_lang = lang.lower()
        xml_locale = cls.LOCALE_MAP.get(clean_lang, "en-GB")
        voice_name = cls.get_voice_name(persona, clean_lang)

        # 1. Determine prosody parameters based on drama & persona
        is_goal = outcome.lower() == "goal" or "GOAAALLL" in text or "¡GOLAÇO" in text or "गोल" in text
        is_high_drama = leverage_index >= 3.0 or is_goal
        is_accessibility = (
            persona == FanPersona.ACCESSIBILITY_AUDIO
            or persona == "accessibility_audio"
        )
        is_tactical = (
            persona == FanPersona.TACTICAL_ANALYST
            or persona == "tactical_analyst"
        )

        if is_goal:
            rate = "+16%"
            pitch = "+18%"
            volume = "+25%"
            style = "excited"
        elif is_high_drama:
            rate = "+10%"
            pitch = "+10%"
            volume = "+15%"
            style = "excited"
        elif is_accessibility:
            rate = "-5%"
            pitch = "0%"
            volume = "+5%"
            style = "narration-relaxed"
        elif is_tactical:
            rate = "+4%"
            pitch = "-2%"
            volume = "0%"
            style = "chat"
        else:
            rate = "+2%"
            pitch = "+2%"
            volume = "0%"
            style = "cheerful"

        if speaking_rate_override is not None:
            pct = int((speaking_rate_override - 1.0) * 100)
            rate = f"{'+' if pct >= 0 else ''}{pct}%"

        # 2. Sanitize and format text content
        escaped_text = html.escape(text.strip())

        # For accessibility audio, insert distinct micro-pauses after full stops
        if is_accessibility:
            escaped_text = escaped_text.replace(". ", '. <break time="220ms"/> ')
            escaped_text = escaped_text.replace("! ", '! <break time="250ms"/> ')
            escaped_text = escaped_text.replace(" | ", ' <break time="300ms"/> ')

        # Emphasize goals
        if is_goal:
            for goal_token in ["GOAAALLL!!", "¡GOLAÇO TOTAL!", "शानदार गोल!!", "هدف عالمي"]:
                escaped_goal = html.escape(goal_token)
                if escaped_goal in escaped_text:
                    escaped_text = escaped_text.replace(
                        escaped_goal,
                        f'<emphasis level="strong">{escaped_goal}</emphasis>',
                    )

        # 3. Assemble full SSML XML document
        ssml = (
            f"<speak version='1.0' "
            f"xmlns='http://www.w3.org/2001/10/synthesis' "
            f"xmlns:mstts='https://www.w3.org/2001/mstts' "
            f"xml:lang='{xml_locale}'>\n"
            f"  <voice name='{voice_name}'>\n"
            f"    <mstts:express-as style='{style}'>\n"
            f"      <prosody rate='{rate}' pitch='{pitch}' volume='{volume}'>\n"
            f"        {escaped_text}\n"
            f"      </prosody>\n"
            f"    </mstts:express-as>\n"
            f"  </voice>\n"
            f"</speak>"
        )

        return ssml
