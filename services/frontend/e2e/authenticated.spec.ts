// These tests inject a NextAuth session cookie to simulate a logged-in user.
// They require:
//   - Frontend running at BASE_URL (default: http://localhost:3000)
//   - Backend running at the configured BACKEND_URL
//   - Postgres with the test user seeded (or backend returning empty data gracefully)
//   - AUTH_SECRET env var matching the frontend's secret
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

    await expect(
      page.getByRole("heading", { name: /welcome back/i }),
    ).toBeVisible();
    await expect(
      page.getByRole("heading", { name: /your thoughts/i }),
    ).not.toBeVisible();
  });

  test("dashboard displays stat cards", async ({ page }) => {
    await page.goto("/");

    await expect(page.getByText("Last 30 Days")).toBeVisible();
    await expect(
      page.getByText("Current Streak", { exact: true }),
    ).toBeVisible();
    await expect(page.getByText("Mood Trend")).toBeVisible();
    await expect(page.getByText("Total Entries").first()).toBeVisible();
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

    await expect(page.locator("body")).toContainText(/journal/i);
  });

  test("can navigate to calendar page", async ({ page }) => {
    await page.goto("/");

    await page.getByRole("link", { name: "Calendar" }).first().click();
    await page.waitForURL("**/journal/calendar");

    await expect(page.getByText("Mon", { exact: true })).toBeVisible();
  });
});

test.describe("Authenticated: Journal Create", () => {
  test.beforeEach(async ({ context }) => {
    await authenticateContext(context);
  });

  test("journal create page loads with the form", async ({ page }) => {
    await page.goto("/journal/create");

    await expect(page.getByPlaceholder(/what's on your mind/i)).toBeVisible();
  });

  test("journal create page shows mood slider", async ({ page }) => {
    await page.goto("/journal/create");

    await expect(
      page.getByText(/how are you feeling\? \(1-10\)/i),
    ).toBeVisible();
    await expect(page.getByRole("slider")).toBeVisible();
  });
});

test.describe("Authenticated: Profile", () => {
  test.beforeEach(async ({ context }) => {
    await authenticateContext(context);
  });

  test("profile page loads with user info", async ({ page }) => {
    await page.goto("/profile");

    await expect(page.getByText(TEST_USER.name)).toBeVisible();
  });

  test("profile page shows stat cards", async ({ page }) => {
    await page.goto("/profile");

    await expect(page.getByText("Total Entries")).toBeVisible();
  });
});
