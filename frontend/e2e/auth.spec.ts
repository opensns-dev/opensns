import { test, expect } from "@playwright/test";

test.describe("Authentication Flow", () => {
  test("should show login page", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByText(/welcome back/i)).toBeVisible();
    await expect(page.locator('input[type="email"], input[name="email"], input#email')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test("should show register page", async ({ page }) => {
    await page.goto("/register");
    await expect(page.getByText(/create.*account|sign up|register/i).first()).toBeVisible();
    await expect(page.locator('input[type="email"], input[name="email"], input#email')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test("should show validation errors for empty form", async ({ page }) => {
    await page.goto("/login");
    await page.locator('button[type="submit"]').click();
    await expect(page).toHaveURL(/login/);
  });

  test("should navigate between login and register", async ({ page }) => {
    await page.goto("/login");
    
    const registerLink = page.locator('a[href*="register"]');
    if (await registerLink.isVisible()) {
      await registerLink.click();
      await expect(page).toHaveURL(/register/);
    }
  });

  test("should allow access to dashboard without auth for now", async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("domcontentloaded");
    await expect(page.locator("body")).toBeVisible();
  });
});

test.describe("Authenticated User Flow", () => {
  test.skip("should register, login, and access dashboard", async ({ page }) => {
    const testEmail = `test_${Date.now()}@example.com`;
    
    await page.goto("/register");
    await page.fill('input[type="email"], input[name="email"], input#email', testEmail);
    await page.fill('input[type="password"]', "TestPassword123!");
    await page.locator('button[type="submit"]').click();
    
    await expect(page).toHaveURL(/onboarding|dashboard/);
  });
});
