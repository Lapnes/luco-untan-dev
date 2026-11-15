/**
 * Luco API Client: Manajemen Autentikasi, Obrolan Sesi Aktif, & Monitoring
 */

// Gunakan URL relatif jika di-proxy oleh Vite, atau URL backend spesifik
const getApiBase = (): string => {
  if (typeof window === 'undefined') return 'http://localhost:8000';
  const { hostname, port, origin } = window.location;
  if (origin.includes('uas-ai.ragilamirzaky.com') || origin.includes('ragilamirzaky.com')) {
    return 'https://uas-ai-be.ragilamirzaky.com';
  }
  if (port === '5173') {
    return `http://${hostname}:8000`;
  }
  return '';
};

export const API_BASE = getApiBase();

// Storage Keys
const TOKEN_KEY = 'luco_access_token';
const REFRESH_KEY = 'luco_refresh_token';
const USER_KEY = 'luco_user_profile';

export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  picture?: string;
  nim_or_nip?: string;
  angkatan?: number;
  is_admin?: boolean;
}

export interface ClarificationCardData {
  id?: string;
  title: string;
  options: string[];
  allow_custom?: boolean;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
  citations?: any[];
  trajectory?: any[];
  steps?: number;
  latency_s?: number;
  rejected?: boolean;
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
  cost_idr?: number;
  user_name?: string;
  clarification?: ClarificationCardData | null;
  feedback?: 'like' | 'dislike' | null;
}

export interface ActiveSessionResponse {
  session: {
    id: string;
    title: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;
  };
  messages: ChatMessage[];
}

export interface MonitoringSummary {
  source: string;
  total_requests: number;
  total_users: number;
  total_sessions: number;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens: number;
  total_cost_usd: number;
  total_cost_idr: number;
  avg_latency_s: number;
  total_rejected: number;
  rejection_rate_percent: number;
  models: {
    model: string;
    requests: number;
    tokens: number;
    prompt_tokens?: number;
    completion_tokens?: number;
    cost_usd: number;
    cost_idr?: number;
    avg_latency_s?: number;
    errors?: number;
  }[];
}

export interface AuditToolCall {
  call_index?: number;
  tool: string;
  args: Record<string, any>;
  duration_ms?: number;
  gap_before_ms?: number;
  files_accessed?: string[];
  lines_accessed?: string;
  output_summary?: string;
  output?: string;
}

export interface AuditTimingBreakdown {
  t_req_in?: number;
  router_latency_ms?: number;
  tools_total_ms?: number;
  tool_calls_breakdown?: AuditToolCall[];
  llm_final_generation_ms?: number;
  total_latency_ms?: number;
  total_latency_s?: number;
}

export interface AuditLogItem {
  id: string;
  created_at: string;
  user_id?: string;
  user_email?: string;
  session_id?: string;
  message_id?: string;
  endpoint: string;
  model: string;
  question: string;
  answer?: string;
  user_prompt_tokens?: number;
  system_prompt_tokens?: number;
  context_tokens?: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number;
  estimated_cost_idr: number;
  latency_s: number;
  steps: number;
  tool_calls?: AuditToolCall[];
  system_prompt?: string;
  user_prompt?: string;
  timing_breakdown?: AuditTimingBreakdown;
  feedback?: 'like' | 'dislike' | null;
  rejected: boolean;
  status?: string;
  reason?: string;
}

// Token Helpers
export const getToken = (): string | null => localStorage.getItem(TOKEN_KEY);
export const setTokens = (access: string, refresh?: string): void => {
  localStorage.setItem(TOKEN_KEY, access);
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
};
export const getUser = (): UserProfile | null => {
  const data = localStorage.getItem(USER_KEY);
  return data ? JSON.parse(data) : null;
};
export const setUser = (user: UserProfile): void => {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
};
export const clearAuth = (): void => {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
};

// Headers with Auth
const authHeaders = (): Record<string, string> => {
  const token = getToken();
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
};

// --- Auth APIs ---

export const getGoogleLoginUrl = (): string => {
  const currentOrigin = window.location.origin;
  return `${API_BASE}/v1/auth/google/login?redirect_to=${encodeURIComponent(currentOrigin)}`;
};

export const fetchCurrentUser = async (): Promise<UserProfile | null> => {
  if (!getToken()) return null;
  const res = await fetch(`${API_BASE}/v1/auth/me`, {
    headers: authHeaders(),
  });
  if (!res.ok) {
    if (res.status === 401) {
      clearAuth();
    }
    return null;
  }
  const user = await res.json();
  setUser(user);
  return user;
};

export const guestLogin = async (name: string = 'Tamu Mahasiswa'): Promise<UserProfile> => {
  const randomId = Math.random().toString(36).substring(2, 8);
  const email = `guest_${randomId}@student.untan.ac.id`;
  const res = await fetch(`${API_BASE}/v1/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email,
      password: `GuestPass_${randomId}!`,
      full_name: `${name} (${randomId.toUpperCase()})`,
    }),
  });

  if (!res.ok) {
    throw new Error('Gagal membuat sesi tamu');
  }

  const data = await res.json();
  setTokens(data.access_token, data.refresh_token);
  const profile: UserProfile = {
    id: data.user.id,
    email: data.user.email,
    full_name: data.user.full_name,
  };
  setUser(profile);
  return profile;
};

// --- Chat APIs ---

export const fetchActiveSession = async (): Promise<ActiveSessionResponse> => {
  const res = await fetch(`${API_BASE}/v1/session/active`, {
    headers: authHeaders(),
  });
  if (!res.ok) {
    if (res.status === 401) {
      clearAuth();
      throw new Error('UNAUTHORIZED');
    }
    throw new Error('Gagal memuat sesi aktif');
  }
  return res.json();
};

export const sendChatMessage = async (
  content: string,
  mode: string = 'viking_indobert',
  signal?: AbortSignal
): Promise<any> => {
  const res = await fetch(`${API_BASE}/v1/chat`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ content, mode }),
    signal,
  });
  if (!res.ok) {
    if (res.status === 401) {
      clearAuth();
      throw new Error('Sesi telah berakhir. Silakan masuk kembali.');
    }
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Gagal mengirim pesan');
  }
  return res.json();
};

export const clearSession = async (): Promise<any> => {
  const res = await fetch(`${API_BASE}/v1/session/clear`, {
    method: 'POST',
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error('Gagal mereset sesi');
  return res.json();
};

export const listSessions = async (): Promise<any[]> => {
  const res = await fetch(`${API_BASE}/v1/sessions`, {
    headers: authHeaders(),
  });
  if (!res.ok) return [];
  const data = await res.json();
  if (Array.isArray(data)) return data;
  return data.sessions || [];
};

export const switchSession = async (sessionId: string): Promise<any> => {
  const res = await fetch(`${API_BASE}/v1/session/${sessionId}/switch`, {
    method: 'POST',
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error('Gagal beralih sesi');
  return res.json();
};

export const deleteSession = async (sessionId: string): Promise<any> => {
  const res = await fetch(`${API_BASE}/v1/sessions/${sessionId}`, {
    method: 'DELETE',
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error('Gagal menghapus sesi');
  return res.json();
};

export const getSharedSession = async (sessionId: string): Promise<any> => {
  const res = await fetch(`${API_BASE}/v1/share/${sessionId}`);
  if (!res.ok) throw new Error('Sesi bersama tidak ditemukan');
  return res.json();
};

// --- Monitoring APIs ---

export interface MonitoringLogsResponse {
  total: number;
  offset: number;
  limit: number;
  logs: AuditLogItem[];
}

export const fetchMonitoringSummary = async (
  model?: string,
  startTime?: string,
  endTime?: string
): Promise<MonitoringSummary> => {
  const url = new URL(`${API_BASE}/v1/monitoring/summary`);
  if (model && model !== 'all') {
    url.searchParams.set('model', model);
  }
  if (startTime) {
    url.searchParams.set('start_time', startTime);
  }
  if (endTime) {
    url.searchParams.set('end_time', endTime);
  }
  const res = await fetch(url.toString(), {
    headers: authHeaders(),
  });
  if (!res.ok) throw new Error('Gagal mengambil ringkasan monitoring');
  return res.json();
};

export const fetchMonitoringLogs = async (
  limit: number = 500,
  offset: number = 0,
  model?: string,
  startTime?: string,
  endTime?: string
): Promise<MonitoringLogsResponse> => {
  const url = new URL(`${API_BASE}/v1/monitoring/logs`);
  url.searchParams.set('limit', String(limit));
  url.searchParams.set('offset', String(offset));
  if (model && model !== 'all') {
    url.searchParams.set('model', model);
  }
  if (startTime) {
    url.searchParams.set('start_time', startTime);
  }
  if (endTime) {
    url.searchParams.set('end_time', endTime);
  }
  const res = await fetch(url.toString(), {
    headers: authHeaders(),
  });
  if (!res.ok) return { total: 0, offset: 0, limit, logs: [] };
  const data = await res.json();
  return {
    total: data.total ?? (data.logs?.length || 0),
    offset: data.offset ?? offset,
    limit: data.limit ?? limit,
    logs: data.logs || [],
  };
};

export const sendFeedback = async (
  messageId: string,
  feedback: 'like' | 'dislike' | 'none'
): Promise<void> => {
  const res = await fetch(`${API_BASE}/v1/messages/${messageId}/feedback`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({ feedback }),
  });
  if (!res.ok) {
    throw new Error('Gagal mencatat feedback reaksi.');
  }
};

export const getExportCsvUrl = (model?: string, startTime?: string, endTime?: string): string => {
  const url = new URL(`${API_BASE}/v1/monitoring/export`);
  if (model && model !== 'all') url.searchParams.set('model', model);
  if (startTime) url.searchParams.set('start_time', startTime);
  if (endTime) url.searchParams.set('end_time', endTime);
  return url.toString();
};

export const downloadMonitoringCsv = async (
  model?: string,
  startTime?: string,
  endTime?: string
): Promise<void> => {
  const url = new URL(`${API_BASE}/v1/monitoring/export`);
  if (model && model !== 'all') url.searchParams.set('model', model);
  if (startTime) url.searchParams.set('start_time', startTime);
  if (endTime) url.searchParams.set('end_time', endTime);

  const res = await fetch(url.toString(), {
    headers: authHeaders(),
  });
  if (!res.ok) {
    throw new Error('Gagal mengunduh audit log CSV');
  }
  const blob = await res.blob();
  const blobUrl = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = blobUrl;
  a.download = `luco_audit_${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(blobUrl);
};

// --- Official Vault Documents APIs ---

export interface VaultDocumentSummary {
  path: string;
  title: string;
  category: string;
  category_id: string;
  summary: string;
  metadata?: Record<string, any>;
}

export interface VaultDocumentDetail extends VaultDocumentSummary {
  content: string;
}

export const fetchVaultDocuments = async (): Promise<VaultDocumentSummary[]> => {
  try {
    const res = await fetch(`${API_BASE}/v1/vault/documents`);
    if (!res.ok) return [];
    const data = await res.json();
    return data.documents || [];
  } catch (e) {
    console.error('Gagal mengambil daftar dokumen vault:', e);
    return [];
  }
};

export const fetchVaultDocument = async (path: string): Promise<VaultDocumentDetail> => {
  const clean = encodeURIComponent(path);
  const res = await fetch(`${API_BASE}/v1/vault/document?path=${clean}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Dokumen '${path}' tidak dapat dimuat`);
  }
  const data = await res.json();
  return data.document;
};

