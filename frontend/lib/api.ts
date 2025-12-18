import type { Call, UploadCallData } from "./types";

const API_BASE_URL = "http://localhost:8000/api/v1";

// Helper to get auth headers from localStorage
function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem("auth_token");
  if (!token) {
    throw new Error("Not authenticated");
  }
  return {
    Authorization: `Bearer ${token}`,
  };
}

// Auth API functions
export interface SignupData {
  name: string;
  email: string;
  password: string;
  domain?: string;
}

export interface LoginData {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: number;
    name: string;
    email: string;
    domain: string | null;
    created_at: string;
  };
}

export async function signup(data: SignupData): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/signup`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to sign up");
  }

  return response.json();
}

export async function login(data: LoginData): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to log in");
  }

  return response.json();
}

// Call API functions (all require authentication)
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
    headers: getAuthHeaders(),
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to upload call");
  }

  return response.json();
}

export async function getCall(id: string): Promise<Call> {
  const response = await fetch(`${API_BASE_URL}/calls/${id}`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch call");
  }

  return response.json();
}

export async function transcribeCall(id: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/calls/${id}/transcribe`, {
    method: "POST",
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to transcribe call");
  }
}

export async function evaluateCall(id: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/calls/${id}/evaluate`, {
    method: "POST",
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to evaluate call");
  }
}

export async function markAsBaseline(id: string): Promise<Call> {
  const response = await fetch(`${API_BASE_URL}/calls/${id}/baseline`, {
    method: "POST",
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to mark as baseline");
  }

  return response.json();
}

export async function unmarkAsBaseline(id: string): Promise<Call> {
  const response = await fetch(`${API_BASE_URL}/calls/${id}/baseline`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to unmark as baseline");
  }

  return response.json();
}
