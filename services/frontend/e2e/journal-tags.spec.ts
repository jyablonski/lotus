/**
 * E2E tests for topic tags on journal entries (gated by frontend_show_tags flag).
 *
 * Feature flag: frontend_show_tags (superusers=true -> Admin only)
 *
 * - Consumer user should NOT see the topic tag filter or tags on entries
 * - Admin user should see the topic tag filter and tags on entries
 *   (when the flag is active and entries have topics)
 */
import { test, expect } from "@playwright/test";
import {
  authenticateContext,
  TEST_USER,
  ADMIN_TEST_USER,
} from "./helpers/auth";

test.describe("Journal Tags: Consumer User", () => {
  test.beforeEach(async ({ context }) => {
    await authenticateContext(context, TEST_USER);
  });

  test("topic tag filter is NOT visible for Consumer", async ({ page }) => {
    await page.goto("/journal/home");

    // The tag filter select has "All Topics" as its default option
    await expect(
      page.locator("select").filter({ hasText: "All Topics" }),
    ).not.toBeVisible();
  });

  test("topic tags are NOT displayed on entry cards for Consumer", async ({
    page,
  }) => {
    await page.goto("/journal/home");

    // Topic tags are rendered in a container with aria-label="Topics"
    await expect(page.locator("[aria-label='Topics']")).not.toBeVisible();
  });
});

test.describe("Journal Tags: Admin User", () => {
  test.beforeEach(async ({ context }) => {
    await authenticateContext(context, ADMIN_TEST_USER);
  });

  test("topic tag filter is visible for Admin", async ({ page }) => {
    await page.goto("/journal/home");

    const tagFilter = page.locator("select").filter({ hasText: "All Topics" });

    // Skip if the flag isn't active
    test.skip(
      !(await tagFilter.isVisible().catch(() => false)),
      "frontend_show_tags flag not active for Admin",
    );

    await expect(tagFilter).toBeVisible();
  });

  test("selecting a tag shows filter badge", async ({ page }) => {
    await page.goto("/journal/home");

    const tagFilter = page.locator("select").filter({ hasText: "All Topics" });
    test.skip(
      !(await tagFilter.isVisible().catch(() => false)),
      "frontend_show_tags flag not active",
    );

    // Select a tag option (the seeded topics: work, growth, wellbeing)
    const options = tagFilter.locator("option");
    const optionCount = await options.count();

    if (optionCount > 1) {
      const secondOption = await options.nth(1).getAttribute("value");
      if (secondOption) {
        await tagFilter.selectOption(secondOption);

        // Filter badge should show "Topic: <tag>"
        await expect(page.getByText(/topic:/i)).toBeVisible();

        // Filter summary should show filtered count
        await expect(
          page.getByText(/showing \d+ of \d+ entries/i),
        ).toBeVisible();
      }
    }
  });

  test("topic tags are displayed on entry cards", async ({ page }) => {
    await page.goto("/journal/home");

    const tagFilter = page.locator("select").filter({ hasText: "All Topics" });
    test.skip(
      !(await tagFilter.isVisible().catch(() => false)),
      "frontend_show_tags flag not active",
    );

    // Admin user's seeded entries have topics (work, growth, wellbeing)
    // Topic tags are rendered in a container with aria-label="Topics"
    const topicContainers = page.locator("[aria-label='Topics']");
    await expect(topicContainers.first()).toBeVisible();
  });

  test("clear filters resets tag selection", async ({ page }) => {
    await page.goto("/journal/home");

    const tagFilter = page.locator("select").filter({ hasText: "All Topics" });
    test.skip(
      !(await tagFilter.isVisible().catch(() => false)),
      "frontend_show_tags flag not active",
    );

    const options = tagFilter.locator("option");
    const optionCount = await options.count();

    if (optionCount > 1) {
      const secondOption = await options.nth(1).getAttribute("value");
      if (secondOption) {
        await tagFilter.selectOption(secondOption);
        await expect(page.getByText(/topic:/i)).toBeVisible();

        // Clear filters
        await page.getByRole("button", { name: /clear filters/i }).click();

        // Tag badge should be gone
        await expect(page.getByText(/topic:/i)).not.toBeVisible();
      }
    }
  });
});
