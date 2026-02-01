import { test, expect } from "@playwright/test";

test.describe("Settings Page", () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication
    await page.goto("/");
    await page.evaluate(() => {
      localStorage.setItem("token", "mock-jwt-token-for-testing");
    });
  });

  test("should display settings page with header", async ({ page }) => {
    await page.goto("/settings");
    
    // Check for settings header
    const heading = page.locator("h1, h2").first();
    await expect(heading).toBeVisible();
    await expect(heading).toContainText(/settings/i);
  });

  test("should have theme toggle options", async ({ page }) => {
    await page.goto("/settings");
    
    // Look for theme toggle buttons
    const lightButton = page.locator('button').filter({ hasText: /light/i });
    const darkButton = page.locator('button').filter({ hasText: /dark/i });
    const systemButton = page.locator('button').filter({ hasText: /system/i });
    
    // At least one theme option should exist
    const hasThemeOptions = (
      await lightButton.isVisible().catch(() => false) ||
      await darkButton.isVisible().catch(() => false) ||
      await systemButton.isVisible().catch(() => false)
    );
    
    expect(hasThemeOptions).toBeTruthy();
  });

  test("should toggle to dark mode", async ({ page }) => {
    await page.goto("/settings");
    
    const darkButton = page.locator('button').filter({ hasText: /dark/i }).first();
    
    if (await darkButton.isVisible()) {
      await darkButton.click();
      await page.waitForTimeout(100);
      
      // Check if dark class is applied to html element
      const htmlClass = await page.locator("html").getAttribute("class");
      expect(htmlClass).toContain("dark");
    }
  });

  test("should toggle to light mode", async ({ page }) => {
    await page.goto("/settings");
    
    // First enable dark mode
    const darkButton = page.locator('button').filter({ hasText: /dark/i }).first();
    if (await darkButton.isVisible()) {
      await darkButton.click();
      await page.waitForTimeout(100);
    }
    
    // Then switch to light mode
    const lightButton = page.locator('button').filter({ hasText: /light/i }).first();
    if (await lightButton.isVisible()) {
      await lightButton.click();
      await page.waitForTimeout(100);
      
      // Check if dark class is removed
      const htmlClass = await page.locator("html").getAttribute("class") || "";
      expect(htmlClass).not.toContain("dark");
    }
  });

  test("should have API key configuration section", async ({ page }) => {
    await page.goto("/settings");
    await page.waitForLoadState("domcontentloaded");
    
    // Look for API key related elements
    const apiKeySection = page.locator('text=/api.*key|openai|fal|engine/i').first();
    const hasApiSection = await apiKeySection.isVisible().catch(() => false);
    
    // API configuration should be present
    expect(hasApiSection).toBeTruthy();
  });

  test("should have save button", async ({ page }) => {
    await page.goto("/settings");
    await page.waitForLoadState("domcontentloaded");
    
    // Look for save button
    const saveButton = page.locator('button').filter({ hasText: /save|update/i }).first();
    
    await expect(saveButton).toBeVisible();
    await expect(saveButton).toBeEnabled();
  });
});

test.describe("Dashboard Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.evaluate(() => {
      localStorage.setItem("token", "mock-jwt-token-for-testing");
    });
  });

  test("should display dashboard with heading", async ({ page }) => {
    await page.goto("/dashboard");
    
    // Dashboard should have a heading
    const heading = page.locator("h1, h2").first();
    await expect(heading).toBeVisible();
  });

  test("should have navigation to campaigns", async ({ page }) => {
    await page.goto("/dashboard");
    
    // Look for link to campaigns
    const campaignsLink = page.locator('a[href*="campaigns"]').first();
    await expect(campaignsLink).toBeVisible();
  });

  test("should have quick action buttons", async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("domcontentloaded");
    
    // Look for action buttons/links
    const actionButton = page.locator('a, button').filter({ hasText: /create|new|campaign|start/i }).first();
    
    await expect(actionButton).toBeVisible();
    await expect(actionButton).toBeEnabled();
  });

  test("should display stats or content cards", async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("domcontentloaded");
    
    // Look for card elements
    const cards = page.locator('[class*="card"], [class*="Card"]');
    const cardCount = await cards.count();
    
    // Dashboard should have at least one card/section
    expect(cardCount).toBeGreaterThan(0);
  });

  test("should show campaign statistics", async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("domcontentloaded");
    
    // Look for stats-related content
    const statsContent = page.locator('text=/total|completed|in progress|campaigns|failed/i');
    const hasStats = await statsContent.first().isVisible().catch(() => false);
    
    expect(hasStats).toBeTruthy();
  });
});
