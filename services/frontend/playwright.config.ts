import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright configuration for Lotus frontend e2e tests.
 *
 * Usage:
 *   npm run test:e2e          - run against an already-running frontend (default: http://localhost:3000)
 *   npm run test:e2e:ci       - same, intended for CI (headless by default)
 *
 * Environment variables:
 *   BASE_URL        - frontend URL (default: http://localhost:3000)
 *   AUTH_SECRET     - NextAuth secret, required for authenticated test sessions
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? [["github"], ["list"]] : "html",

  use: {
    baseURL: process.env.BASE_URL || "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  /* Do NOT start a webServer here — e2e tests expect the full stack
     (frontend + backend + postgres) to already be running, either
     locally via `make up` or in CI via docker-compose. */
});
