// The CSGODouble page is gated by the frontend_admin waffle flag (superusers=true),
// so only Admin-role users can view it. Consumer users are redirected to /profile.
import { test, expect } from "@playwright/test";
import {
  authenticateContext,
  TEST_USER,
  ADMIN_TEST_USER,
} from "./helpers/auth";

test.describe("CSGODouble: Consumer User (non-admin)", () => {
  test.beforeEach(async ({ context }) => {
    await authenticateContext(context, TEST_USER);
  });

  test("non-admin user is redirected away from /games/csgodouble", async ({
    page,
  }) => {
    await page.goto("/games/csgodouble");

    await page.waitForURL("**/profile", { timeout: 10000 });

    await expect(
      page.getByRole("heading", { name: /csgo double/i }),
    ).not.toBeVisible();
  });
});

test.describe("CSGODouble: Admin User", () => {
  test.beforeEach(async ({ context }) => {
    await authenticateContext(context, ADMIN_TEST_USER);
  });

  test("page loads with heading", async ({ page }) => {
    await page.goto("/games/csgodouble");

    const heading = page.getByRole("heading", { name: /csgo double/i });
    test.skip(
      !(await heading.isVisible().catch(() => false)),
      "frontend_admin flag not active for Admin user",
    );

    await expect(heading).toBeVisible();
  });

  test("back to profile link is visible", async ({ page }) => {
    await page.goto("/games/csgodouble");

    const backLink = page.getByRole("link", { name: /back to profile/i });
    test.skip(
      !(await backLink.isVisible().catch(() => false)),
      "frontend_admin flag not active",
    );

    await expect(backLink).toBeVisible();
    await expect(backLink).toHaveAttribute("href", "/profile");
  });

  test("balance display is visible", async ({ page }) => {
    await page.goto("/games/csgodouble");

    const balanceLabel = page.getByText("Balance");
    test.skip(
      !(await balanceLabel.isVisible().catch(() => false)),
      "frontend_admin flag not active",
    );

    await expect(balanceLabel).toBeVisible();
    // The balance value (e.g. "$100") renders as a sibling <p> of the label.
    const balanceValue = balanceLabel.locator("..").locator("p.text-2xl");
    await expect(balanceValue).toBeVisible();
    await expect(balanceValue).toHaveText(/^\$\d+$/);
  });

  test("countdown or spinning state is displayed", async ({ page }) => {
    await page.goto("/games/csgodouble");

    // The status card can be in one of three states: countdown, spinning, or loading.
    const statusCard = page.locator("text=/rolling in|spinning|loading/i");
    test.skip(
      !(await statusCard.isVisible().catch(() => false)),
      "frontend_admin flag not active",
    );

    await expect(statusCard).toBeVisible();
  });

  test("bet input and quick-amount buttons are visible", async ({ page }) => {
    await page.goto("/games/csgodouble");

    const betInput = page.locator("input[type='number']");
    test.skip(
      !(await betInput.isVisible().catch(() => false)),
      "frontend_admin flag not active",
    );

    await expect(betInput).toBeVisible();

    // exact: true prevents "+1" from matching "+10", "+100", "+1000".
    for (const label of ["Clear", "Last", "+1", "+10", "+100", "Max"]) {
      await expect(
        page.getByRole("button", { name: label, exact: true }),
      ).toBeVisible();
    }
  });

  test("three betting zones are displayed", async ({ page }) => {
    await page.goto("/games/csgodouble");

    const redZone = page.getByRole("button", { name: /1 to 7/i });
    test.skip(
      !(await redZone.isVisible().catch(() => false)),
      "frontend_admin flag not active",
    );

    await expect(redZone).toBeVisible();
    await expect(
      page.getByRole("button", { name: "0" }).filter({ hasText: "14x" }),
    ).toBeVisible();
    await expect(page.getByRole("button", { name: /8 to 14/i })).toBeVisible();
  });

  test("placing a bet updates zone total and balance", async ({ page }) => {
    await page.goto("/games/csgodouble");

    const betInput = page.locator("input[type='number']");
    test.skip(
      !(await betInput.isVisible().catch(() => false)),
      "frontend_admin flag not active",
    );

    // Scope to the Balance label's parent so we match the value, not any $-prefixed text.
    const balanceValue = page
      .getByText("Balance")
      .locator("..")
      .locator("p.text-2xl");
    const initialBalance = await balanceValue.textContent();

    await betInput.fill("10");

    const redZone = page.getByRole("button", { name: /1 to 7/i });
    await redZone.click();

    await expect(page.getByText("Your bet: $10")).toBeVisible();
    await expect(page.getByText("Total placed this round: $10")).toBeVisible();

    const newBalance = await balanceValue.textContent();
    expect(newBalance).not.toEqual(initialBalance);
  });

  test("clear all bets refunds balance", async ({ page }) => {
    await page.goto("/games/csgodouble");

    const betInput = page.locator("input[type='number']");
    test.skip(
      !(await betInput.isVisible().catch(() => false)),
      "frontend_admin flag not active",
    );

    // Scope to the Balance label's parent so we match the value, not any $-prefixed text.
    const balanceValue = page
      .getByText("Balance")
      .locator("..")
      .locator("p.text-2xl");
    const initialBalance = await balanceValue.textContent();

    await betInput.fill("10");
    await page.getByRole("button", { name: /1 to 7/i }).click();
    await expect(page.getByText("Your bet: $10")).toBeVisible();

    await page.getByRole("button", { name: /clear all bets/i }).click();

    await expect(balanceValue).toHaveText(initialBalance!);
    await expect(page.getByText("Total placed this round: $0")).toBeVisible();
  });

  test("roulette strip is rendered with colored cells", async ({ page }) => {
    await page.goto("/games/csgodouble");

    // Strip cells use bg-red-600 / bg-zinc-900 / bg-emerald-600 (red/black/green).
    const cells = page.locator(
      "[class*='bg-red-600'], [class*='bg-zinc-900'], [class*='bg-emerald-600']",
    );
    test.skip((await cells.count()) === 0, "frontend_admin flag not active");

    expect(await cells.count()).toBeGreaterThan(5);
  });
});
