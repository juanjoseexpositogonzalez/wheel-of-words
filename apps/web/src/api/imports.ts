import type { ImportResult } from "../types/imports";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

interface ImportErrorResponse {
  error: { code: string; message: string };
}

export async function postImport(file: File): Promise<ImportResult> {
  const body = new FormData();
  body.append("file", file);

  const response = await fetch(`${apiBaseUrl}/api/v1/imports`, {
    method: "POST",
    body,
  });

  if (!response.ok) {
    const errorBody = (await response.json()) as ImportErrorResponse;
    throw new Error(errorBody.error.message);
  }

  return response.json() as Promise<ImportResult>;
}

export async function deleteImport(id: number): Promise<void> {
  const response = await fetch(`${apiBaseUrl}/api/v1/imports/${id}`, {
    method: "DELETE",
  });

  if (!response.ok) {
    const errorBody = (await response.json()) as ImportErrorResponse;
    throw new Error(errorBody.error.message);
  }
}
