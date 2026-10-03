"""Premier League Historical and Curated Match Catalog.

Contains metadata, squads, and key milestone moments for Premier League fixtures.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from matchmind.models import PlayerInfo, TeamInfo


class KeyMoment(BaseModel):
    """Significant milestone or inflection point in a match."""
    id: str = Field(..., description="Unique moment identifier")
    minute: int = Field(..., description="Match minute")
    second: int = Field(0, description="Match second")
    period: int = Field(1, description="Match period (1 or 2)")
    moment_type: str = Field(..., description="GOAL, RED_CARD, YELLOW_CARD, BIG_CHANCE, TACTICAL_SHIFT")
    team: str = Field(..., description="Team associated with the moment")
    player: str = Field(..., description="Player involved")
    description: str = Field(..., description="Human readable highlight description")
    score_after: str = Field(..., description="Scoreline following this moment e.g. '1 - 0'")
    xg: Optional[float] = Field(None, description="Expected Goal value if shot")
    leverage_index: float = Field(1.0, description="Tactical leverage index")


class MatchSummary(BaseModel):
    """Metadata summary of a match fixture."""
    match_id: str
    title: str
    competition: str
    season: str
    date: str
    venue: str
    home_team: str
    away_team: str
    home_badge_color: str
    away_badge_color: str
    final_score: Dict[str, int]
    duration_minutes: int
    source_type: str  # "curated" or "statsbomb"
    statsbomb_match_id: Optional[str] = None
    description: str
    key_moments: List[KeyMoment] = []
    home_squad: List[PlayerInfo] = []
    away_squad: List[PlayerInfo] = []


# ---------------------------------------------------------------------------
# SQUAD DEFINITIONS
# ---------------------------------------------------------------------------

ARSENAL_SQUAD = [
    PlayerInfo(id=101, name="David Raya", jersey_number=22, position="Goalkeeper"),
    PlayerInfo(id=102, name="Ben White", jersey_number=4, position="Right Back"),
    PlayerInfo(id=103, name="William Saliba", jersey_number=2, position="Center Back"),
    PlayerInfo(id=104, name="Gabriel Magalhães", jersey_number=6, position="Center Back"),
    PlayerInfo(id=105, name="Oleksandr Zinchenko", jersey_number=35, position="Left Back"),
    PlayerInfo(id=106, name="Declan Rice", jersey_number=41, position="Defensive Midfield"),
    PlayerInfo(id=107, name="Jorginho", jersey_number=20, position="Central Midfield"),
    PlayerInfo(id=108, name="Martin Ødegaard", jersey_number=8, position="Attacking Midfield"),
    PlayerInfo(id=109, name="Bukayo Saka", jersey_number=7, position="Right Wing"),
    PlayerInfo(id=110, name="Kai Havertz", jersey_number=29, position="Striker"),
    PlayerInfo(id=111, name="Gabriel Martinelli", jersey_number=11, position="Left Wing"),
    PlayerInfo(id=112, name="Leandro Trossard", jersey_number=19, position="Forward"),
]

LIVERPOOL_SQUAD = [
    PlayerInfo(id=201, name="Alisson Becker", jersey_number=1, position="Goalkeeper"),
    PlayerInfo(id=202, name="Trent Alexander-Arnold", jersey_number=66, position="Right Back"),
    PlayerInfo(id=203, name="Ibrahima Konaté", jersey_number=5, position="Center Back"),
    PlayerInfo(id=204, name="Virgil van Dijk", jersey_number=4, position="Center Back"),
    PlayerInfo(id=205, name="Joe Gomez", jersey_number=2, position="Left Back"),
    PlayerInfo(id=206, name="Alexis Mac Allister", jersey_number=10, position="Central Midfield"),
    PlayerInfo(id=207, name="Ryan Gravenberch", jersey_number=38, position="Central Midfield"),
    PlayerInfo(id=208, name="Curtis Jones", jersey_number=17, position="Central Midfield"),
    PlayerInfo(id=209, name="Diogo Jota", jersey_number=20, position="Right Wing"),
    PlayerInfo(id=210, name="Cody Gakpo", jersey_number=18, position="Striker"),
    PlayerInfo(id=211, name="Luis Díaz", jersey_number=7, position="Left Wing"),
    PlayerInfo(id=212, name="Darwin Núñez", jersey_number=9, position="Striker"),
]

MAN_CITY_SQUAD = [
    PlayerInfo(id=301, name="Ederson", jersey_number=31, position="Goalkeeper"),
    PlayerInfo(id=302, name="Kyle Walker", jersey_number=2, position="Right Back"),
    PlayerInfo(id=303, name="Rúben Dias", jersey_number=3, position="Center Back"),
    PlayerInfo(id=304, name="Manuel Akanji", jersey_number=25, position="Center Back"),
    PlayerInfo(id=305, name="Nathan Aké", jersey_number=6, position="Left Back"),
    PlayerInfo(id=306, name="Rodri", jersey_number=16, position="Defensive Midfield"),
    PlayerInfo(id=307, name="Kevin De Bruyne", jersey_number=17, position="Attacking Midfield"),
    PlayerInfo(id=308, name="Phil Foden", jersey_number=47, position="Attacking Midfield"),
    PlayerInfo(id=309, name="Bernardo Silva", jersey_number=20, position="Right Wing"),
    PlayerInfo(id=310, name="Erling Haaland", jersey_number=9, position="Striker"),
    PlayerInfo(id=311, name="Jeremy Doku", jersey_number=11, position="Left Wing"),
]

CHELSEA_SQUAD = [
    PlayerInfo(id=401, name="Đorđe Petrović", jersey_number=28, position="Goalkeeper"),
    PlayerInfo(id=402, name="Malo Gusto", jersey_number=27, position="Right Back"),
    PlayerInfo(id=403, name="Axel Disasi", jersey_number=2, position="Center Back"),
    PlayerInfo(id=404, name="Levi Colwill", jersey_number=26, position="Center Back"),
    PlayerInfo(id=405, name="Ben Chilwell", jersey_number=21, position="Left Back"),
    PlayerInfo(id=406, name="Moisés Caicedo", jersey_number=25, position="Defensive Midfield"),
    PlayerInfo(id=407, name="Enzo Fernández", jersey_number=8, position="Central Midfield"),
    PlayerInfo(id=408, name="Conor Gallagher", jersey_number=23, position="Central Midfield"),
    PlayerInfo(id=409, name="Cole Palmer", jersey_number=20, position="Right Wing"),
    PlayerInfo(id=410, name="Nicolas Jackson", jersey_number=15, position="Striker"),
    PlayerInfo(id=411, name="Raheem Sterling", jersey_number=7, position="Left Wing"),
]

TOTTENHAM_SQUAD = [
    PlayerInfo(id=501, name="Guglielmo Vicario", jersey_number=13, position="Goalkeeper"),
    PlayerInfo(id=502, name="Pedro Porro", jersey_number=23, position="Right Back"),
    PlayerInfo(id=503, name="Cristian Romero", jersey_number=17, position="Center Back"),
    PlayerInfo(id=504, name="Ben Davies", jersey_number=33, position="Center Back"),
    PlayerInfo(id=505, name="Destiny Udogie", jersey_number=38, position="Left Back"),
    PlayerInfo(id=506, name="Yves Bissouma", jersey_number=8, position="Defensive Midfield"),
    PlayerInfo(id=507, name="Pape Matar Sarr", jersey_number=29, position="Central Midfield"),
    PlayerInfo(id=508, name="Dejan Kulusevski", jersey_number=21, position="Attacking Midfield"),
    PlayerInfo(id=509, name="Brennan Johnson", jersey_number=22, position="Right Wing"),
    PlayerInfo(id=510, name="Richarlison", jersey_number=9, position="Striker"),
    PlayerInfo(id=511, name="Son Heung-min", jersey_number=7, position="Left Wing"),
]

NEWCASTLE_SQUAD = [
    PlayerInfo(id=601, name="Martin Dúbravka", jersey_number=1, position="Goalkeeper"),
    PlayerInfo(id=602, name="Kieran Trippier", jersey_number=2, position="Right Back"),
    PlayerInfo(id=603, name="Fabian Schär", jersey_number=5, position="Center Back"),
    PlayerInfo(id=604, name="Jamaal Lascelles", jersey_number=6, position="Center Back"),
    PlayerInfo(id=605, name="Tino Livramento", jersey_number=21, position="Left Back"),
    PlayerInfo(id=606, name="Lewis Miley", jersey_number=67, position="Central Midfield"),
    PlayerInfo(id=607, name="Bruno Guimarães", jersey_number=39, position="Central Midfield"),
    PlayerInfo(id=608, name="Joelinton", jersey_number=7, position="Central Midfield"),
    PlayerInfo(id=609, name="Miguel Almirón", jersey_number=24, position="Right Wing"),
    PlayerInfo(id=610, name="Alexander Isak", jersey_number=14, position="Striker"),
    PlayerInfo(id=611, name="Anthony Gordon", jersey_number=10, position="Left Wing"),
]


# ---------------------------------------------------------------------------
# MATCH CATALOG REGISTRY
# ---------------------------------------------------------------------------

MATCH_CATALOG: Dict[str, MatchSummary] = {
    "arsenal_liverpool_2024": MatchSummary(
        match_id="arsenal_liverpool_2024",
        title="Arsenal vs Liverpool (Title Clash 2024)",
        competition="Premier League",
        season="2023/24",
        date="2024-02-04",
        venue="Emirates Stadium, London",
        home_team="Arsenal",
        away_team="Liverpool",
        home_badge_color="#EF0107",
        away_badge_color="#C8102E",
        final_score={"home": 3, "away": 1},
        duration_minutes=96,
        source_type="curated",
        description="A pivotal Premier League title clash where Arsenal dismantled Liverpool 3-1 through intense pressing and transitional clinical finishing.",
        home_squad=ARSENAL_SQUAD,
        away_squad=LIVERPOOL_SQUAD,
        key_moments=[
            KeyMoment(
                id="m1_14",
                minute=14,
                second=20,
                period=1,
                moment_type="GOAL",
                team="Arsenal",
                player="Bukayo Saka",
                description="Saka reacts quickest to slot home after Havertz's shot is parried by Alisson.",
                score_after="1 - 0",
                xg=0.68,
                leverage_index=2.4,
            ),
            KeyMoment(
                id="m1_45",
                minute=45,
                second=52,
                period=1,
                moment_type="GOAL",
                team="Liverpool",
                player="Gabriel Magalhães",
                description="Chaotic miscommunication in the Arsenal box under pressure results in a Gabriel own goal.",
                score_after="1 - 1",
                xg=0.34,
                leverage_index=2.8,
            ),
            KeyMoment(
                id="m1_67",
                minute=67,
                second=15,
                period=2,
                moment_type="GOAL",
                team="Arsenal",
                player="Gabriel Martinelli",
                description="Van Dijk and Alisson collide on a bouncing ball, allowing Martinelli to roll into an empty net.",
                score_after="2 - 1",
                xg=0.76,
                leverage_index=3.2,
            ),
            KeyMoment(
                id="m1_88",
                minute=88,
                second=30,
                period=2,
                moment_type="RED_CARD",
                team="Liverpool",
                player="Ibrahima Konaté",
                description="Konaté receives a second yellow card for cynical obstruction on Kai Havertz.",
                score_after="2 - 1",
                xg=None,
                leverage_index=2.6,
            ),
            KeyMoment(
                id="m1_92",
                minute=92,
                second=40,
                period=2,
                moment_type="GOAL",
                team="Arsenal",
                player="Leandro Trossard",
                description="Trossard surges past Elliott down the wing and megs Alisson from a tight angle to seal the points.",
                score_after="3 - 1",
                xg=0.31,
                leverage_index=1.9,
            ),
        ],
    ),
    "mancity_chelsea_2024": MatchSummary(
        match_id="mancity_chelsea_2024",
        title="Manchester City vs Chelsea (Etihad Drama)",
        competition="Premier League",
        season="2023/24",
        date="2024-02-17",
        venue="Etihad Stadium, Manchester",
        home_team="Manchester City",
        away_team="Chelsea",
        home_badge_color="#6CABDD",
        away_badge_color="#034694",
        final_score={"home": 1, "away": 1},
        duration_minutes=95,
        source_type="curated",
        description="End-to-end tactical spectacle as Chelsea's counter-attack struck first before Rodri fired a dramatic late equalizer.",
        home_squad=MAN_CITY_SQUAD,
        away_squad=CHELSEA_SQUAD,
        key_moments=[
            KeyMoment(
                id="m2_42",
                minute=42,
                second=10,
                period=1,
                moment_type="GOAL",
                team="Chelsea",
                player="Raheem Sterling",
                description="Devastating Chelsea break: Palmer feeds Jackson, who squares to Sterling to cut inside Walker and curl in.",
                score_after="0 - 1",
                xg=0.58,
                leverage_index=2.7,
            ),
            KeyMoment(
                id="m2_56",
                minute=56,
                second=35,
                period=2,
                moment_type="BIG_CHANCE",
                team="Manchester City",
                player="Erling Haaland",
                description="De Bruyne delivers a pinpoint whipped cross, but Haaland's bullet header veers inches wide.",
                score_after="0 - 1",
                xg=0.48,
                leverage_index=2.5,
            ),
            KeyMoment(
                id="m2_83",
                minute=83,
                second=18,
                period=2,
                moment_type="GOAL",
                team="Manchester City",
                player="Rodri",
                description="A deflected block falls kindly to Rodri at the D, unleashing an unstoppable venomous left-foot rocket.",
                score_after="1 - 1",
                xg=0.19,
                leverage_index=3.4,
            ),
        ],
    ),
    "tottenham_newcastle_2024": MatchSummary(
        match_id="tottenham_newcastle_2024",
        title="Tottenham vs Newcastle (Ange-Ball Showcase)",
        competition="Premier League",
        season="2023/24",
        date="2023-12-10",
        venue="Tottenham Hotspur Stadium, London",
        home_team="Tottenham Hotspur",
        away_team="Newcastle United",
        home_badge_color="#132257",
        away_badge_color="#241F20",
        final_score={"home": 4, "away": 1},
        duration_minutes=94,
        source_type="curated",
        description="Ange Postecoglou's high-octane inverted full-backs tore through Newcastle with Son Heung-min producing a playmaking clinic.",
        home_squad=TOTTENHAM_SQUAD,
        away_squad=NEWCASTLE_SQUAD,
        key_moments=[
            KeyMoment(
                id="m3_26",
                minute=26,
                second=12,
                period=1,
                moment_type="GOAL",
                team="Tottenham Hotspur",
                player="Destiny Udogie",
                description="Son skins Trippier on the byline and delivers a low cutback for Udogie to tap in his first Spurs goal.",
                score_after="1 - 0",
                xg=0.71,
                leverage_index=2.1,
            ),
            KeyMoment(
                id="m3_38",
                minute=38,
                second=44,
                period=1,
                moment_type="GOAL",
                team="Tottenham Hotspur",
                player="Richarlison",
                description="Another masterclass run by Son beating Trippier, squaring for Richarlison to sweep home.",
                score_after="2 - 0",
                xg=0.65,
                leverage_index=2.3,
            ),
            KeyMoment(
                id="m3_60",
                minute=60,
                second=18,
                period=2,
                moment_type="GOAL",
                team="Tottenham Hotspur",
                player="Richarlison",
                description="Pedro Porro launches a stunning 50-yard diagonal pass, Richarlison controls and slots past Dubravka.",
                score_after="3 - 0",
                xg=0.52,
                leverage_index=1.6,
            ),
            KeyMoment(
                id="m3_85",
                minute=85,
                second=10,
                period=2,
                moment_type="GOAL",
                team="Tottenham Hotspur",
                player="Son Heung-min",
                description="Son is brought down by Dubravka and steps up to bury the penalty with supreme confidence.",
                score_after="4 - 0",
                xg=0.79,
                leverage_index=1.2,
            ),
            KeyMoment(
                id="m3_91",
                minute=91,
                second=25,
                period=2,
                moment_type="GOAL",
                team="Newcastle United",
                player="Joelinton",
                description="Wilson intercepts a loose pass and lays it off for Joelinton to drive into the bottom corner.",
                score_after="4 - 1",
                xg=0.42,
                leverage_index=1.1,
            ),
        ],
    ),
    "match_3869685": MatchSummary(
        match_id="match_3869685",
        title="Argentina vs France (World Cup 2022 Final - StatsBomb Data)",
        competition="FIFA World Cup",
        season="2022",
        date="2022-12-18",
        venue="Lusail Iconic Stadium, Lusail",
        home_team="Argentina",
        away_team="France",
        home_badge_color="#75AADB",
        away_badge_color="#002654",
        final_score={"home": 3, "away": 3},
        duration_minutes=120,
        source_type="statsbomb",
        statsbomb_match_id="3869685",
        description="The greatest football match in modern history. 4,400+ real StatsBomb tracking and event datapoints.",
        home_squad=[],
        away_squad=[],
        key_moments=[
            KeyMoment(
                id="m4_23",
                minute=23,
                second=15,
                period=1,
                moment_type="GOAL",
                team="Argentina",
                player="Lionel Messi",
                description="Messi rolls penalty into bottom right corner sending Lloris the wrong way.",
                score_after="1 - 0",
                xg=0.79,
                leverage_index=2.8,
            ),
            KeyMoment(
                id="m4_36",
                minute=36,
                second=22,
                period=1,
                moment_type="GOAL",
                team="Argentina",
                player="Ángel Di María",
                description="Sublime counter-attack involving Messi, Alvarez, Mac Allister, finished emphatically by Di María.",
                score_after="2 - 0",
                xg=0.62,
                leverage_index=3.1,
            ),
            KeyMoment(
                id="m4_80",
                minute=80,
                second=11,
                period=2,
                moment_type="GOAL",
                team="France",
                player="Kylian Mbappé",
                description="Mbappé fires penalty past Martinez despite fingertips on the ball.",
                score_after="2 - 1",
                xg=0.79,
                leverage_index=3.6,
            ),
            KeyMoment(
                id="m4_81",
                minute=81,
                second=45,
                period=2,
                moment_type="GOAL",
                team="France",
                player="Kylian Mbappé",
                description="Sensational first-time volley into far corner 97 seconds after his first goal!",
                score_after="2 - 2",
                xg=0.28,
                leverage_index=4.5,
            ),
        ],
    ),
}


def get_match_catalog() -> List[MatchSummary]:
    """Returns list of all available matches in catalog."""
    return list(MATCH_CATALOG.values())


def get_match(match_id: str) -> Optional[MatchSummary]:
    """Retrieves a single match summary by ID."""
    return MATCH_CATALOG.get(match_id)
