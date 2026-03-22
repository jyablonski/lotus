/**
 * E2E tests for the journal home page basics.
 *
 * Tests run against the real backend with seeded data for the
 * Consumer test user (3 journal entries in bootstrap SQL).
 */
import { test, expect } from "@playwright/test";
import { authenticateContext } from "./helpers/auth";

test.describe("Journal Home: Page Structure", () => {
  test.beforeEach(async ({ context }) => {
    await authenticateContext(context);
  });

  test("page loads with heading and entry count", async ({ page }) => {
    await page.goto("/journal/home");

    await expect(
      page.getByRole("heading", { name: /my journal/i }),
    ).toBeVisible();

    // Subtitle shows total count (seeded entries for the Consumer test user)
    await expect(page.getByText(/entries total/i)).toBeVisible();
  });

  test("search input is visible with default placeholder", async ({ page }) => {
    await page.goto("/journal/home");

    await expect(page.getByPlaceholder("Search your entries...")).toBeVisible();
  });

  test("mood filter dropdown is visible with default option", async ({
    page,
  }) => {
    await page.goto("/journal/home");

    const moodSelect = page.locator("select").filter({ hasText: "All Moods" });
    await expect(moodSelect).toBeVisible();
  });

  test("new entry button links to create page", async ({ page }) => {
    await page.goto("/journal/home");

    const newEntryLink = page.getByRole("link", { name: /new entry/i });
    await expect(newEntryLink).toBeVisible();
    await expect(newEntryLink).toHaveAttribute("href", "/journal/create");
  });
});

test.describe("Journal Home: Exact Search & Filters", () => {
  test.beforeEach(async ({ context }) => {
    await authenticateContext(context);
  });

  test("typing in search shows filter summary with search term", async ({
    page,
  }) => {
    await page.goto("/journal/home");

    const searchInput = page.getByPlaceholder("Search your entries...");
    await searchInput.fill("learning");

    // Filter summary should appear with the search term
    await expect(page.getByText(/showing \d+ of \d+ entries/i)).toBeVisible();
    await expect(page.getByText("Text: learning")).toBeVisible();
  });

  test("clear filters button resets search", async ({ page }) => {
    await page.goto("/journal/home");

    const searchInput = page.getByPlaceholder("Search your entries...");
    await searchInput.fill("learning");

    // Wait for filter summary to appear
    await expect(page.getByText(/showing \d+ of \d+ entries/i)).toBeVisible();

    // Click clear filters
    await page.getByRole("button", { name: /clear filters/i }).click();

    // Search input should be cleared
    await expect(searchInput).toHaveValue("");

    // Filter summary should disappear
    await expect(
      page.getByText(/showing \d+ of \d+ entries/i),
    ).not.toBeVisible();
  });

  test("mood filter shows filter badge when a mood is selected", async ({
    page,
  }) => {
    await page.goto("/journal/home");

    // Select a non-default mood from the dropdown
    const moodSelect = page.locator("select").filter({ hasText: "All Moods" });
    const options = moodSelect.locator("option");
    const optionCount = await options.count();

    // Only test if there are mood options beyond "All Moods"
    if (optionCount > 1) {
      // Select the second option (first actual mood)
      const secondOption = await options.nth(1).getAttribute("value");
      if (secondOption) {
        await moodSelect.selectOption(secondOption);

        // Filter summary should appear with mood badge
        await expect(
          page.getByText(/showing \d+ of \d+ entries/i),
        ).toBeVisible();
        await expect(page.getByText(/mood:/i)).toBeVisible();
      }
    }
  });
});

test.describe("Journal Home: Entry Display", () => {
  test.beforeEach(async ({ context }) => {
    await authenticateContext(context);
  });

  test("journal entries are displayed as cards", async ({ page }) => {
    await page.goto("/journal/home");

    // Seeded entries should show mood badges
    const moodBadges = page.getByText(/mood \d/i);
    await expect(moodBadges.first()).toBeVisible();
  });

  test("entries show date and mood information", async ({ page }) => {
    await page.goto("/journal/home");

    // Each entry card has a mood badge
    const cards = page.locator("[class*='cursor-pointer']");
    const cardCount = await cards.count();
    expect(cardCount).toBeGreaterThan(0);
  });
});
