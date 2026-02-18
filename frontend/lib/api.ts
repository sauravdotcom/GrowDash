import { AnalyticsResponse, CopilotRequest, CopilotResponse, UploadResponse } from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:7000/api/v1";

async function parseResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const detail = payload?.detail || `Request failed with status ${response.status}`;
    throw new Error(detail);
  }

  return response.json() as Promise<T>;
}

async function safeFetch(url: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(url, init);
  } catch (err) {
    const primaryReason = err instanceof Error ? err.message : "Unknown network error";
    const fallbackUrl = getLoopbackFallbackUrl(url);

    if (fallbackUrl) {
      try {
        return await fetch(fallbackUrl, init);
      } catch (fallbackErr) {
        const fallbackReason =
          fallbackErr instanceof Error ? fallbackErr.message : "Unknown network error";
        throw new Error(
          `Cannot reach API at ${url} (${primaryReason}) or ${fallbackUrl} (${fallbackReason}). ` +
            "Check backend on port 7000 and CORS origin."
        );
      }
    }

    throw new Error(
      `Cannot reach API at ${url}. ${primaryReason}. Check backend on port 7000 and CORS origin.`
    );
  }
}

function getLoopbackFallbackUrl(url: string): string | null {
  try {
    const parsed = new URL(url);
    if (parsed.hostname === "localhost") {
      parsed.hostname = "127.0.0.1";
      return parsed.toString();
    }
    if (parsed.hostname === "127.0.0.1") {
      parsed.hostname = "localhost";
      return parsed.toString();
    }
    return null;
  } catch {
    return null;
  }
}

export async function fetchAnalytics(): Promise<AnalyticsResponse> {
  const response = await safeFetch(`${API_BASE_URL}/analytics`, {
    cache: "no-store"
  });
  return parseResponse<AnalyticsResponse>(response);
}

export async function uploadTradebook(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await safeFetch(`${API_BASE_URL}/trades/upload`, {
    method: "POST",
    body: formData
  });

  return parseResponse<UploadResponse>(response);
}

export async function fetchCopilotAdvice(payload: CopilotRequest): Promise<CopilotResponse> {
  const response = await safeFetch(`${API_BASE_URL}/ai/copilot`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  return parseResponse<CopilotResponse>(response);
}
