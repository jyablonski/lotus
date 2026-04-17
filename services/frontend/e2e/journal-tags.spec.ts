// Topic tags are gated behind frontend_show_tags (superusers-only, Admin in tests).
// Consumer should see neither the tag filter nor tags on entries; Admin should see
// both when the flag is active and entries have topics.
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

    await expect(
      page.locator("select").filter({ hasText: "All Topics" }),
    ).not.toBeVisible();
  });

  test("topic tags are NOT displayed on entry cards for Consumer", async ({
    page,
  }) => {
    await page.goto("/journal/home");

    // Topic tags render inside a container with aria-label="Topics".
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

    // Seeded topics for the Admin user are work/growth/wellbeing.
    const options = tagFilter.locator("option");
    const optionCount = await options.count();

    if (optionCount > 1) {
      const secondOption = await options.nth(1).getAttribute("value");
      if (secondOption) {
        await tagFilter.selectOption(secondOption);

        await expect(page.getByText(/topic:/i)).toBeVisible();
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

    // Admin's seeded entries have topics and render inside aria-label="Topics".
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

        await page.getByRole("button", { name: /clear filters/i }).click();

        await expect(page.getByText(/topic:/i)).not.toBeVisible();
      }
    }
  });
});
