import { afterEach, describe, expect, it, vi } from "vitest";
import { deleteImport, postImport } from "../../src/api/imports";
import type { ImportResult } from "../../src/types/imports";

function makeFile(name: string, content: string): File {
  return new File([content], name, { type: "text/plain" });
}

const result: ImportResult = {
  id: 1,
  import_status: "succeeded",
  distinct_form_count: 2,
  total_token_count: 3,
  forms: [
    { normalized_form: "corres", display_form: "corres", frequency: 1 },
    { normalized_form: "corro", display_form: "corro", frequency: 2 },
  ],
};

describe("postImport", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("posts the file as multipart form data and parses the ordered result", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response(JSON.stringify(result), { status: 201 }));
    const file = makeFile("muestra.txt", "corro corro corres");

    await expect(postImport(file)).resolves.toEqual(result);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("http://localhost:8000/api/v1/imports");
    expect(init.method).toBe("POST");
    const body = init.body as FormData;
    expect(body.get("file")).toBe(file);
  });

  it("rejects with the backend error message on failure", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          error: { code: "INVALID_FILE_TYPE", message: "Solo se admiten archivos .txt." },
        }),
        { status: 422 },
      ),
    );

    await expect(postImport(makeFile("notes.pdf", "x"))).rejects.toThrow(
      "Solo se admiten archivos .txt.",
    );
  });
});

describe("deleteImport", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("sends a DELETE request to the import's own endpoint", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response(null, { status: 204 }));

    await expect(deleteImport(1)).resolves.toBeUndefined();

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe("http://localhost:8000/api/v1/imports/1");
    expect(init.method).toBe("DELETE");
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

    await expect(deleteImport(999_999)).rejects.toThrow("La importación solicitada no existe.");
  });
});
