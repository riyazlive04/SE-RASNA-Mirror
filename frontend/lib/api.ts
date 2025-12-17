import type { Call, UploadCallData } from "./types";

const API_BASE_URL = "http://localhost:8000/api/v1";

export async function uploadCall(data: UploadCallData): Promise<Call> {
  const formData = new FormData();
  formData.append("audio_file", data.audio_file);
  formData.append("agent_name", data.agent_name);
  if (data.customer_name) {
    formData.append("customer_name", data.customer_name);
  }
  formData.append("call_type", data.call_type);
  formData.append("lead_type", data.lead_type);
  formData.append("call_stage", data.call_stage);
  formData.append("deck_shared", String(data.deck_shared));

  const response = await fetch(`${API_BASE_URL}/calls/`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to upload call");
  }

  return response.json();
}

export async function getCall(id: string): Promise<Call> {
  const response = await fetch(`${API_BASE_URL}/calls/${id}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch call");
  }

  return response.json();
}

export async function transcribeCall(id: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/calls/${id}/transcribe`, {
    method: "POST",
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to transcribe call");
  }
}

export async function evaluateCall(id: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/calls/${id}/evaluate`, {
    method: "POST",
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to evaluate call");
  }
}
