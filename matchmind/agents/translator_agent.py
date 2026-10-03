"""Translator Agent: Stage 5 of the MatchMind Intelligence Pipeline.

Provides sub-second multilingual commentary generation across global languages
(Spanish, Hindi, Arabic, Portuguese, French) preserving domain terms and player names.
"""

from typing import Dict, List, Optional
import httpx
import structlog

from matchmind.agents.base_agent import BaseAgent
from matchmind.config import settings
from matchmind.constants import SUPPORTED_LANGUAGES
from matchmind.models import AgentMessage

logger = structlog.get_logger(__name__)


class SportsLocalizationEngine:
    """Offline sports terminology translation engine with culturally authentic phraseology."""

    VOCABULARY = {
        "es": {
            "GOAAALLL": "¡GOLAÇO TOTAL!",
            "Goal": "Gol",
            "TACTICAL ANALYSIS": "ANÁLISIS TÁCTICO",
            "Big chance": "¡Gran ocasión!",
            "brilliant play": "jugada magistral",
            "progressive ball": "pase progresivo entre líneas",
            "great movement": "gran desplazamiento táctico",
            "Field Tilt": "Inclinación de Campo (Field Tilt)",
            "Audio Description": "Audiodescripción",
        },
        "hi": {
            "GOAAALLL": "शानदार गोल!!",
            "Goal": "गोल",
            "TACTICAL ANALYSIS": "सामरिक विश्लेषण",
            "Big chance": "बड़ा मौका!",
            "brilliant play": "लाजवाब खेल",
            "progressive ball": "प्रगतिशील पास (रक्षात्मक पंक्ति को तोड़ते हुए)",
            "great movement": "शानदार मूवमेंट",
            "Field Tilt": "फील्ड टिल्ट (दबाव)",
            "Audio Description": "ऑडियो विवरण",
        },
        "ar": {
            "GOAAALLL": "هدف عالمي لا يصدق!",
            "Goal": "هدف",
            "TACTICAL ANALYSIS": "تحليل تكتيكي",
            "Big chance": "فرصة خطيرة جداً!",
            "brilliant play": "تمريرة ساحرة وذكية",
            "progressive ball": "تمريرة كاسرة للخطوط الدفاعية",
            "great movement": "تحرك تكتيكي ممتاز",
            "Field Tilt": "الاستحواذ الهجومي",
            "Audio Description": "الوصف الصوتي للمكفوفين",
        },
        "pt": {
            "GOAAALLL": "GOLAÇO ESPETACULAR!",
            "Goal": "Gol",
            "TACTICAL ANALYSIS": "ANÁLISE TÁTICA",
            "Big chance": "Grande oportunidade!",
            "brilliant play": "jogada genial",
            "progressive ball": "passe vertical que quebra linhas",
            "great movement": "ótima movimentação tática",
            "Field Tilt": "Pressão Territorial (Field Tilt)",
            "Audio Description": "Audiodescrição",
        },
        "fr": {
            "GOAAALLL": "QUEL BUT MAGNIFIQUE!",
            "Goal": "But",
            "TACTICAL ANALYSIS": "ANALYSE TACTIQUE",
            "Big chance": "Grosse occasion de but!",
            "brilliant play": "action collective remarquable",
            "progressive ball": "passe vers l'avant cassant les lignes",
            "great movement": "excellent déplacement tactique",
            "Field Tilt": "Domination Territoriale",
            "Audio Description": "Audiodescription",
        },
    }

    @classmethod
    def translate_phrase(cls, text: str, target_lang: str) -> str:
        """Rule-based domain localization that preserves English metrics and player names."""
        mapping = cls.VOCABULARY.get(target_lang, {})
        translated = text
        for en_phrase, target_phrase in mapping.items():
            translated = translated.replace(en_phrase, target_phrase)
        return translated


class TranslatorAgent(BaseAgent):
    """Generates real-time multilingual commentary feeds for global supporters."""

    def __init__(self):
        super().__init__(
            agent_id="translator_agent",
            role_name="Real-Time Multilingual Localization Specialist",
            supported_message_types=["PERSONA_COMMENTARY"],
        )
        self.target_languages = ["es", "hi", "ar", "pt", "fr"]

    async def _translate_with_azure(self, text: str, target_lang: str) -> Optional[str]:
        """Call Azure AI Translator API if configured."""
        if not settings.azure_translator_key or not settings.azure_translator_endpoint:
            return None

        try:
            url = f"{settings.azure_translator_endpoint.rstrip('/')}/translate"
            params = {"api-version": "3.0", "to": target_lang}
            headers = {
                "Ocp-Apim-Subscription-Key": settings.azure_translator_key,
                "Ocp-Apim-Subscription-Region": settings.azure_translator_region,
                "Content-Type": "application/json",
            }
            body = [{"text": text}]
            async with httpx.AsyncClient(timeout=1.5) as client:
                res = await client.post(url, params=params, headers=headers, json=body)
                if res.status_code == 200:
                    data = res.json()
                    return data[0]["translations"][0]["text"]
        except Exception as exc:
            self.log.warning("Azure Translator failed, falling back to local engine", error=str(exc))
        return None

    async def process(self, message: AgentMessage) -> List[AgentMessage]:
        payload = message.payload
        narrative_dict = payload.get("narrative", {})
        commentary_map = narrative_dict.get("commentary_by_persona", {})
        primary_text = commentary_map.get("casual_fan") or commentary_map.get("broadcast_commentator") or ""

        translations: Dict[str, str] = {"en": primary_text}

        for lang in self.target_languages:
            azure_translated = await self._translate_with_azure(primary_text, lang)
            if azure_translated:
                translations[lang] = azure_translated
            else:
                translations[lang] = SportsLocalizationEngine.translate_phrase(primary_text, lang)

        narrative_dict["translations"] = translations

        out_message = AgentMessage(
            source_agent=self.agent_id,
            target_agents=["factcheck_agent"],
            match_id=message.match_id,
            event_index=message.event_index,
            match_minute=message.match_minute,
            message_type="TRANSLATED_COMMENTARY",
            payload={
                "narrative": narrative_dict,
                "event": payload.get("event"),
                "metric_state": payload.get("metric_state"),
            },
            metadata=message.metadata,
        )

        return [out_message]
