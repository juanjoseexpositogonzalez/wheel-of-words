import type { VocabularyResult } from "../types/vocabulary";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

interface VocabularyErrorResponse {
  error: { code: string; message: string };
}

async function parseOrThrow(response: Response): Promise<VocabularyResult> {
  if (!response.ok) {
    const errorBody = (await response.json()) as VocabularyErrorResponse;
    throw new Error(errorBody.error.message);
  }
  return response.json() as Promise<VocabularyResult>;
}

export async function getVocabulary(importId: number, pos?: string): Promise<VocabularyResult> {
  const query = pos === undefined ? "" : `?pos=${encodeURIComponent(pos)}`;
  const response = await fetch(`${apiBaseUrl}/api/v1/imports/${importId}/vocabulary${query}`);

  return parseOrThrow(response);
}
