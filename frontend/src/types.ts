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

export interface KeyMoment {
  id: string;
  minute: number;
  second: number;
  period: number;
  moment_type: "GOAL" | "RED_CARD" | "YELLOW_CARD" | "BIG_CHANCE" | "TACTICAL_SHIFT" | string;
  team: string;
  player: string;
  description: string;
  score_after: string;
  xg?: number;
  leverage_index: number;
}

export interface MatchSummary {
  match_id: string;
  title: string;
  competition: string;
  season: string;
  date: string;
  venue: string;
  home_team: string;
  away_team: string;
  home_badge_color: string;
  away_badge_color: string;
  final_score: { home: number; away: number };
  duration_minutes: number;
  source_type: "curated" | "statsbomb";
  description: string;
  key_moments: KeyMoment[];
}

export interface MatchTimelineInfo {
  match_id: string;
  title: string;
  competition: string;
  home_team: string;
  away_team: string;
  home_badge_color: string;
  away_badge_color: string;
  final_score: { home: number; away: number };
  duration_minutes: number;
  total_events: number;
  current_index: number;
  current_minute: number;
  current_second?: number;
  is_playing: boolean;
  speed: number;
  key_moments: KeyMoment[];
}

export type PitchOverlayMode = "standard" | "heatmap" | "pass_network" | "pressing";

export interface HeatmapPoint {
  x: number;
  y: number;
  intensity: number;
  count: number;
}

export interface HeatmapData {
  pitch_length: number;
  pitch_width: number;
  total_actions: number;
  max_intensity: number;
  points: HeatmapPoint[];
}

export interface PassNode {
  id: string;
  name: string;
  jersey_number: number;
  position: string;
  x: number;
  y: number;
  touch_count: number;
}

export interface PassLink {
  source: string;
  target: string;
  count: number;
  weight: number;
}

export interface PassNetworkData {
  team: string;
  nodes: PassNode[];
  links: PassLink[];
  total_links: number;
}

export interface PressureZoneData {
  team: string;
  total_pressures: number;
  high_press_pct: number;
  breakdown: {
    high_press_attacking_third: number;
    mid_block_middle_third: number;
    low_block_defensive_third: number;
  };
  high_press_actions: Array<{
    x: number;
    y: number;
    player: string;
    type: string;
    outcome: string;
  }>;
}


