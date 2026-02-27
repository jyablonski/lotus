/**
 * E2E tests for the sign-in page.
 *
 * These tests verify that the custom sign-in page at /signin renders
 * correctly for unauthenticated users with both the email (magic link)
 * form and the GitHub OAuth button.
 */
import { test, expect } from "@playwright/test";

test.describe("Sign-In Page", () => {
  test("renders the sign-in page heading", async ({ page }) => {
    await page.goto("/signin");

    await expect(
      page.getByRole("heading", { name: /welcome to lotus/i }),
    ).toBeVisible();
  });

  test("shows email input field", async ({ page }) => {
    await page.goto("/signin");

    const emailInput = page.getByLabel(/email address/i);
    await expect(emailInput).toBeVisible();
    await expect(emailInput).toHaveAttribute("type", "email");
  });

  test("shows 'Sign in with Email' button", async ({ page }) => {
    await page.goto("/signin");

    await expect(
      page.getByRole("button", { name: /sign in with email/i }),
    ).toBeVisible();
  });

  test("shows 'Sign in with GitHub' button", async ({ page }) => {
    await page.goto("/signin");

    await expect(
      page.getByRole("button", { name: /sign in with github/i }),
    ).toBeVisible();
  });

  test("shows 'or continue with' divider text", async ({ page }) => {
    await page.goto("/signin");

    await expect(page.getByText(/or continue with/i)).toBeVisible();
  });

  test("has a 'Back to home' link", async ({ page }) => {
    await page.goto("/signin");

    const homeLink = page.getByRole("link", { name: /back to home/i });
    await expect(homeLink).toBeVisible();
    await expect(homeLink).toHaveAttribute("href", "/");
  });

  test("sign-in description text is visible", async ({ page }) => {
    await page.goto("/signin");

    await expect(page.getByText(/sign in to start journaling/i)).toBeVisible();
  });
});
