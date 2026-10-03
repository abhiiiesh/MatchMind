export interface PlayerInfo {
  id: number;
  name: string;
  jersey_number?: number;
  position?: string;
}

export interface TeamInfo {
  id: number;
  name: string;
}

export interface MatchEvent {
  event_id: string;
  index: number;
  period: number;
  timestamp: string;
  minute: number;
  second: number;
  match_id: string;
  event_type: string;
  team: TeamInfo;
  player?: PlayerInfo;
  start_x?: number;
  start_y?: number;
  end_x?: number;
  end_y?: number;
  outcome?: string;
  under_pressure?: boolean;
  duration_seconds?: number;
  metadata?: Record<string, any>;
}

export interface MetricState {
  match_id: string;
  minute: number;
  home_team: string;
  away_team: string;
  score: { home: number; away: number };
  cumulative_xg: { home: number; away: number };
  rolling_ppda: { home: number; away: number };
  field_tilt: number;
  possession_pct: { home: number; away: number };
  momentum_direction: string;
  momentum_value?: number;
  momentum_shift_detected: boolean;
  momentum_timeline?: Array<{ minute: number; value: number; is_shift: boolean; event_type: string }>;
  current_leverage_index: number;
  current_action_xg?: number;
  current_action_xt?: number;
}


export interface NarrativeOutput {
  narrative_id: string;
  match_id: string;
  event_index: number;
  minute: number;
  game_state_arc: string;
  leverage_index: number;
  why_it_matters_explanation: string;
  commentary_by_persona: Record<string, string>;
  translations: Record<string, string>;
  verified_by_factcheck: boolean;
  factcheck_notes?: string;
}

export interface VerifiedMessagePayload {
  narrative: NarrativeOutput;
  event: MatchEvent;
  metric_state: MetricState;
  is_verified: boolean;
}

export interface AgentHealth {
  agent_id: string;
  role_name: string;
  status: string;
  last_active: string;
  processed_count: number;
  error_count: number;
  average_latency_ms: number;
  current_task?: string;
}

export type PersonaType = "tactical_analyst" | "casual_fan" | "broadcast_commentator" | "accessibility_audio";
export type LanguageCode = "en" | "es" | "hi" | "ar" | "pt" | "fr";
