import { expect, test } from "@playwright/test";

// bosque.txt: synthetic prose authored for this repository (T1C13, Art. IV.1-2, H6).
// Reused from the import E2E spec — same fixture, same provenance.
const FIXTURE_PATH = "e2e/fixtures/bosque.txt";

test("import, delete with confirmation, table disappears", async ({ page }) => {
  await page.goto("/");

  await page.getByLabel("Archivo de texto (.txt)").setInputFiles(FIXTURE_PATH);
  await page.getByRole("button", { name: "Importar" }).click();
  await expect(page.getByRole("table")).toBeVisible();

  // One activation shows a confirmation control; the table must still be
  // present until the user actually confirms (AC-002-16).
  await page.getByRole("button", { name: /eliminar/i }).click();
  await expect(page.getByRole("table")).toBeVisible();

  await page.getByRole("button", { name: /confirmar/i }).click();

  // The table and the delete control are both gone — the page returns to its
  // pre-import state, ready to import again.
  await expect(page.getByRole("table")).not.toBeVisible();
  await expect(page.getByRole("button", { name: /eliminar/i })).not.toBeVisible();
});
