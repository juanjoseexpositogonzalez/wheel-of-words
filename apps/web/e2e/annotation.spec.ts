import { expect, test } from "@playwright/test";

// bosque.txt: synthetic prose authored for this repository (T1C13, Art. IV.1-2, H6).
// Reused from the import E2E spec — same fixture, same provenance. The
// content is Spanish; the installed analyzer is English-only
// (`Settings.annotation_language = "en"`, REQ-003-003) — this test proves
// the wiring end to end, not linguistic accuracy on foreign-language input.
const FIXTURE_PATH = "e2e/fixtures/bosque.txt";

test("import, annotate, table shows lemma/pos/confidence per occurrence", async ({ page }) => {
  await page.goto("/");

  await page.getByLabel("Archivo de texto (.txt)").setInputFiles(FIXTURE_PATH);
  await page.getByRole("button", { name: "Importar" }).click();
  await expect(page.getByRole("table")).toBeVisible();

  await page.getByRole("button", { name: "Anotar" }).click();

  // A second table appears — the annotation table — carrying real
  // per-occurrence pos/lemma/confidence values (REQ-003-018, REQ-003-009).
  await expect(page.getByRole("table")).toHaveCount(2);
  const annotationTable = page.getByRole("table").nth(1);
  await expect(annotationTable).toBeVisible();
  await expect(annotationTable.getByRole("cell", { name: "lobo" }).first()).toBeVisible();
});
