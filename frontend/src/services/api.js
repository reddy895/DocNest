/**
 * DocNest API Client
 * Centralized REST communication layer with FastAPI backend.
 */

export async function fetchHealth() {
  const res = await fetch('/api/health');
  if (!res.ok) throw new Error('Health check request failed');
  return res.json();
}

export async function fetchDocuments() {
  const res = await fetch('/api/documents');
  if (!res.ok) throw new Error('Failed to fetch document listing');
  return res.json();
}

export async function fetchDocumentById(docId) {
  const res = await fetch(`/api/documents/${docId}`);
  if (!res.ok) throw new Error(`Failed to fetch document ${docId}`);
  return res.json();
}

export async function deleteDocumentById(docId) {
  const res = await fetch(`/api/documents/${docId}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Failed to delete document ${docId}`);
  }
  return res.json();
}

export async function uploadDocumentFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch('/api/documents/upload', {
    method: 'POST',
    body: formData,
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || 'Upload failed');
  }
  return data;
}

export async function sendChatQuery({
  question,
  docId = null,
  topK = 4,
  similarityThreshold = 0.25,
}) {
  const res = await fetch('/api/chat/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      doc_id: docId,
      top_k: topK,
      similarity_threshold: similarityThreshold,
    }),
  });

  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || 'Query execution failed');
  }
  return data;
}

export async function fetchChatSuggestions(docId = null) {
  const url = docId
    ? `/api/chat/suggestions?doc_id=${docId}`
    : '/api/chat/suggestions';
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch suggestions');
  return res.json();
}
