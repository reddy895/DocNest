/**
 * DocNest Production API Client
 * Centralized REST and SSE communication layer with automatic JWT injection.
 */

const TOKEN_KEY = 'docnest_auth_token';

export function getAuthToken() {
  return localStorage.getItem(TOKEN_KEY) || '';
}

export function setAuthToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

function getHeaders(contentType = 'application/json') {
  const headers = {};
  if (contentType) headers['Content-Type'] = contentType;
  const token = getAuthToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

// ---------------- AUTHENTICATION ----------------
export async function loginUser(email, password) {
  const res = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Login failed. Please check credentials.');
  }
  const data = await res.json();
  if (data.access_token) setAuthToken(data.access_token);
  return data;
}

export async function registerUser({ email, username, password, workspace_name }) {
  const res = await fetch('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, username, password, workspace_name }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Registration failed.');
  }
  const data = await res.json();
  if (data.access_token) setAuthToken(data.access_token);
  return data;
}

export async function fetchCurrentUser() {
  const res = await fetch('/api/auth/me', { headers: getHeaders() });
  if (!res.ok) throw new Error('Unauthenticated');
  return res.json();
}

// ---------------- SYSTEM & TELEMETRY ----------------
export async function fetchHealth() {
  const res = await fetch('/api/system/health', { headers: getHeaders() });
  if (!res.ok) throw new Error('Health check request failed');
  return res.json();
}

export async function fetchDashboardStats() {
  const res = await fetch('/api/system/dashboard-stats', { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch dashboard statistics');
  return res.json();
}

export async function fetchUserSettings() {
  const res = await fetch('/api/settings', { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch user settings');
  return res.json();
}

export async function updateUserSettings(settings) {
  const res = await fetch('/api/settings', {
    method: 'PUT',
    headers: getHeaders(),
    body: JSON.stringify(settings),
  });
  if (!res.ok) throw new Error('Failed to update pipeline settings');
  return res.json();
}

// ---------------- DOCUMENTS & SAMPLES ----------------
export async function fetchDocuments() {
  const res = await fetch('/api/documents', { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch document listing');
  return res.json();
}

export async function fetchDocumentById(docId) {
  const res = await fetch(`/api/documents/${docId}`, { headers: getHeaders() });
  if (!res.ok) throw new Error(`Failed to fetch document ${docId}`);
  return res.json();
}

export async function fetchDocumentStatus(docId) {
  const res = await fetch(`/api/documents/${docId}/status`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to poll status');
  return res.json();
}

export async function loadSampleDocuments(sampleType = 'all') {
  const res = await fetch(`/api/documents/load-sample?sample_type=${sampleType}`, {
    method: 'POST',
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error('Failed to load sample documents');
  return res.json();
}

export async function uploadDocumentFile(file, asyncProcessing = false) {
  const formData = new FormData();
  formData.append('file', file);

  const token = getAuthToken();
  const headers = {};
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`/api/documents/upload?async_processing=${asyncProcessing}`, {
    method: 'POST',
    headers,
    body: formData,
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || 'Upload failed');
  }
  return data;
}

export async function updateDocumentMetadata(docId, updateData) {
  const res = await fetch(`/api/documents/${docId}`, {
    method: 'PATCH',
    headers: getHeaders(),
    body: JSON.stringify(updateData),
  });
  if (!res.ok) throw new Error('Failed to update document metadata');
  return res.json();
}

export async function reindexDocument(docId) {
  const res = await fetch(`/api/documents/${docId}/reindex`, {
    method: 'POST',
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error('Failed to trigger re-indexing');
  return res.json();
}

export async function deleteDocumentById(docId) {
  const res = await fetch(`/api/documents/${docId}`, {
    method: 'DELETE',
    headers: getHeaders(),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to delete document ${docId}`);
  }
  return res.json();
}

// ---------------- SESSIONS & MESSAGES ----------------
export async function fetchChatSessions() {
  const res = await fetch('/api/chat/sessions', { headers: getHeaders() });
  if (!res.ok) return [];
  return res.json();
}

export async function createChatSession(title = 'New Conversation') {
  const res = await fetch('/api/chat/sessions', {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error('Failed to create chat session');
  return res.json();
}

export async function fetchSessionMessages(sessionId) {
  const res = await fetch(`/api/chat/sessions/${sessionId}/messages`, { headers: getHeaders() });
  if (!res.ok) return [];
  return res.json();
}

export async function updateChatSession(sessionId, updateData) {
  const res = await fetch(`/api/chat/sessions/${sessionId}`, {
    method: 'PATCH',
    headers: getHeaders(),
    body: JSON.stringify(updateData),
  });
  if (!res.ok) throw new Error('Failed to update session');
  return res.json();
}

export async function deleteChatSession(sessionId) {
  const res = await fetch(`/api/chat/sessions/${sessionId}`, {
    method: 'DELETE',
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error('Failed to delete chat session');
  return res.json();
}

export async function recordMessageFeedback(messageId, rating, comment = '') {
  const res = await fetch(`/api/chat/${messageId}/feedback`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify({ rating, comment }),
  });
  if (!res.ok) throw new Error('Failed to record feedback');
  return res.json();
}

// ---------------- EVALUATION RUNS ----------------
export async function fetchEvalRuns() {
  const res = await fetch('/api/eval/runs', { headers: getHeaders() });
  if (!res.ok) return [];
  return res.json();
}

export async function triggerEvalRun(maxCases = 3) {
  const res = await fetch(`/api/eval/run?max_cases=${maxCases}`, {
    method: 'POST',
    headers: getHeaders(),
  });
  if (!res.ok) throw new Error('Evaluation run failed');
  return res.json();
}

export async function fetchEvalRunDetail(runId) {
  const res = await fetch(`/api/eval/runs/${runId}`, { headers: getHeaders() });
  if (!res.ok) throw new Error('Failed to fetch evaluation run details');
  return res.json();
}
