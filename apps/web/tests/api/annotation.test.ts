import { afterEach, describe, expect, it, vi } from "vitest";
import { getAnnotation, postAnnotation } from "../../src/api/annotation";
import type { AnnotationResult } from "../../src/types/annotation";

const result: AnnotationResult = {
  id: 7,
  provenance: {
    source: "spacy",
    model_name: "en_core_web_sm",
    model_version: "3.8.0",
    language: "en",
    processed_at: "2026-08-24T09:00:00",
  },
  occurrences: [
    {
      position: 0,
      raw_text: "ran",
      pos: "VERB",
      pos_origin: "automatic",
      automatic_pos: "VERB",
      pos_confidence: 0.98,
      lemma: "run",
      lemma_origin: "automatic",
      automatic_lemma: "run",
      lemma_confidence: null,
    },
  ],
};

describe("postAnnotation", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("posts to the import's annotation endpoint and parses the result", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response(JSON.stringify(result), { status: 201 }));

    await expect(postAnnotation(7)).resolves.toEqual(result);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("http://localhost:8000/api/v1/imports/7/annotation");
    expect(init.method).toBe("POST");
  });

  it("rejects with the backend error message on failure", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          error: { code: "UNSUPPORTED_LANGUAGE", message: "No hay un analizador instalado." },
        }),
        { status: 422 },
      ),
    );

    await expect(postAnnotation(7)).rejects.toThrow("No hay un analizador instalado.");
  });
});

describe("getAnnotation", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("sends a GET request to the import's annotation endpoint", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response(JSON.stringify(result), { status: 200 }));

    await expect(getAnnotation(7)).resolves.toEqual(result);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit | undefined];
    expect(url).toBe("http://localhost:8000/api/v1/imports/7/annotation");
    expect(init?.method ?? "GET").toBe("GET");
  });

  it("rejects with the backend error message when the import is unknown", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          error: { code: "IMPORT_NOT_FOUND", message: "La importación solicitada no existe." },
        }),
        { status: 404 },
      ),
    );

    await expect(getAnnotation(999_999)).rejects.toThrow("La importación solicitada no existe.");
  });
});
