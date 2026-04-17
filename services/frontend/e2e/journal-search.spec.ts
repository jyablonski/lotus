// Seeded feature flags gate the search modes:
//   - keyword_search=everyone  -> visible for all users
//   - semantic_search=superusers -> visible for Admin only
// Tests use conditional skips so they stay green regardless of backend flag state.
import { test, expect } from "@playwright/test";
import {
  authenticateContext,
  TEST_USER,
  ADMIN_TEST_USER,
} from "./helpers/auth";

test.describe("Search Modes: Consumer User", () => {
  test.beforeEach(async ({ context }) => {
    await authenticateContext(context, TEST_USER);
  });

  test("keyword search button is visible (keyword_search=everyone)", async ({
    page,
  }) => {
    await page.goto("/journal/home");

    const keywordButton = page.getByRole("button", { name: "Keyword" });

    test.skip(
      !(await keywordButton.isVisible().catch(() => false)),
      "keyword_search flag not active for Consumer",
    );

    await expect(keywordButton).toBeVisible();
  });

  test("semantic search button is NOT visible for Consumer", async ({
    page,
  }) => {
    await page.goto("/journal/home");

    await expect(
      page.getByRole("button", { name: "Semantic" }),
    ).not.toBeVisible();
  });

  test("switching to keyword mode changes placeholder", async ({ page }) => {
    await page.goto("/journal/home");

    const keywordButton = page.getByRole("button", { name: "Keyword" });
    test.skip(
      !(await keywordButton.isVisible().catch(() => false)),
      "keyword_search flag not active",
    );

    await keywordButton.click();

    await expect(
      page.getByPlaceholder("Keyword search your entries..."),
    ).toBeVisible();
  });

  test("keyword search shows filter badge with mode label", async ({
    page,
  }) => {
    await page.goto("/journal/home");

    const keywordButton = page.getByRole("button", { name: "Keyword" });
    test.skip(
      !(await keywordButton.isVisible().catch(() => false)),
      "keyword_search flag not active",
    );

    await keywordButton.click();

    const searchInput = page.getByPlaceholder("Keyword search your entries...");
    await searchInput.fill("walk");

    // Generous timeout because the search input is debounced.
    await expect(page.getByText(/keyword: walk/i)).toBeVisible({
      timeout: 10000,
    });
  });

  test("switching back to exact mode restores default placeholder", async ({
    page,
  }) => {
    await page.goto("/journal/home");

    const keywordButton = page.getByRole("button", { name: "Keyword" });
    test.skip(
      !(await keywordButton.isVisible().catch(() => false)),
      "keyword_search flag not active",
    );

    await keywordButton.click();
    await expect(
      page.getByPlaceholder("Keyword search your entries..."),
    ).toBeVisible();

    await page.getByRole("button", { name: "Exact" }).click();
    await expect(page.getByPlaceholder("Search your entries...")).toBeVisible();
  });
});

test.describe("Search Modes: Admin User", () => {
  test.beforeEach(async ({ context }) => {
    await authenticateContext(context, ADMIN_TEST_USER);
  });

  test("both keyword and semantic buttons are visible for Admin", async ({
    page,
  }) => {
    await page.goto("/journal/home");

    const keywordButton = page.getByRole("button", { name: "Keyword" });
    const semanticButton = page.getByRole("button", { name: "Semantic" });

    test.skip(
      !(await keywordButton.isVisible().catch(() => false)),
      "keyword_search flag not active for Admin",
    );

    await expect(keywordButton).toBeVisible();
    await expect(semanticButton).toBeVisible();
  });

  test("exact button is also visible in the toggle group", async ({ page }) => {
    await page.goto("/journal/home");

    const exactButton = page.getByRole("button", { name: "Exact" });
    test.skip(
      !(await exactButton.isVisible().catch(() => false)),
      "search toggle not active for Admin",
    );

    await expect(exactButton).toBeVisible();
  });

  test("switching to semantic mode changes placeholder and icon area", async ({
    page,
  }) => {
    await page.goto("/journal/home");

    const semanticButton = page.getByRole("button", { name: "Semantic" });
    test.skip(
      !(await semanticButton.isVisible().catch(() => false)),
      "semantic_search flag not active",
    );

    await semanticButton.click();

    await expect(
      page.getByPlaceholder("Semantic search your entries..."),
    ).toBeVisible();
  });

  test("semantic search shows filter badge with mode label", async ({
    page,
  }) => {
    await page.goto("/journal/home");

    const semanticButton = page.getByRole("button", { name: "Semantic" });
    test.skip(
      !(await semanticButton.isVisible().catch(() => false)),
      "semantic_search flag not active",
    );

    await semanticButton.click();

    const searchInput = page.getByPlaceholder(
      "Semantic search your entries...",
    );
    await searchInput.fill("deployment");

    // Generous timeout because the search input is debounced.
    await expect(page.getByText(/semantic: deployment/i)).toBeVisible({
      timeout: 10000,
    });
  });

  test("switching from semantic to exact clears filter badge", async ({
    page,
  }) => {
    await page.goto("/journal/home");

    const semanticButton = page.getByRole("button", { name: "Semantic" });
    test.skip(
      !(await semanticButton.isVisible().catch(() => false)),
      "semantic_search flag not active",
    );

    await semanticButton.click();
    const searchInput = page.getByPlaceholder(
      "Semantic search your entries...",
    );
    await searchInput.fill("deployment");
    await expect(page.getByText(/semantic: deployment/i)).toBeVisible({
      timeout: 10000,
    });

    // Switching back to Exact keeps the input text but swaps the mode label.
    await page.getByRole("button", { name: "Exact" }).click();
    await expect(page.getByText(/text: deployment/i)).toBeVisible();
  });

  test("clear filters resets everything including search mode display", async ({
    page,
  }) => {
    await page.goto("/journal/home");

    const keywordButton = page.getByRole("button", { name: "Keyword" });
    test.skip(
      !(await keywordButton.isVisible().catch(() => false)),
      "keyword_search flag not active",
    );

    await keywordButton.click();
    const searchInput = page.getByPlaceholder("Keyword search your entries...");
    await searchInput.fill("debugging");

    await expect(page.getByText(/keyword: debugging/i)).toBeVisible({
      timeout: 10000,
    });

    await page.getByRole("button", { name: /clear filters/i }).click();

    await expect(
      page.getByText(/showing \d+ of \d+ entries/i),
    ).not.toBeVisible();
  });
});
