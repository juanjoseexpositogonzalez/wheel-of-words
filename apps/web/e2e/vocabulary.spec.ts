import { expect, test } from "@playwright/test";

const FIXTURE_PATH = "e2e/fixtures/bosque.txt";

test("import, annotate, and view grouped vocabulary with occurrence counts", async ({ page }) => {
  await page.goto("/");

  await page.getByLabel("Archivo de texto (.txt)").setInputFiles(FIXTURE_PATH);
  await page.getByRole("button", { name: "Importar" }).click();
  await expect(page.getByRole("table")).toHaveCount(1);

  await page.getByRole("button", { name: "Anotar" }).click();
  await expect(page.getByRole("table")).toHaveCount(2);

  await page.getByRole("button", { name: "Ver vocabulario" }).click();
  const vocabularyTable = page.getByRole("table", { name: /vocabulario agrupado/i });
  await expect(vocabularyTable).toBeVisible();
  await expect(vocabularyTable.getByRole("columnheader", { name: "Apariciones" })).toBeVisible();
  await expect(vocabularyTable.getByRole("cell", { name: "1" }).first()).toBeVisible();
});
