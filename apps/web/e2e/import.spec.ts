import { expect, test } from "@playwright/test";

// bosque.txt: synthetic prose authored for this repository (T1C13, Art. IV.1-2, H6).
// It resembles no copyrighted work. Path is relative to the CWD Playwright runs from.
const FIXTURE_PATH = "e2e/fixtures/bosque.txt";

test("uploading a .txt file makes the frequency table visible", async ({ page }) => {
  await page.goto("/");

  await page.getByLabel("Archivo de texto (.txt)").setInputFiles(FIXTURE_PATH);
  await page.getByRole("button", { name: "Importar" }).click();

  await expect(page.getByRole("table")).toBeVisible();
  await expect(page.getByRole("cell", { name: "lobo" }).first()).toBeVisible();
});
