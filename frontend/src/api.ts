export type TaskType =
  | "classification"
  | "regression"
  | "clustering"
  | "anomaly_detection";
export type Variant = "base" | "optimized";

export interface MLBackendStatus {
  available: boolean;
  package: string;
  detail: string;
}

export interface HealthResponse {
  status: "ok";
  ml_backend: MLBackendStatus;
}

export interface ModelSpec {
  id: string;
  name: string;
  task_type: TaskType;
  variants: Variant[];
  parameters: Record<string, unknown>;
}

export interface DatasetSpec {
  id: string;
  name: string;
  task_type: TaskType;
}

export interface ExperimentConfig {
  model: string;
  variant: Variant;
  dataset: string;
  params: Record<string, unknown>;
  test_size: number;
  random_state: number;
}

export interface ExperimentResult {
  model: string;
  variant: Variant;
  dataset: string;
  metrics: Record<string, number>;
  diagnostics: Record<string, unknown>;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as
      | { detail?: { message?: string } | string }
      | null;
    const detail = payload?.detail;
    const message =
      typeof detail === "string" ? detail : detail?.message ?? response.statusText;
    throw new Error(message);
  }
  return (await response.json()) as T;
}

export const api = {
  health: () => request<HealthResponse>("/api/health"),
  models: () => request<ModelSpec[]>("/api/models"),
  datasets: () => request<DatasetSpec[]>("/api/datasets"),
  runExperiment: (config: ExperimentConfig) =>
    request<ExperimentResult>("/api/experiments", {
      method: "POST",
      body: JSON.stringify(config),
    }),
};
