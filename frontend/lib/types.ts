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

export interface EvaluationResponse {
  result: EvaluationResult | null;
  status: Status;
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
