import { afterEach, describe, expect, it, vi } from "vitest";
import { getVocabulary } from "../../src/api/vocabulary";
import type { VocabularyResult } from "../../src/types/vocabulary";

const result: VocabularyResult = {
  id: 7,
  group_count: 1,
  total_occurrence_count: 2,
  groups: [{ lemma: "run", pos: "VERB", occurrence_count: 2 }],
};

describe("getVocabulary", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("sends one GET request to the import vocabulary endpoint", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response(JSON.stringify(result), { status: 200 }));

    await expect(getVocabulary(7)).resolves.toEqual(result);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit | undefined];
    expect(url).toBe("http://localhost:8000/api/v1/imports/7/vocabulary");
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

    await expect(getVocabulary(999_999)).rejects.toThrow("La importación solicitada no existe.");
  });
});
