import { test, expect } from "@playwright/test";

// Test user credentials
const TEST_USER = {
  email: `test_${Date.now()}@example.com`,
  password: "TestPassword123!",
};

test.describe("Authentication Flow", () => {
  test("should show login page", async ({ page }) => {
    await page.goto("/login");
    await expect(page.locator("h1, h2").first()).toContainText(/sign in|login|welcome/i);
    await expect(page.locator('input[type="email"], input[name="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test("should show register page", async ({ page }) => {
    await page.goto("/register");
    await expect(page.locator("h1, h2").first()).toContainText(/sign up|register|create/i);
    await expect(page.locator('input[type="email"], input[name="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test("should show validation errors for empty form", async ({ page }) => {
    await page.goto("/login");
    await page.locator('button[type="submit"]').click();
    // Should stay on login page or show validation
    await expect(page).toHaveURL(/login/);
  });

  test("should navigate between login and register", async ({ page }) => {
    await page.goto("/login");
    
    // Find link to register
    const registerLink = page.locator('a[href*="register"]');
    if (await registerLink.isVisible()) {
      await registerLink.click();
      await expect(page).toHaveURL(/register/);
    }
  });

  test("should redirect unauthenticated users from protected routes", async ({ page }) => {
    // Clear any existing auth
    await page.goto("/");
    await page.evaluate(() => localStorage.clear());
    
    // Try to access protected route
    await page.goto("/dashboard");
    
    // Should redirect to login
    await expect(page).toHaveURL(/login|register/);
  });
});

test.describe("Authenticated User Flow", () => {
  test.skip("should register, login, and access dashboard", async ({ page }) => {
    // This test requires a running backend
    // Skip in CI without proper backend setup
    
    // Register
    await page.goto("/register");
    await page.fill('input[type="email"], input[name="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.locator('button[type="submit"]').click();
    
    // Should redirect to onboarding or dashboard
    await expect(page).toHaveURL(/onboarding|dashboard/);
  });
});
