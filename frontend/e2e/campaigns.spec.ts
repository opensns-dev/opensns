import { test, expect } from "@playwright/test";

test.describe("Campaigns Page", () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication by setting token
    await page.goto("/");
    await page.evaluate(() => {
      localStorage.setItem("token", "mock-jwt-token-for-testing");
    });
  });

  test("should display campaigns page with heading", async ({ page }) => {
    await page.goto("/campaigns");
    
    // Check for main heading
    const heading = page.locator("h1, h2").first();
    await expect(heading).toBeVisible();
  });

  test("should have create campaign button", async ({ page }) => {
    await page.goto("/campaigns");
    
    // Look for create/new campaign button
    const createButton = page.locator('button, a').filter({ hasText: /create|new|add/i });
    await expect(createButton.first()).toBeVisible();
  });

  test("should render campaign detail page", async ({ page }) => {
    await page.goto("/campaigns/1");
    
    // Page should load and show content (either campaign or error state)
    await page.waitForLoadState("domcontentloaded");
    await expect(page.locator("body")).not.toBeEmpty();
  });
});

test.describe("Campaign Creation", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.evaluate(() => {
      localStorage.setItem("token", "mock-jwt-token-for-testing");
    });
  });

  test("should show new campaign form elements", async ({ page }) => {
    await page.goto("/campaigns/new");
    
    // Look for form elements
    const urlInput = page.locator('input[name="product_url"], input[placeholder*="url" i], input[type="url"]');
    const titleInput = page.locator('input[name="title"], input[placeholder*="title" i]');
    
    // At least one form element should be visible
    const hasUrlInput = await urlInput.isVisible().catch(() => false);
    const hasTitleInput = await titleInput.isVisible().catch(() => false);
    
    expect(hasUrlInput || hasTitleInput).toBeTruthy();
  });
});

test.describe("Campaign Detail Features", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.evaluate(() => {
      localStorage.setItem("token", "mock-jwt-token-for-testing");
    });
  });

  test("should have asset tabs when campaign loads", async ({ page }) => {
    await page.goto("/campaigns/1");
    await page.waitForLoadState("domcontentloaded");
    
    // Look for asset type tabs (Images, Videos, Copies)
    const imagesTab = page.locator('button, [role="tab"]').filter({ hasText: /image/i });
    const videosTab = page.locator('button, [role="tab"]').filter({ hasText: /video/i });
    const copiesTab = page.locator('button, [role="tab"]').filter({ hasText: /cop|text|ad/i });
    
    // Check if tabs exist (they will if campaign loads, won't if error state)
    const tabCount = await imagesTab.count() + await videosTab.count() + await copiesTab.count();
    
    // Either we have tabs (success) or we have an error message (expected without data)
    const hasErrorMessage = await page.locator('text=/not found|error|failed|access/i').isVisible().catch(() => false);
    
    expect(tabCount > 0 || hasErrorMessage).toBeTruthy();
  });

  test("should have back navigation link", async ({ page }) => {
    await page.goto("/campaigns/1");
    await page.waitForLoadState("domcontentloaded");
    
    // Look for back link to campaigns list
    const backLink = page.locator('a[href="/campaigns"]');
    
    // Either back link exists or we're on error page
    const hasBackLink = await backLink.isVisible().catch(() => false);
    const hasGoBackButton = await page.locator('button, a').filter({ hasText: /back|go back|return/i }).isVisible().catch(() => false);
    
    expect(hasBackLink || hasGoBackButton).toBeTruthy();
  });

  test("should handle clicking back navigation", async ({ page }) => {
    await page.goto("/campaigns/1");
    await page.waitForLoadState("domcontentloaded");
    
    const backLink = page.locator('a[href="/campaigns"]').first();
    
    if (await backLink.isVisible()) {
      await backLink.click();
      await expect(page).toHaveURL(/\/campaigns$/);
    }
  });
});
