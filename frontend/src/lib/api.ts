import type {
  ApiErrorDetail,
  CatalogResponse,
  CompareRequestBody,
  CompareResponse,
  ContextRequestBody,
  ContextResponse,
  CropReference,
  DemoResponse,
  MonthlyClimateResponse,
  ResolvedLocation,
} from "./types";

// Same-origin by default: the Vite dev server proxies /api, and FastAPI can serve the built app.
const BASE = String(import.meta.env.VITE_API_BASE ?? "").replace(/\/$/, "");

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: ApiErrorDetail[];

  constructor(status: number, code: string, message: string, details: ApiErrorDetail[] = []) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.details = details;
  }

  /** The service answered but rejected the input, as opposed to being unreachable. */
  get isInputError() {
    return this.status === 422 || this.status === 413;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(BASE + path, {
      ...init,
      headers: { Accept: "application/json", ...(init.body ? { "Content-Type": "application/json" } : {}) },
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new ApiError(0, "network_error", "Layanan FieldShift tidak dapat dihubungi.");
  }
  if (!response.ok) {
    let code = "http_error";
    let message = "Data belum dapat dimuat.";
    let details: ApiErrorDetail[] = [];
    try {
      const body = await response.json();
      if (body?.error) {
        code = body.error.code ?? code;
        message = body.error.message ?? message;
        details = Array.isArray(body.error.details) ? body.error.details : [];
      }
    } catch {
      // Non-JSON error bodies keep the generic message.
    }
    throw new ApiError(response.status, code, message, details);
  }
  return (await response.json()) as T;
}

const post = (body: unknown, signal?: AbortSignal): RequestInit => ({
  method: "POST",
  body: JSON.stringify(body),
  signal,
});

export const api = {
  locations: (signal?: AbortSignal) => request<{ locations: ResolvedLocation[] }>("/api/v1/locations", { signal }),
  crops: (signal?: AbortSignal) => request<{ crops: CropReference[] }>("/api/v1/crops", { signal }),
  catalog: (signal?: AbortSignal) => request<CatalogResponse>("/api/v1/catalog", { signal }),
  context: (body: ContextRequestBody, signal?: AbortSignal) => request<ContextResponse>("/api/v1/context", post(body, signal)),
  monthlyClimate: (body: ContextRequestBody, signal?: AbortSignal) =>
    request<MonthlyClimateResponse>("/api/v1/climate/monthly", post(body, signal)),
  compare: (body: CompareRequestBody, signal?: AbortSignal) => request<CompareResponse>("/api/v1/compare", post(body, signal)),
  demo: (signal?: AbortSignal) => request<DemoResponse>("/api/v1/demo", { signal }),
};

export function isAbort(error: unknown) {
  return error instanceof DOMException && error.name === "AbortError";
}
