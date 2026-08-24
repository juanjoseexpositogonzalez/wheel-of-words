import type { AnnotationResult } from "../types/annotation";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

interface AnnotationErrorResponse {
  error: { code: string; message: string };
}

async function parseOrThrow(response: Response): Promise<AnnotationResult> {
  if (!response.ok) {
    const errorBody = (await response.json()) as AnnotationErrorResponse;
    throw new Error(errorBody.error.message);
  }
  return response.json() as Promise<AnnotationResult>;
}

export async function postAnnotation(importId: number): Promise<AnnotationResult> {
  const response = await fetch(`${apiBaseUrl}/api/v1/imports/${importId}/annotation`, {
    method: "POST",
  });

  return parseOrThrow(response);
}

export async function getAnnotation(importId: number): Promise<AnnotationResult> {
  const response = await fetch(`${apiBaseUrl}/api/v1/imports/${importId}/annotation`);

  return parseOrThrow(response);
}
