import { defineConfig, devices } from "@playwright/test";

declare const process: { env: Record<string, string | undefined> };

export default defineConfig({
  testDir: "./e2e",
  use: {
    baseURL: "http://127.0.0.1:5173",
    screenshot: "only-on-failure",
    trace: "on-first-retry",
    video: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      // Playwright uses POSIX sh, where `exec -a` is unavailable. This label is
      // exported to the spawned backend while PORT keeps E2E off the dev port.
      command:
        "cd ../.. && WHEEL_PROCESS_NAME=wheel-vocabulary-e2e-api PORT=8010 make dev-backend",
      url: "http://127.0.0.1:8010/api/v1/health",
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
    {
      command: "VITE_API_BASE_URL=http://127.0.0.1:8010 pnpm exec vite --host 127.0.0.1",
      url: "http://127.0.0.1:5173",
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
  ],
});
