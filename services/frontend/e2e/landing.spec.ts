/**
 * E2E tests for the landing page (unauthenticated visitors).
 *
 * These tests do NOT require a running backend — the landing page
 * is entirely static and rendered for unauthenticated users.
 */
import { test, expect } from "@playwright/test";

test.describe("Landing Page", () => {
  test("shows the landing page for unauthenticated users", async ({ page }) => {
    await page.goto("/");

    // The main heading should be visible
    await expect(
      page.getByRole("heading", { name: /your thoughts/i }),
    ).toBeVisible();
  });

  test("displays the Lotus brand in the navbar", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByRole("link", { name: /lotus/i })).toBeVisible();
  });

  test("shows 'Start Your Journey' CTA linking to signin", async ({ page }) => {
    const cta = page.getByRole("link", { name: /start your journey/i });
    await page.goto("/");

    await expect(cta).toBeVisible();
    await expect(cta).toHaveAttribute("href", "/signin");
  });

  test("shows feature cards", async ({ page }) => {
    await page.goto("/");

    // The four feature titles from LandingPage.tsx
    const features = [
      "Simple Writing",
      "Daily Tracking",
      "Mood Insights",
      "Private & Secure",
    ];
    for (const feature of features) {
      await expect(page.getByText(feature)).toBeVisible();
    }
  });

  test("shows the Login link in the navbar for unauthenticated users", async ({
    page,
  }) => {
    await page.goto("/");

    // LoginButton renders a Link (anchor) containing "Login"
    await expect(page.getByRole("link", { name: /login/i })).toBeVisible();
  });

  test("footer shows copyright", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByText(/© 2026 Lotus/)).toBeVisible();
  });
});
