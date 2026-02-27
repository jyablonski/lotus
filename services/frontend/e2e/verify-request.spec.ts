/**
 * E2E tests for the verify-request page.
 *
 * This page is shown after a user submits their email for a magic link.
 * It displays a "check your email" message with a link to try again.
 */
import { test, expect } from "@playwright/test";

test.describe("Verify Request Page", () => {
  test("renders the 'Check your email' heading", async ({ page }) => {
    await page.goto("/verify-request");

    await expect(
      page.getByRole("heading", { name: /check your email/i }),
    ).toBeVisible();
  });

  test("shows instruction text about the sign-in link", async ({ page }) => {
    await page.goto("/verify-request");

    await expect(page.getByText(/we sent you a sign-in link/i)).toBeVisible();
  });

  test("shows expiration notice", async ({ page }) => {
    await page.goto("/verify-request");

    await expect(
      page.getByText(/the link will expire in 24 hours/i),
    ).toBeVisible();
  });

  test("has a 'Try again' link pointing to /signin", async ({ page }) => {
    await page.goto("/verify-request");

    const tryAgainLink = page.getByRole("link", { name: /try again/i });
    await expect(tryAgainLink).toBeVisible();
    await expect(tryAgainLink).toHaveAttribute("href", "/signin");
  });

  test("has a 'Back to home' link", async ({ page }) => {
    await page.goto("/verify-request");

    const homeLink = page.getByRole("link", { name: /back to home/i });
    await expect(homeLink).toBeVisible();
    await expect(homeLink).toHaveAttribute("href", "/");
  });
});
