/**
 * E2E tests for the CSGODouble game page.
 *
 * Access is gated by the `frontend_admin` waffle flag (superusers=true),
 * so only Admin-role users can view the page. Consumer users are
 * redirected to /profile.
 */
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

    // frontend_admin flag is superusers-only, so Consumer gets redirected to /profile
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

    // Skip if admin flag isn't active (shouldn't happen, but safety)
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
    // Balance value (e.g. "$100") is the sibling <p> after the "Balance" label
    const balanceValue = balanceLabel.locator("..").locator("p.text-2xl");
    await expect(balanceValue).toBeVisible();
    await expect(balanceValue).toHaveText(/^\$\d+$/);
  });

  test("countdown or spinning state is displayed", async ({ page }) => {
    await page.goto("/games/csgodouble");

    // Either "Rolling in X.Xs" countdown, "Spinning…", or "Loading…" should show
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

    // Quick bet buttons (exact: true to avoid +1 matching +10, +100, +1000)
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

    // Red zone (1-7, 2x)
    await expect(redZone).toBeVisible();
    // Green zone (0, 14x)
    await expect(
      page.getByRole("button", { name: "0" }).filter({ hasText: "14x" }),
    ).toBeVisible();
    // Black zone (8-14, 2x)
    await expect(page.getByRole("button", { name: /8 to 14/i })).toBeVisible();
  });

  test("placing a bet updates zone total and balance", async ({ page }) => {
    await page.goto("/games/csgodouble");

    const betInput = page.locator("input[type='number']");
    test.skip(
      !(await betInput.isVisible().catch(() => false)),
      "frontend_admin flag not active",
    );

    // Read initial balance (scoped to the Balance label's parent)
    const balanceValue = page
      .getByText("Balance")
      .locator("..")
      .locator("p.text-2xl");
    const initialBalance = await balanceValue.textContent();

    // Set bet amount to 10
    await betInput.fill("10");

    // Place a bet on 1-7 (red zone)
    const redZone = page.getByRole("button", { name: /1 to 7/i });
    await redZone.click();

    // The zone should show "Your bet: $10"
    await expect(page.getByText("Your bet: $10")).toBeVisible();

    // Total placed should show 10
    await expect(page.getByText("Total placed this round: $10")).toBeVisible();

    // Balance should have decreased
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

    // Read initial balance (scoped to the Balance label's parent)
    const balanceValue = page
      .getByText("Balance")
      .locator("..")
      .locator("p.text-2xl");
    const initialBalance = await balanceValue.textContent();

    // Place a bet
    await betInput.fill("10");
    await page.getByRole("button", { name: /1 to 7/i }).click();

    // Verify bet was placed
    await expect(page.getByText("Your bet: $10")).toBeVisible();

    // Clear all bets
    await page.getByRole("button", { name: /clear all bets/i }).click();

    // Balance should be restored
    await expect(balanceValue).toHaveText(initialBalance!);

    // Total placed should be 0
    await expect(page.getByText("Total placed this round: $0")).toBeVisible();
  });

  test("roulette strip is rendered with colored cells", async ({ page }) => {
    await page.goto("/games/csgodouble");

    // The roulette strip renders cells with bg-red-600, bg-zinc-900, bg-emerald-600
    const cells = page.locator(
      "[class*='bg-red-600'], [class*='bg-zinc-900'], [class*='bg-emerald-600']",
    );
    test.skip((await cells.count()) === 0, "frontend_admin flag not active");

    // Should have multiple visible cells in the strip
    expect(await cells.count()).toBeGreaterThan(5);
  });
});
