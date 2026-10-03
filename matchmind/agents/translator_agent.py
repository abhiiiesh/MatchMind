"""Translator Agent: Stage 5 of the MatchMind Intelligence Pipeline.

Provides sub-second multilingual commentary generation across global languages
(Spanish, Hindi, Arabic, Portuguese, French) preserving domain terms and player names.
"""

from typing import Dict, List, Optional
import httpx
import structlog

from matchmind.agents.base_agent import BaseAgent
from matchmind.config import settings
from matchmind.constants import SUPPORTED_LANGUAGES, FanPersona
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
            "Routine possession maintenance by": "Mantenimiento táctico de la posesión por",
            "Sustaining tempo as": "Sosteniendo el ritmo mientras",
            "control possession rhythm": "controla los tiempos del encuentro",
            "Current score stands at": "El marcador se sitúa en",
            "executes action in the opponent's half": "ejecuta maniobra en el último tercio",
            "Historical Context:": "Contexto Histórico:",
            "Rivalry Context:": "Contexto de Rivalidad:",
            "penetrated multiple defensive layers": "superó múltiples líneas de contención rivales",
            "This line-breaking pass bypasses the opponent's pressing trap": "Este pase entre líneas elude la trampa de presión rival",
            "and directly shifts play into the final third": "y traslada directamente el ataque a la zona de peligro",
            "with great movement for": "con gran desplazamiento para",
            "in the": "en el",
            "th minute": "º minuto",
            "What a moment for": "¡Qué momento inolvidable para la hinchada de",
            "fans!": "!",
            "The crowd is on their feet!": "¡El estadio entero se pone de pie!",
            "Can you believe how close that was": "¿Pueden creer lo cerca que estuvo",
            "Beautiful pass that opens up the whole defense!": "¡Pase quirúrgico que desarma toda la estructura defensiva!",
        },
        "hi": {
            "GOAAALLL": "शानदार गोल!!",
            "Goal": "गोल",
            "TACTICAL ANALYSIS": "सामरिक विश्लेषण",
            "Big chance": "बड़ा गोल का मौका!",
            "brilliant play": "लाजवाब खेल कौशल",
            "progressive ball": "प्रगतिशील पास (रक्षा पंक्ति को भेदते हुए)",
            "great movement": "शानदार सामरिक मूवमेंट",
            "Field Tilt": "फील्ड टिल्ट (आक्रामक दबाव)",
            "Audio Description": "ऑडियो विवरण (नेत्रहीनों के लिए)",
            "Routine possession maintenance by": "गेंद पर रणनीतिक नियंत्रण बनाए रखते हुए",
            "Sustaining tempo as": "खेल की गति को बरकरार रखते हुए",
            "control possession rhythm": "मैच की लय को पूरी तरह नियंत्रित कर रहे हैं",
            "Current score stands at": "वर्तमान स्कोर है",
            "executes action in the opponent's half": "विरोधी के रक्षात्मक क्षेत्र में आक्रामक चाल",
            "Historical Context:": "ऐतिहासिक रिकॉर्ड:",
            "Rivalry Context:": "पारस्परिक प्रतिद्वंद्विता:",
            "penetrated multiple defensive layers": "विरोधी रक्षा पंक्ति को पूरी तरह भेद दिया",
            "This line-breaking pass bypasses the opponent's pressing trap": "यह लाइन-ब्रेकिंग पास विरोधी के हाई-प्रेस जाल को चकमा देता है",
            "and directly shifts play into the final third": "और हमले को सीधे अंतिम तीसरे क्षेत्र में धकेल देता है",
            "with great movement for": "द्वारा शानदार मूवमेंट",
            "in the": "में",
            "th minute": "वें मिनट में",
            "What a moment for": "समर्थकों के लिए क्या ऐतिहासिक क्षण है!",
            "fans!": "!",
            "The crowd is on their feet!": "दर्शकों में जबरदस्त उत्साह!",
            "Can you believe how close that was": "विश्वास नहीं होता यह कितना करीबी मौका था",
            "Beautiful pass that opens up the whole defense!": "लाजवाब पास जिसने विरोधी रक्षा को बिखेर कर रख दिया!",
        },
        "ar": {
            "GOAAALLL": "هدف عالمي لا يصدق!",
            "Goal": "هدف",
            "TACTICAL ANALYSIS": "تحليل تكتيكي معمق",
            "Big chance": "فرصة محققة للتهديف!",
            "brilliant play": "تمريرة ساحرة وذكية",
            "progressive ball": "تمريرة كاسرة للخطوط الدفاعية",
            "great movement": "تحرك تكتيكي استثنائي",
            "Field Tilt": "الاستحواذ الهجومي الفعال",
            "Audio Description": "الوصف الصوتي التفاعلي",
            "Routine possession maintenance by": "تدوير منظم واستحواذ ذكي على الكرة بواسطة",
            "Sustaining tempo as": "الحفاظ على إيقاع اللعب الهادئ بينما",
            "control possession rhythm": "يفرض سيطرته التامة على نسق المواجهة",
            "Current score stands at": "النتيجة الحالية حتى اللحظة",
            "executes action in the opponent's half": "يقود هجمة متقدمة في نصف ملعب الخصم",
            "Historical Context:": "السجل التاريخي:",
            "Rivalry Context:": "تاريخ ديربي الفريقين:",
            "penetrated multiple defensive layers": "اخترقت المنظومة الدفاعية بكل إحكام",
            "This line-breaking pass bypasses the opponent's pressing trap": "هذه التمريرة الذكية تضرب مصيدة الضغط العالي مباشرة",
            "and directly shifts play into the final third": "وتنقل الكرة ببراعة إلى الثلث الهجومي الأخير",
            "with great movement for": "بتحرك تكتيكي رائع لصالح",
            "What a moment for": "يا لها من لحظة جنونية لعشاق",
            "fans!": "!",
            "The crowd is on their feet!": "الجماهير تهتف بحرارة في المدرجات!",
            "Can you believe how close that was": "فرصة لا تصدق كادت تعانق الشباك",
            "Beautiful pass that opens up the whole defense!": "تمريرة حريرية مميزة تكشف خطوط الدفاع بالكامل!",
        },
        "pt": {
            "GOAAALLL": "GOLAÇO ESPETACULAR!",
            "Goal": "Gol",
            "TACTICAL ANALYSIS": "ANÁLISE TÁTICA",
            "Big chance": "Grande oportunidade de gol!",
            "brilliant play": "jogada genial e criativa",
            "progressive ball": "passe vertical que quebra linhas",
            "great movement": "ótima movimentação tática",
            "Field Tilt": "Pressão Territorial (Field Tilt)",
            "Audio Description": "Audiodescrição Acessível",
            "Routine possession maintenance by": "Manutenção estratégica da posse de bola por",
            "Sustaining tempo as": "Cadenciando o ritmo enquanto",
            "control possession rhythm": "controla os tempos do jogo",
            "Current score stands at": "O placar no momento é",
            "executes action in the opponent's half": "constrói jogada ofensiva no campo adversário",
            "Historical Context:": "Contexto Histórico:",
            "Rivalry Context:": "Histórico do Confronto:",
            "penetrated multiple defensive layers": "rompeu múltiplas linhas defensivas",
            "This line-breaking pass bypasses the opponent's pressing trap": "Este passe entre linhas supera o bloco de pressão rival",
            "and directly shifts play into the final third": "e aciona diretamente os atacantes no terço final",
            "with great movement for": "com excelente movimentação para",
            "What a moment for": "Que explosão de alegria para a torcida do",
            "fans!": "!",
        },
        "fr": {
            "GOAAALLL": "QUEL BUT MAGNIFIQUE!",
            "Goal": "But",
            "TACTICAL ANALYSIS": "ANALYSE TACTIQUE",
            "Big chance": "Énorme occasion de but!",
            "brilliant play": "action collective de grande classe",
            "progressive ball": "passe vers l'avant cassant les lignes",
            "great movement": "excellent déplacement tactique",
            "Field Tilt": "Domination Territoriale",
            "Audio Description": "Audiodescription",
            "Routine possession maintenance by": "Conservation méthodique du ballon par",
            "Sustaining tempo as": "Gestion du tempo pendant que",
            "control possession rhythm": "dicte le rythme de la rencontre",
            "Current score stands at": "Le score est actuellement de",
            "executes action in the opponent's half": "mène l'action dans les 30 derniers mètres",
            "Historical Context:": "Contexte Historique :",
            "Rivalry Context:": "Historique des Confrontations :",
            "penetrated multiple defensive layers": "a transpercé l'ensemble du rideau défensif",
            "This line-breaking pass bypasses the opponent's pressing trap": "Cette passe tranchante transperce le premier rideau de pressing",
            "and directly shifts play into the final third": "et projette le bloc offensif dans la surface de vérité",
            "with great movement for": "avec un superbe appel de balle pour",
            "What a moment for": "Quel moment d'extase pour les supporters de",
            "fans!": "!",
        },
    }

    @classmethod
    def translate_phrase(cls, text: str, target_lang: str) -> str:
        """Rule-based domain localization that preserves English metrics and player names."""
        mapping = cls.VOCABULARY.get(target_lang, {})
        translated = text
        for en_phrase, target_phrase in sorted(mapping.items(), key=lambda x: len(x[0]), reverse=True):
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
        primary_text = (
            commentary_map.get(FanPersona.CASUAL_FAN)
            or commentary_map.get("casual_fan")
            or commentary_map.get(FanPersona.BROADCAST_COMMENTATOR)
            or commentary_map.get("broadcast_commentator")
            or commentary_map.get(FanPersona.TACTICAL_ANALYST)
            or commentary_map.get("tactical_analyst")
            or ""
        )


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
