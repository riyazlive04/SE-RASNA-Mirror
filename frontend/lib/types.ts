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
