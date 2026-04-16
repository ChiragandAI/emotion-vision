import { compressImageFile } from "./compress";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export function getApiBaseUrl() {
  return API_BASE_URL;
}

export async function getHealth() {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error("Health check failed");
  }
  return response.json();
}

export async function getDemoInfo() {
  const response = await fetch(`${API_BASE_URL}/api/v1/demo`);
  if (!response.ok) {
    throw new Error("Demo info request failed");
  }
  return response.json();
}

export async function inferImage(file) {
  const prepared = await compressImageFile(file);
  const formData = new FormData();
  formData.append("file", prepared);
  const response = await fetch(`${API_BASE_URL}/api/v1/infer/image`, {
    method: "POST",
    body: formData
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "Image inference failed");
  }
  return response.json();
}

export async function inferVideo(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE_URL}/api/v1/infer/video`, {
    method: "POST",
    body: formData
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || "Video inference failed");
  }
  return response.json();
}
