import type { Call, UploadCallData, Baseline } from "./types";

const API_BASE_URL = "http://localhost:8000/api/v1";

/**
 * Strict auth guard - ensures token exists before making protected API calls.
 *
 * Why this exists:
 * - Prevents silent 401 errors by failing fast on the client
 * - Never sends unauthenticated requests to protected endpoints
 * - Allows UI to redirect to login immediately
 *
 * Throws "AUTH_REQUIRED" if:
 * - Called during SSR (window is undefined)
 * - No token found in localStorage
 *
 * @returns {string} Valid access token
 * @throws {Error} AUTH_REQUIRED if no token available
 */
function requireAuthToken(): string {
  if (typeof window === "undefined") {
    throw new Error("AUTH_REQUIRED");
  }

  const token = localStorage.getItem("access_token");

  if (!token) {
    throw new Error("AUTH_REQUIRED");
  }

  return token;
}

/**
 * Get authorization headers for protected API calls.
 *
 * IMPORTANT: This now throws if no token exists (fail-fast design).
 * UI components must handle AUTH_REQUIRED errors and redirect to login.
 *
 * @returns {HeadersInit} Headers with Authorization: Bearer <token>
 * @throws {Error} AUTH_REQUIRED if no token available
 */
function getAuthHeaders(): HeadersInit {
  const token = requireAuthToken();

  // Defensive logging (development only)
  if (process.env.NODE_ENV === "development") {
    console.debug("[AUTH] Token present:", !!token);
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

// Baseline API functions (Phase 7)
export async function generateBaseline(): Promise<Baseline> {
  const response = await fetch(`${API_BASE_URL}/baseline/generate`, {
    method: "POST",
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to generate baseline");
  }

  return response.json();
}

export async function getBaseline(): Promise<Baseline | null> {
  const response = await fetch(`${API_BASE_URL}/baseline/`, {
    headers: getAuthHeaders(),
  });

  if (response.status === 404) {
    return null; // No baseline exists yet
  }

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch baseline");
  }

  return response.json();
}

// Phase 8.2: Baseline trends API
import type { BaselineTrend, Team, TeamMember, TeamBaseline, TeamTrend } from "./types";

export async function getBaselineTrends(): Promise<BaselineTrend | null> {
  const response = await fetch(`${API_BASE_URL}/baseline/trends`, {
    headers: getAuthHeaders(),
  });

  // Phase 8.2: 204 No Content = insufficient data for trends (graceful)
  if (response.status === 204) {
    return null;
  }

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch baseline trends");
  }

  return response.json();
}

// Phase 9: Team/agency intelligence API
export async function createTeam(name: string): Promise<Team> {
  const response = await fetch(`${API_BASE_URL}/teams/`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to create team");
  }

  return response.json();
}

export async function getUserTeams(): Promise<Team[]> {
  const response = await fetch(`${API_BASE_URL}/teams/`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch teams");
  }

  const data = await response.json();
  return data.teams || [];
}

export async function addTeamMember(teamId: number, userId: number, role: "manager" | "member"): Promise<TeamMember> {
  const response = await fetch(`${API_BASE_URL}/teams/${teamId}/members`, {
    method: "POST",
    headers: {
      ...getAuthHeaders(),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ user_id: userId, role }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to add team member");
  }

  return response.json();
}

export async function getTeamMembers(teamId: number): Promise<TeamMember[]> {
  const response = await fetch(`${API_BASE_URL}/teams/${teamId}/members`, {
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch team members");
  }

  const data = await response.json();
  return data.members || [];
}

export async function generateTeamBaseline(teamId: number): Promise<TeamBaseline> {
  const response = await fetch(`${API_BASE_URL}/teams/${teamId}/baseline/generate`, {
    method: "POST",
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to generate team baseline");
  }

  return response.json();
}

export async function getTeamBaseline(teamId: number): Promise<TeamBaseline | null> {
  const response = await fetch(`${API_BASE_URL}/teams/${teamId}/baseline`, {
    headers: getAuthHeaders(),
  });

  if (response.status === 404) {
    return null; // No team baseline exists yet
  }

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch team baseline");
  }

  return response.json();
}

export async function getTeamTrends(teamId: number): Promise<TeamTrend | null> {
  const response = await fetch(`${API_BASE_URL}/teams/${teamId}/trends`, {
    headers: getAuthHeaders(),
  });

  // Phase 9: 204 No Content = insufficient team snapshots for trends
  if (response.status === 204) {
    return null;
  }

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch team trends");
  }

  return response.json();
}
