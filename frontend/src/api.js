const API_BASE = window.SMRTI_API_BASE || "";

export async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (response.status === 204) return null;
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || "Request failed");
  return data;
}

export function friendlyError(error) {
  const message = error.message || "Request failed";
  if (message.includes("Supermemory Local rejected")) {
    return "Start supermemory-server from this project folder, then retry.";
  }
  if (message.includes("Supermemory rejected")) {
    return "Check your Supermemory mode and API key in .env, then retry.";
  }
  if (message.toLowerCase().includes("groq")) {
    return "Check Groq credentials in your .env file.";
  }
  return message;
}

export const api = {
  status: () => request("/status"),
  memoryCheck: () => request("/status/memory-check", { method: "POST" }),
  preview: (body) => request("/ingest/preview", jsonPost(body)),
  previewDocument: (formData) => request("/documents/preview", { method: "POST", body: formData }),
  saveMemories: (memories) => request("/memories", jsonPost({ memories })),
  listMemories: (persona, subjectId, limit = 50) => request(`/memories?persona=${persona}&limit=${limit}${subjectId ? `&subject_id=${encodeURIComponent(subjectId)}` : ""}`),
  updateMemory: (id, body) => request(`/memories/${id}`, jsonPatch(body)),
  deleteMemory: (id) => request(`/memories/${id}`, { method: "DELETE" }),
  ask: (body) => request("/ask", jsonPost(body)),
  summary: (body) => request("/summary", jsonPost(body)),
  evalRetrieval: (body) => request("/retrieval/evaluate", jsonPost(body)),
  loadDemo: () => request("/demo/load", { method: "POST" }),
  transcribe: (formData) => request("/voice/transcribe", { method: "POST", body: formData }),
};

function jsonPost(body) {
  return {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
}

function jsonPatch(body) {
  return {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  };
}
