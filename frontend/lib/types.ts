export type LeadType = "hot" | "warm" | "cold";
export type CallStage = "qualification" | "main" | "follow-up";
export type Status = "pending" | "completed" | "failed";

export interface RasnaScore {
  rapport: number;
  situation: number;
  pain: number;
  need: number;
  ask: number;
  overall: number;
}

export interface EvaluationResult {
  scores: RasnaScore;
  strengths: string[];
  improvements: string[];
  next_call_focus: string;
  llm_used?: boolean;
}

export interface TranscriptionResponse {
  text: string | null;
  status: Status;
}

export interface BaselineComparison {
  above_baseline: string[];
  below_baseline: string[];
  summary: string;
}

export interface EvaluationResponse {
  result: EvaluationResult | null;
  status: Status;
  comparison_to_baseline?: BaselineComparison | null;
}

export interface Call {
  id: number;
  agent_name: string;
  customer_name: string | null;
  call_type: string;
  call_date: string;
  lead_type: LeadType;
  call_stage: CallStage;
  deck_shared: boolean;
  audio_filename: string;
  audio_format: string;
  audio_size: number;
  transcription: TranscriptionResponse;
  evaluation: EvaluationResponse;
  is_baseline: boolean;
  baseline_marked_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface UploadCallData {
  agent_name: string;
  customer_name?: string;
  call_type: string;
  lead_type: LeadType;
  call_stage: CallStage;
  deck_shared: boolean;
  audio_file: File;
}

export interface BaselineSummary {
  common_strengths: string[];
  common_improvement_themes: string[];
  average_overall_score: number;
}

export interface RasnaAverages {
  rapport: number;
  ask: number;
  situation: number;
  next_steps: number;
  articulation: number;
}

export interface Baseline {
  id: number;
  user_id: number;
  rasna_averages: RasnaAverages;
  summary: BaselineSummary;
  call_count: number;
  is_stale: boolean;  // Phase 7.1: True when baseline calls changed
  created_at: string;
  updated_at: string;
}

// Phase 8: Baseline evolution trend
export interface BaselineTrend {
  improved_dimensions: string[];
  declined_dimensions: string[];
  stable_dimensions: string[];
  dimension_deltas: Record<string, number>;
  summary: string;
  snapshots_compared: number;
  latest_snapshot_date: string;
  previous_snapshot_date: string;
  latest_call_count: number;
  previous_call_count: number;
}

// Phase 9: Team/agency intelligence
export type TeamRole = "owner" | "manager" | "member";

export interface Team {
  id: number;
  name: string;
  created_by: number;
  created_at: string;
  role: TeamRole;  // Current user's role in this team
}

export interface TeamMember {
  user_id: number;
  name: string;
  email: string;
  role: TeamRole;
  joined_at: string;
}

export interface TeamBaseline {
  team_id: number;
  aggregated_rasna_averages: Record<string, number>;  // NO individual scores
  agent_count: number;
  snapshot_created_at: string;
}

export interface TeamTrend {
  improved_dimensions: string[];
  declined_dimensions: string[];
  stable_dimensions: string[];
  dimension_deltas: Record<string, number>;
  summary: string;
  snapshots_compared: number;
  latest_snapshot_date: string;
  previous_snapshot_date: string;
  latest_agent_count: number;
  previous_agent_count: number;
}
