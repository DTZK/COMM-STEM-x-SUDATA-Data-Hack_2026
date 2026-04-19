const API_BASE = "http://localhost:8000";

export interface PredictRequest {
  category_id: number;
  days_to_trend: number;
  like_rate: number;
  comment_rate: number;
  tag_count: number;
  publish_hour: number;
  publish_dow: number;
}

export interface PredictResponse {
  archetype: string;
  confidence: number;
  timing: string;
  recommendation: string;
  color: string;
}

export interface CategoryItem {
  id: number;
  name: string;
}

export async function fetchCategories(): Promise<CategoryItem[]> {
  const res = await fetch(`${API_BASE}/categories`);
  if (!res.ok) throw new Error("Failed to fetch categories");
  return res.json();
}

export async function predict(payload: PredictRequest): Promise<PredictResponse> {
  const res = await fetch(`${API_BASE}/predict`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Prediction failed");
  }
  return res.json();
}

export async function scoreCsv(file: File): Promise<Blob> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/score-csv`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "CSV scoring failed");
  }
  return res.blob();
}