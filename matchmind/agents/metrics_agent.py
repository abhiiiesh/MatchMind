"""Metrics Agent: Stage 2 of the MatchMind Intelligence Pipeline.

Consumes NORMALIZED_EVENT envelopes, calculates advanced tactical metrics
(xG, xT, PPDA, Field Tilt, Leverage Index), and emits METRIC_UPDATE envelopes.
"""

from typing import Dict, List, Optional
from matchmind.agents.base_agent import BaseAgent
from matchmind.constants import (
    FIELD_TILT_DOMINANT,
    HIGH_XG_THRESHOLD,
    LEVERAGE_INDEX_EXTREME,
    LEVERAGE_INDEX_HIGH,
    EventType,
)
from matchmind.metrics.expected_goals import ExpectedGoalsModel
from matchmind.metrics.expected_threat import ExpectedThreatGrid
from matchmind.metrics.pressing import PressingEngine
from matchmind.metrics.momentum import MomentumEngine
from matchmind.models import AgentMessage, MatchEvent, MetricState


class MetricsAgent(BaseAgent):
    """Calculates live tactical and predictive metrics."""

    def __init__(self):
        super().__init__(
            agent_id="metrics_agent",
            role_name="Advanced Football Metrics Engine",
            supported_message_types=["NORMALIZED_EVENT"],
        )
        self.xg_model = ExpectedGoalsModel()
        self.xt_grid = ExpectedThreatGrid()
        self.pressing_engine = PressingEngine(window_minutes=5)
        self.momentum_engine = MomentumEngine(window_minutes=5)

        # Rolling internal state
        self.active_match_id: Optional[str] = None
        self.home_team_name: Optional[str] = None
        self.away_team_name: Optional[str] = None
        self.score = {"home": 0, "away": 0}
        self.cumulative_xg = {"home": 0.0, "away": 0.0}
        self.cumulative_xt = {"home": 0.0, "away": 0.0}
        self.final_third_passes = {"home": 0, "away": 0}
        self.pass_counts = {"home": 0, "away": 0}

    def reset(self, match_id: Optional[str] = None) -> None:
        """Resets all metrics state cleanly for a new match or replay sequence."""
        self.active_match_id = match_id
        self.home_team_name = None
        self.away_team_name = None
        self.score = {"home": 0, "away": 0}
        self.cumulative_xg = {"home": 0.0, "away": 0.0}
        self.cumulative_xt = {"home": 0.0, "away": 0.0}
        self.final_third_passes = {"home": 0, "away": 0}
        self.pass_counts = {"home": 0, "away": 0}
        self.pressing_engine = PressingEngine(window_minutes=5)
        self.momentum_engine = MomentumEngine(window_minutes=5)
        self.log.info("MetricsAgent state reset", match_id=match_id)

    def _determine_teams(self, event: MatchEvent) -> None:
        """Establish home vs away identities dynamically."""
        if not self.home_team_name:
            self.home_team_name = event.team.name
        elif not self.away_team_name and event.team.name != self.home_team_name:
            self.away_team_name = event.team.name

    def _calculate_leverage_index(self, minute: int, score_diff: int, action_xg: Optional[float]) -> float:
        """Computes the emotional volatility / importance of the current moment."""
        # Time pressure factor (increases sharply after 75th minute)
        time_factor = 1.0 + (minute / 90.0) ** 2.2
        # Closeness factor (tight games are exponentially more leveraged)
        closeness_factor = 2.5 if abs(score_diff) <= 1 else (1.2 if abs(score_diff) == 2 else 0.4)
        # Action danger factor
        danger_factor = 1.0 + (action_xg or 0.0) * 3.0

        leverage = round(time_factor * closeness_factor * danger_factor, 2)
        return float(leverage)

    async def process(self, message: AgentMessage) -> List[AgentMessage]:
        payload = message.payload
        event_dict = payload.get("event")
        event = MatchEvent(**event_dict)

        if self.active_match_id != event.match_id:
            self.reset(event.match_id)

        self._determine_teams(event)
        is_home = (event.team.name == self.home_team_name)
        team_key = "home" if is_home else "away"
        opp_key = "away" if is_home else "home"
        opp_name = self.away_team_name if is_home else (self.home_team_name or "Opponent")

        action_xg = None
        action_xt = None
        is_goal = False

        replay_score = payload.get("replay_score") or (message.metadata.get("replay_score") if message.metadata else None)

        # 1. Shot Event Analysis (xG)
        if event.event_type == EventType.SHOT:
            raw_xg = event.metadata.get("shot_statsbomb_xg")
            if event.start_x is not None and event.start_y is not None:
                action_xg = self.xg_model.calculate_xg(
                    x=event.start_x,
                    y=event.start_y,
                    under_pressure=event.under_pressure,
                    precomputed_xg=raw_xg,
                )
                if replay_score is not None:
                    self.cumulative_xg[team_key] = round(action_xg, 2)
                    self.cumulative_xg[opp_key] = 0.0
                else:
                    self.cumulative_xg[team_key] = round(self.cumulative_xg[team_key] + action_xg, 2)

            if event.outcome == "Goal":
                is_goal = True
                if replay_score is None:
                    self.score[team_key] += 1
        elif event.event_type in [EventType.GOAL, "Goal"]:
            is_goal = True
            if replay_score is None:
                self.score[team_key] += 1

        if replay_score is not None:
            self.score = {
                "home": int(replay_score.get("home", 0)),
                "away": int(replay_score.get("away", 0)),
            }

        # 2. Pass / Progression Analysis (xT & Field Tilt)
        if event.event_type == EventType.PASS:
            self.pass_counts[team_key] += 1
            if (
                event.start_x is not None
                and event.start_y is not None
                and event.end_x is not None
                and event.end_y is not None
            ):
                action_xt = self.xt_grid.value_action(
                    event.start_x, event.start_y, event.end_x, event.end_y
                )
                if action_xt and action_xt > 0:
                    self.cumulative_xt[team_key] = round(self.cumulative_xt[team_key] + action_xt, 3)
                if event.start_x >= 80.0:  # Attacking third
                    self.final_third_passes[team_key] += 1


        # 3. Pressing & PPDA Registration
        is_defensive = event.event_type in [
            EventType.PRESSURE,
            EventType.DUEL,
            EventType.INTERCEPTION,
            EventType.BLOCK,
            EventType.FOUL_COMMITTED,
        ]
        is_pressing_zone = (event.start_x or 0.0) >= 48.0
        self.pressing_engine.record_action(
            minute=event.minute,
            team_name=event.team.name,
            is_defensive_action=is_defensive,
            is_opponent_pass=(event.event_type == EventType.PASS),
            is_pressing_zone=is_pressing_zone,
        )

        # Compute rolling PPDA
        home_ppda = self.pressing_engine.get_current_ppda(
            event.minute, self.home_team_name or "Home", self.away_team_name or "Away"
        )
        away_ppda = self.pressing_engine.get_current_ppda(
            event.minute, self.away_team_name or "Away", self.home_team_name or "Home"
        )

        # Field Tilt Calculation
        total_ft_passes = self.final_third_passes["home"] + self.final_third_passes["away"]
        field_tilt_val = (
            round((self.final_third_passes["home"] / total_ft_passes) * 100.0, 1)
            if total_ft_passes > 0
            else 50.0
        )

        # Momentum & Leverage Calculation
        score_diff = self.score["home"] - self.score["away"]
        current_leverage = self._calculate_leverage_index(event.minute, score_diff, action_xg)

        momentum_dir = "balanced"
        if field_tilt_val >= FIELD_TILT_DOMINANT:
            momentum_dir = "home_dominant"
        elif field_tilt_val <= (100.0 - FIELD_TILT_DOMINANT):
            momentum_dir = "away_dominant"

        # Record momentum step and compute timeline
        momentum_entry = self.momentum_engine.record_step(
            minute=event.minute,
            field_tilt=field_tilt_val,
            home_xg=self.cumulative_xg["home"],
            away_xg=self.cumulative_xg["away"],
            home_xt_added=self.cumulative_xt["home"],
            away_xt_added=self.cumulative_xt["away"],
            home_ppda=home_ppda,
            away_ppda=away_ppda,
            event_type=event.event_type,
        )
        momentum_val = momentum_entry["value"]
        is_momentum_shift = momentum_entry["is_shift"]

        metric_state = MetricState(
            match_id=event.match_id,
            minute=event.minute,
            home_team=self.home_team_name or "Home",
            away_team=self.away_team_name or "Away",
            score=self.score.copy(),
            cumulative_xg=self.cumulative_xg.copy(),
            rolling_ppda={"home": home_ppda, "away": away_ppda},
            field_tilt=field_tilt_val,
            possession_pct={
                "home": round((self.pass_counts["home"] / max(1, sum(self.pass_counts.values()))) * 100, 1),
                "away": round((self.pass_counts["away"] / max(1, sum(self.pass_counts.values()))) * 100, 1),
            },
            momentum_direction=momentum_dir,
            momentum_value=momentum_val,
            momentum_shift_detected=is_momentum_shift or (current_leverage >= LEVERAGE_INDEX_HIGH),
            momentum_timeline=self.momentum_engine.get_timeline(max_points=40),
            current_leverage_index=current_leverage,
            current_action_xg=action_xg,
            current_action_xt=action_xt,
        )


        out_msg = AgentMessage(
            source_agent=self.agent_id,
            target_agents=["context_agent"],
            match_id=event.match_id,

            event_index=event.index,
            match_minute=event.minute,
            message_type="METRIC_UPDATE",
            payload={
                "metric_state": metric_state.model_dump(),
                "event": event.model_dump(),
                "is_goal": is_goal,
                "is_high_threat": (action_xg or 0.0) >= HIGH_XG_THRESHOLD,
            },
        )

        return [out_msg]
