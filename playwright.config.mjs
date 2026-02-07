import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 30_000,
  expect: {
    timeout: 7_500,
  },
  fullyParallel: true,
  reporter: [["list"], ["html", { open: "never" }]],
  projects: [
    { name: "chromium-light", use: { colorScheme: "light" } },
    { name: "chromium-dark", use: { colorScheme: "dark" } },
  ],
  use: {
    baseURL: process.env.E2E_BASE_URL || "http://127.0.0.1:8788",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  webServer: {
    command: "python3 -m http.server 8788 --directory site",
    url: "http://127.0.0.1:8788",
    reuseExistingServer: !process.env.CI,
    timeout: 30_000,
  },
});
