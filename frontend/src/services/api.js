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

export async function inferImage(file, { applyBias = false } = {}) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("apply_bias", applyBias ? "true" : "false");
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

export async function inferVideo(file, onProgress) {
  const formData = new FormData();
  formData.append("file", file);
  const startResponse = await fetch(`${API_BASE_URL}/api/v1/infer/video`, {
    method: "POST",
    body: formData
  });
  if (!startResponse.ok) {
    const detail = await startResponse.text();
    throw new Error(detail || "Video inference failed");
  }
  const { job_id: jobId } = await startResponse.json();

  return new Promise((resolve, reject) => {
    const source = new EventSource(`${API_BASE_URL}/api/v1/infer/video/${jobId}/events`);
    source.onmessage = (event) => {
      let data;
      try {
        data = JSON.parse(event.data);
      } catch {
        return;
      }
      if (typeof onProgress === "function") {
        onProgress(data);
      }
      if (data.status === "done") {
        source.close();
        resolve({
          filename: data.filename,
          mode: data.mode,
          frames_processed: data.processed,
          annotated_video_url: data.annotated_video_url,
          sample_frames: []
        });
      } else if (data.status === "error") {
        source.close();
        reject(new Error(data.error || "Video processing failed"));
      }
    };
    source.onerror = () => {
      source.close();
      reject(new Error("Lost connection to progress stream"));
    };
  });
}
