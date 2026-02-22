/**
 * E2E tests for authenticated pages.
 *
 * These tests inject a NextAuth session cookie to simulate a logged-in user.
 * They require:
 *   - The frontend running at BASE_URL (default: http://localhost:3000)
 *   - The backend running at the configured BACKEND_URL
 *   - PostgreSQL with the test user seeded (or the backend returning
 *     empty data gracefully)
 *   - AUTH_SECRET env var matching the frontend's secret
 */
import { test, expect } from "@playwright/test";
import { authenticateContext, TEST_USER } from "./helpers/auth";

test.describe("Authenticated: Dashboard", () => {
  test.beforeEach(async ({ context }) => {
    await authenticateContext(context);
  });

  test("shows the dashboard for authenticated users (not landing page)", async ({
    page,
  }) => {
    await page.goto("/");

    // Should see the welcome greeting, NOT the landing page heading
    await expect(
      page.getByRole("heading", { name: /welcome back/i }),
    ).toBeVisible();

    // Landing page heading should NOT be present
    await expect(
      page.getByRole("heading", { name: /your thoughts/i }),
    ).not.toBeVisible();
  });

  test("dashboard displays stat cards", async ({ page }) => {
    await page.goto("/");

    // The four stat card titles from LoggedInDashboard.tsx
    const statTitles = [
      "Last 30 Days",
      "Current Streak",
      "Mood Trend",
      "Total Entries",
    ];
    for (const title of statTitles) {
      await expect(page.getByText(title)).toBeVisible();
    }
  });

  test("dashboard has a 'New Entry' button linking to create page", async ({
    page,
  }) => {
    await page.goto("/");

    const newEntryLink = page.getByRole("link", { name: /new entry/i });
    await expect(newEntryLink).toBeVisible();
    await expect(newEntryLink).toHaveAttribute("href", "/journal/create");
  });

  test("dashboard shows quick action links", async ({ page }) => {
    await page.goto("/");

    await expect(
      page.getByRole("link", { name: /view calendar/i }),
    ).toBeVisible();
    await expect(page.getByRole("link", { name: /settings/i })).toBeVisible();
  });
});

test.describe("Authenticated: Navigation", () => {
  test.beforeEach(async ({ context }) => {
    await authenticateContext(context);
  });

  test("navbar shows navigation links for authenticated users", async ({
    page,
  }) => {
    await page.goto("/");

    // Desktop nav links
    await expect(
      page.getByRole("link", { name: "Home" }).first(),
    ).toBeVisible();
    await expect(
      page.getByRole("link", { name: "Journal" }).first(),
    ).toBeVisible();
    await expect(
      page.getByRole("link", { name: "Calendar" }).first(),
    ).toBeVisible();
  });

  test("can navigate to journal home page", async ({ page }) => {
    await page.goto("/");

    await page.getByRole("link", { name: "Journal" }).first().click();
    await page.waitForURL("**/journal/home");

    // Journal home page should show the journal header or list
    await expect(page.locator("body")).toContainText(/journal/i);
  });

  test("can navigate to calendar page", async ({ page }) => {
    await page.goto("/");

    await page.getByRole("link", { name: "Calendar" }).first().click();
    await page.waitForURL("**/journal/calendar");

    // Calendar page should show weekday headers
    await expect(page.getByText("Mon")).toBeVisible();
  });
});

test.describe("Authenticated: Journal Create", () => {
  test.beforeEach(async ({ context }) => {
    await authenticateContext(context);
  });

  test("journal create page loads with the form", async ({ page }) => {
    await page.goto("/journal/create");

    // Should see the text editor placeholder or the mood selector
    await expect(page.getByPlaceholder(/write your thoughts/i)).toBeVisible();
  });

  test("journal create page shows mood selector", async ({ page }) => {
    await page.goto("/journal/create");

    // Mood selector buttons (at least one mood option should be visible)
    await expect(page.getByText(/happy/i)).toBeVisible();
  });
});

test.describe("Authenticated: Profile", () => {
  test.beforeEach(async ({ context }) => {
    await authenticateContext(context);
  });

  test("profile page loads with user info", async ({ page }) => {
    await page.goto("/profile");

    // Should see the test user's name
    await expect(page.getByText(TEST_USER.name)).toBeVisible();
  });

  test("profile page shows stat cards", async ({ page }) => {
    await page.goto("/profile");

    // Profile stats include these titles
    await expect(page.getByText("Total Entries")).toBeVisible();
  });
});
