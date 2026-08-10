import { expect, test } from "@playwright/test";

test("shows that the backend is available", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("heading", { name: "Wheel Vocabulary" })).toBeVisible();
  await expect(page.getByText("Backend disponible")).toBeVisible();
  await expect(page.getByText("wheel-vocabulary-api · 0.1.0")).toBeVisible();
});
