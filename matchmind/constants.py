"""Constants, coordinates, thresholds, and taxonomy for MatchMind."""

from enum import Enum

# =====================================================================
# Pitch Dimensions & Geometry
# =====================================================================
# StatsBomb pitch coordinate system (yards)
STATSBOMB_PITCH_LENGTH = 120.0
STATSBOMB_PITCH_WIDTH = 80.0
STATSBOMB_GOAL_LINE_X = 120.0
STATSBOMB_GOAL_CENTER_Y = 40.0
STATSBOMB_GOAL_WIDTH = 8.0  # 8 yards (~7.32m)

# Standard FIFA / SPADL pitch coordinate system (meters)
SPADL_PITCH_LENGTH = 105.0
SPADL_PITCH_WIDTH = 68.0
SPADL_GOAL_LINE_X = 105.0
SPADL_GOAL_CENTER_Y = 34.0

# =====================================================================
# Event Types & Action Categorization
# =====================================================================
class EventType(str, Enum):
    PASS = "Pass"
    SHOT = "Shot"
    BALL_RECEIPT = "Ball Receipt*"
    CARRY = "Carry"
    PRESSURE = "Pressure"
    DUEL = "Duel"
    INTERCEPTION = "Interception"
    BLOCK = "Block"
    CLEARANCE = "Clearance"
    DISPOSSESSED = "Dispossessed"
    FOUL_COMMITTED = "Foul Committed"
    FOUL_WON = "Foul Won"
    GOAL = "Goal"
    OWN_GOAL = "Own Goal"
    DRIBBLE = "Dribble"
    BALL_RECOVERY = "Ball Recovery"
    SUBSTITUTION = "Substitution"
    TACTICAL_SHIFT = "Tactical Shift"

class ActionOutcome(str, Enum):
    SUCCESS = "Success"
    INCOMPLETE = "Incomplete"
    BLOCKED = "Blocked"
    SAVED = "Saved"
    OFF_TARGET = "Off Target"
    POST = "Post"
    GOAL = "Goal"
    UNKNOWN = "Unknown"

# =====================================================================
# Tactical & Analytical Thresholds
# =====================================================================
# PPDA (Passes Per Defensive Action) Pressing Tiers
PPDA_ULTRA_HIGH_PRESS = 8.0
PPDA_BALANCED_PRESS = 13.0
# Values > 13 indicate a mid-to-low defensive block

# High danger xG threshold (Moments that require deep explanation)
HIGH_XG_THRESHOLD = 0.30
SPECTACULAR_GOAL_XG_THRESHOLD = 0.08  # Low xG converted = remarkable goal

# Field Tilt Thresholds (Final-third pass dominance)
FIELD_TILT_DOMINANT = 65.0  # > 65% indicates territorial siege
FIELD_TILT_BALANCED = 50.0

# Leverage Index Thresholds (Emotional volatility of moments)
LEVERAGE_INDEX_HIGH = 3.0
LEVERAGE_INDEX_EXTREME = 6.0  # 90th+ min 1-goal differential, penalties, red cards

# Momentum Shift Threshold (Change required to signal significant tactical shift)
MOMENTUM_SHIFT_THRESHOLD = 30.0


# =====================================================================
# Audience Personas & Target Languages
# =====================================================================
class FanPersona(str, Enum):
    TACTICAL_ANALYST = "tactical_analyst"
    CASUAL_FAN = "casual_fan"
    BROADCAST_COMMENTATOR = "broadcast_commentator"
    ACCESSIBILITY_AUDIO = "accessibility_audio"

SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish (Español)",
    "hi": "Hindi (हिन्दी)",
    "ar": "Arabic (العربية)",
    "pt": "Portuguese (Português)",
    "fr": "French (Français)",
    "de": "German (Deutsch)",
    "ja": "Japanese (日本語)",
}
