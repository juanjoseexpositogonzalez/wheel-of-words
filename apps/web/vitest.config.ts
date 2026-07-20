import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// https://vitest.dev/config/
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test-setup.ts"],
    coverage: {
      provider: "v8",
      include: ["src/**"],
      exclude: ["src/test-setup.ts", "src/main.tsx"],
      // Coverage threshold is NOT enabled here — Slice D task TD03 activates it.
      // coverageThreshold: { lines: 70 }  ← enabled in Slice D
    },
  },
});
