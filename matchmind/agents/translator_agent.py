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
            "Brilliant save! The keeper denies": "¡Parada colosal! El arquero le niega el gol a",
            "Heart in mouth moment for": "¡Momento de máxima tensión para la afición de",
            "supporters!": "!",
            "Massive block!": "¡Bloqueo heroico!",
            "shoots but it's charged down at": "remató pero la defensa interceptó con todo al minuto",
            "Off target from": "Disparo desviado de",
            "Had time to pick a spot at": "Tenía espacio para definir al minuto",
            "converted a high-probability opportunity": "convirtió una ocasión de alta probabilidad",
            "forced a crucial save from the goalkeeper": "exigió una estirada providencial del guardameta",
            "had the shot blocked by the retreating defensive line": "vio su disparo bloqueado por la zaga replegada",
            "attempted a strike": "probó un potente remate",
            "but fired off target": "pero el balón se marchó desviado",
            "rattled the woodwork": "¡hizo temblar el poste rival!",
            "A backward recycling pass under tactical pressure": "Pase de seguridad hacia atrás ante la presión rival",
            "High-intensity defensive intervention by": "Intervención defensiva de alta intensidad por",
            "Part of a coordinated counter-press": "Parte de una presión tras pérdida coordinada",
            "Defensive containment by": "Contención defensiva estructurada por",
            "AND IT'S IN!": "¡Y VA PARA ADENTRO!",
            "breaks through in the": "rompe el cerrojo defensivo en el",
            "A seismic goal that makes it": "Un gol de época que coloca el marcador",
            "Terrific stop! The goalkeeper gets down well to turn aside": "¡Paradón de reflejos! El arquero desvía el remate de",
            "Charged down!": "¡Tiro bloqueado en el área!",
            "High and wide!": "¡Por encima del larguero!",
            "Tactical phase at minute": "Fase táctica en el minuto",
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
            "into the match:": "del partido:",
            "threads it forward for": "conduce hacia adelante para",
            "Patience and purpose in their build-up play.": "Paciencia y precisión en la construcción del juego.",
            "Action taking place in the attacking half.": "Acción en campo rival.",
            "scores a goal": "marca un gol",
            "Minute ": "Minuto ",
            "Chance taken by": "Ocasión generada por",
            "Struck with conviction in the": "Remató con convicción en el",
            "testing the defense as": "poniendo a prueba a la defensa rival mientras",
            "ramp up the pressure.": "intensifica el asedio ofensivo.",
            "lets fly in the": "prueba el disparo en el",
            "but the defender throws their body on the line.": "pero la defensa intercepta con heroísmo.",
            "opens up the angle in the": "se genera el ángulo en el",
            "but can't keep the effort down.": "pero no logra darle dirección a la portería.",
            "An ambitious effort that failed to trouble the goalkeeper.": "Un disparo ambicioso que no inquietó al guardameta.",
            "The defensive block closed down the shooting lane in the nick of time.": "El bloque defensivo cerró la línea de disparo justo a tiempo.",
            "An extraordinary low-probability finish": "¡Una definición colosal de mínima probabilidad!",
            "under heavy defensive pressure from an acute angle, beating the goalkeeper's post-shot positioning through sheer individual technique.": "bajo intensa presión defensiva desde un ángulo muy cerrado, batiendo al portero por pura jerarquía individual.",
            "created by breaking the central defensive line. The opposing center-backs were dragged out of shape, presenting a clinical finish rarely conceded in Premier League fixtures.": "generada tras romper la línea defensiva central. Los centrales quedaron desajustados, culminando con una definición impecable.",
            "Generated during sustained pressure": "Generada durante una fase de asedio continuo",
            "testing the keeper's reflexes.": "exigiendo los reflejos del portero.",
            "took the shot with an expected goal value of": "probó el remate con un valor de expected goals de",
            "With the opponent maintaining an aggressive PPDA of": "Con el rival ejerciendo una agresiva presión PPDA de",
            "reset possession to evade a midfield turnover trap.": "retrasó la posesión para desactivar la trampa de pérdida en la medular.",
            "specifically intended to choke transition lanes and force an immediate turnover.": "diseñada específicamente para bloquear líneas de pase y forzar una recuperación inmediata.",
            "Resetting the defensive shape to restrict half-space penetration.": "Reajustando el bloque defensivo para taponar los carriles interiores.",
            "organizing their shape with leverage index at": "organizando su bloque táctico con un índice de leverage de",
            "Absolute chaos at": "¡Locura total al minuto",
            "Scoreline shifts to": "El marcador cambia a",
            "scores!": "¡marca el gol!",
            "scores": "anota",
            # Curated Key Moment Highlights & Replay Commentary
            "Devastating Chelsea break: Palmer feeds Jackson, who squares to Sterling to cut inside Walker and curl in.": "¡Devastador contragolpe del Chelsea! Palmer conecta con Jackson, quien asiste a Sterling para recortar ante Walker y definir con una rosca impecable.",
            "De Bruyne delivers a pinpoint whipped cross, but Haaland's bullet header veers inches wide.": "De Bruyne envía un centro medido con rosca letal, pero el cabezazo de Haaland se marcha desviado por milímetros.",
            "A deflected block falls kindly to Rodri at the D, unleashing an unstoppable venomous left-foot rocket.": "Un rechace defensivo le cae a Rodri en la media luna, soltando un zurdazo imparable y venenoso que revienta la red.",
            "Saka reacts quickest to slot home after Havertz's shot is parried by Alisson.": "Saka reacciona con máxima rapidez para mandar el balón a la red tras el rechace de Alisson al tiro de Havertz.",
            "Chaotic miscommunication in the Arsenal box under pressure results in a Gabriel own goal.": "Desajuste caótico en el área del Arsenal bajo presión que culmina en un desafortunado autogol de Gabriel.",
            "Van Dijk and Alisson collide on a bouncing ball, allowing Martinelli to roll into an empty net.": "Van Dijk y Alisson chocan en un balón dividido, permitiendo a Martinelli empujar a puerta vacía.",
            "Konaté receives a second yellow card for cynical obstruction on Kai Havertz.": "Konaté recibe la segunda tarjeta amarilla por una obstrucción cínica sobre Kai Havertz.",
            "Trossard surges past Elliott down the wing and megs Alisson from a tight angle to seal the points.": "Trossard desborda a Elliott por la banda y bate a Alisson con un caño desde un ángulo escorado para sentenciar los puntos.",
            "Son skins Trippier on the byline and delivers a low cutback for Udogie to tap in his first Spurs goal.": "Son desborda a Trippier sobre la línea de fondo y pone un pase raso para que Udogie empuje su primer gol con los Spurs.",
            "Another masterclass run by Son beating Trippier, squaring for Richarlison to sweep home.": "Otra jugada magistral de Son superando a Trippier, asistiendo para que Richarlison defina de primeras al fondo de la red.",
            "Pedro Porro launches a stunning 50-yard diagonal pass, Richarlison controls and slots past Dubravka.": "Pedro Porro lanza un descomunal pase diagonal de 45 metros, Richarlison controla y define con clase ante Dubravka.",
            "Son is brought down by Dubravka and steps up to bury the penalty with supreme confidence.": "Son es derribado en el área por Dubravka y asume la responsabilidad para convertir el penalti con enorme jerarquía.",
            "Wilson intercepts a loose pass and lays it off for Joelinton to drive into the bottom corner.": "Wilson intercepta un pase impreciso y asiste a Joelinton para clavar un disparo seco y raso junto al poste.",
            "Messi rolls penalty into bottom right corner sending Lloris the wrong way.": "Messi engaña a Lloris y coloca el penalti con sutileza junto al poste derecho.",
            "Sublime counter-attack involving Messi, Alvarez, Mac Allister, finished emphatically by Di María.": "Contragolpe de antología hilvanado por Messi, Álvarez y Mac Allister, culminado con una definición sublime de Di María.",
            "Mbappé fires penalty past Martinez despite fingertips on the ball.": "Mbappé ajusta su remate de penalti batiendo a Martínez pese a rozar el esférico.",
            "Sensational first-time volley into far corner 97 seconds after his first goal!": "¡Volea sensacional de primeras al ángulo más lejano apenas 97 segundos después de su primer gol!",
            "[TACTICAL REVIEW | ": "[ANÁLISIS TÁCTICO | ",
            "Audio description: ": "Audiodescripción: ",
            "executes PASS at ": "ejecuta un pase en el minuto ",
            "executes SHOT at ": "ejecuta un disparo en el minuto ",
            "executes PRESSURE at ": "ejecuta presión defensiva en el minuto ",
            "executes INTERCEPTION at ": "ejecuta una intercepción en el minuto ",
            "executes DUEL at ": "disputa un duelo en el minuto ",
            "executes FOUL_COMMITTED at ": "comete una infracción en el minuto ",
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
            "Devastating Chelsea break: Palmer feeds Jackson, who squares to Sterling to cut inside Walker and curl in.": "चेल्सी का घातक काउंटर-अटैक: पाल्मर ने जैक्सन को गेंद दी, जिन्होंने स्टर्लिंग को पास दिया और स्टर्लिंग ने वॉकर को छकाते हुए शानदार कर्लिंग शॉट से गोल दागा!",
            "De Bruyne delivers a pinpoint whipped cross, but Haaland's bullet header veers inches wide.": "डी ब्रुइन ने सटीक घुमावदार क्रॉस दिया, लेकिन हालैंड का बुलेट हेडर कुछ ही इंच से चूक गया।",
            "A deflected block falls kindly to Rodri at the D, unleashing an unstoppable venomous left-foot rocket.": "डिफेंस से टकराई गेंद रॉड्री के पास डी पर गिरी, और उन्होंने बाएं पैर से अजेय रॉकेट शॉट दागकर गोल कर दिया!",
            "Saka reacts quickest to slot home after Havertz's shot is parried by Alisson.": "एलीसन द्वारा हैवर्ट्ज़ के शॉट को रोकने के बाद साका ने सबसे तेज़ी से गेंद को नेट में डाल दिया।",
            "[TACTICAL REVIEW | ": "[सामरिक समीक्षा | ",
            "Audio description: ": "ऑडियो विवरण: ",
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
            "Devastating Chelsea break: Palmer feeds Jackson, who squares to Sterling to cut inside Walker and curl in.": "هجمة مرتدة ساحقة لتشيلسي: بالمر يمرر لجاكسون الذي يرسلها لسترلينج ليرواغ ووكر ويسدد كرة مقوسة بديعة في الشباك!",
            "De Bruyne delivers a pinpoint whipped cross, but Haaland's bullet header veers inches wide.": "دي بروين يرسل عرضية متقنة بالميليمتير، لكن رأسية هالاند الصاروخية تمر بجوار القائم بسنتيمترات.",
            "A deflected block falls kindly to Rodri at the D, unleashing an unstoppable venomous left-foot rocket.": "كرة مرتدة من الدفاع تتهيأ لرودري على مشارف المنطقة، ليطلق صاروخاً يسارياً لا يُصد ولا يُرد في الشباك!",
            "Saka reacts quickest to slot home after Havertz's shot is parried by Alisson.": "ساكا يتصرف بأسرع ما يمكن ليتابع الكرة المرتدة من أليسون بعد تسديدة هافيرتز ويسكنها الشباك.",
            "[TACTICAL REVIEW | ": "[تحليل تكتيكي | ",
            "Audio description: ": "الوصف الصوتي: ",
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
            "Devastating Chelsea break: Palmer feeds Jackson, who squares to Sterling to cut inside Walker and curl in.": "Contra-ataque demolidor do Chelsea: Palmer toca para Jackson, que cruza rasteiro para Sterling cortar Walker e finalizar no ângulo com categoria!",
            "De Bruyne delivers a pinpoint whipped cross, but Haaland's bullet header veers inches wide.": "De Bruyne cruza na medida, mas o cabeceio potente de Haaland passa raspando a trave.",
            "A deflected block falls kindly to Rodri at the D, unleashing an unstoppable venomous left-foot rocket.": "A sobra fica limpa para Rodri na meia-lua, disparando um foguete canhoto imparável no fundo da rede.",
            "Saka reacts quickest to slot home after Havertz's shot is parried by Alisson.": "Saka reage mais rápido para empurrar para as redes após Alisson espalmar a finalização de Havertz.",
            "Chaotic miscommunication in the Arsenal box under pressure results in a Gabriel own goal.": "Falha de comunicação caótica na área do Arsenal sob pressão resulta em gol contra de Gabriel.",
            "Van Dijk and Alisson collide on a bouncing ball, allowing Martinelli to roll into an empty net.": "Van Dijk e Alisson trombam na bola dividida, permitindo que Martinelli empurre com tranquilidade para o gol vazio.",
            "Konaté receives a second yellow card for cynical obstruction on Kai Havertz.": "Konaté leva o segundo cartão amarelo por obstrução deliberada em Kai Havertz e é expulso.",
            "Trossard surges past Elliott down the wing and megs Alisson from a tight angle to seal the points.": "Trossard dispara pela ponta, passa por Elliott e dá uma caneta em Alisson de ângulo agudo para decretar o triunfo.",
            "[TACTICAL REVIEW | ": "[ANÁLISE TÁTICA | ",
            "Audio description: ": "Audiodescrição: ",
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
            "Devastating Chelsea break: Palmer feeds Jackson, who squares to Sterling to cut inside Walker and curl in.": "Contre-attaque foudroyante de Chelsea : Palmer lance Jackson qui sert Sterling pour repiquer devant Walker et marquer avec une superbe frappe enroulée !",
            "De Bruyne delivers a pinpoint whipped cross, but Haaland's bullet header veers inches wide.": "De Bruyne distille un centre millimétré, mais la tête puissante de Haaland frôle le montant.",
            "A deflected block falls kindly to Rodri at the D, unleashing an unstoppable venomous left-foot rocket.": "Un contre défensif atterrit devant Rodri à l'entrée de la surface, qui expédie un boulet de canon imparable du pied gauche.",
            "Saka reacts quickest to slot home after Havertz's shot is parried by Alisson.": "Saka est le plus prompt à réagir pour conclure dans le but après un tir de Havertz repoussé par Alisson.",
            "Chaotic miscommunication in the Arsenal box under pressure results in a Gabriel own goal.": "Mésentente chaotique dans la défense d'Arsenal sous pression provoquant un but contre son camp de Gabriel.",
            "Van Dijk and Alisson collide on a bouncing ball, allowing Martinelli to roll into an empty net.": "Collision entre Van Dijk et Alisson sur un ballon aérien, permettant à Martinelli de pousser le ballon dans le but vide.",
            "Konaté receives a second yellow card for cynical obstruction on Kai Havertz.": "Konaté reçoit un deuxième carton jaune pour obstruction évidente sur Kai Havertz.",
            "Trossard surges past Elliott down the wing and megs Alisson from a tight angle to seal the points.": "Trossard déborde Elliott sur l'aile et passe le ballon entre les jambes d'Alisson sous un angle fermé pour sceller la victoire.",
            "[TACTICAL REVIEW | ": "[ANALYSE TACTIQUE | ",
            "Audio description: ": "Audiodescription : ",
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
        translations_by_persona: Dict[str, Dict[str, str]] = {}

        for p_key, p_text in commentary_map.items():
            if not p_text:
                continue
            p_str = str(p_key.value if hasattr(p_key, "value") else p_key)
            translations_by_persona[p_str] = {"en": p_text}
            for lang in self.target_languages:
                translations_by_persona[p_str][lang] = SportsLocalizationEngine.translate_phrase(p_text, lang)

        for lang in self.target_languages:
            azure_translated = await self._translate_with_azure(primary_text, lang)
            if azure_translated:
                translations[lang] = azure_translated
            else:
                translations[lang] = SportsLocalizationEngine.translate_phrase(primary_text, lang)

        narrative_dict["translations"] = translations
        narrative_dict["translations_by_persona"] = translations_by_persona

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
                "historical_context": payload.get("historical_context"),
            },
            metadata=message.metadata,
        )

        return [out_message]
