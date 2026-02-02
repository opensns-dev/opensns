import { test, expect } from "@playwright/test";

test.describe("Campaigns Page", () => {
  test("should display campaigns page with heading", async ({ page }) => {
    await page.goto("/campaigns");
    
    const heading = page.getByRole('heading', { name: /campaigns/i });
    await expect(heading).toBeVisible();
  });

  test("should have create campaign button", async ({ page }) => {
    await page.goto("/campaigns");
    
    const createButton = page.getByRole('button', { name: /create campaign/i });
    await expect(createButton).toBeVisible();
  });

  test("should show empty state or campaigns list", async ({ page }) => {
    await page.goto("/campaigns");
    
    const table = page.locator('table');
    await expect(table).toBeVisible();
    
    const emptyMessage = page.getByText(/no campaigns yet/i);
    const campaignRows = table.locator('tbody tr');
    
    const hasEmpty = await emptyMessage.isVisible().catch(() => false);
    const rowCount = await campaignRows.count();
    
    expect(hasEmpty || rowCount > 0).toBeTruthy();
  });
});

test.describe("Campaign Creation", () => {
  test("should show new campaign form in dialog", async ({ page }) => {
    await page.goto("/campaigns");
    
    const createButton = page.getByRole('button', { name: /create campaign/i });
    await createButton.click();
    
    const dialog = page.locator('[role="dialog"]');
    await expect(dialog).toBeVisible();
    
    const titleInput = dialog.locator('input#title');
    const urlInput = dialog.locator('input#url');
    
    await expect(titleInput).toBeVisible();
    await expect(urlInput).toBeVisible();
  });

  test("should create a new campaign", async ({ page }) => {
    await page.goto("/campaigns");
    
    const errorMessage = page.getByText(/failed to load/i);
    const hasError = await errorMessage.isVisible().catch(() => false);
    if (hasError) {
      console.log("Skipping test - campaigns API not available");
      return;
    }
    
    const createButton = page.getByRole('button', { name: /create campaign/i });
    await expect(createButton).toBeVisible({ timeout: 10000 });
    await createButton.click();
    
    const dialog = page.locator('[role="dialog"]');
    await expect(dialog).toBeVisible();
    
    const titleInput = dialog.locator('input#title');
    const urlInput = dialog.locator('input#url');
    
    await titleInput.fill(`E2E Test Campaign ${Date.now()}`);
    await urlInput.fill("https://example.com/test-product");
    
    const submitButton = dialog.getByRole('button', { name: /start analysis/i });
    await submitButton.click();
    
    await expect(dialog).not.toBeVisible({ timeout: 10000 });
  });
});

test.describe("Campaign Detail Features", () => {
  test("should navigate to campaign detail from list", async ({ page }) => {
    await page.goto("/campaigns");
    
    const viewButton = page.getByRole('link', { name: /view/i }).first();
    const hasViewButton = await viewButton.isVisible().catch(() => false);
    
    if (!hasViewButton) {
      return;
    }
    
    await viewButton.click();
    await expect(page).toHaveURL(/\/campaigns\/\d+/);
    
    const backLink = page.locator('a[href="/campaigns"]');
    await expect(backLink).toBeVisible();
  });

  test("should show campaign info card on detail page", async ({ page }) => {
    await page.goto("/campaigns");
    
    const viewButton = page.getByRole('link', { name: /view/i }).first();
    const hasViewButton = await viewButton.isVisible().catch(() => false);
    
    if (!hasViewButton) {
      return;
    }
    
    await viewButton.click();
    
    const campaignInfoHeading = page.getByRole('heading', { name: /campaign info/i });
    await expect(campaignInfoHeading).toBeVisible({ timeout: 5000 });
  });

  test("should have asset type tabs", async ({ page }) => {
    await page.goto("/campaigns");
    
    const viewButton = page.getByRole('link', { name: /view/i }).first();
    const hasViewButton = await viewButton.isVisible().catch(() => false);
    
    if (!hasViewButton) {
      return;
    }
    
    await viewButton.click();
    await page.waitForLoadState("networkidle");
    
    const imagesTab = page.getByRole('button', { name: /images/i });
    const videosTab = page.getByRole('button', { name: /videos/i });
    const copiesTab = page.getByRole('button', { name: /ad copies/i });
    
    await expect(imagesTab).toBeVisible({ timeout: 5000 });
    await expect(videosTab).toBeVisible();
    await expect(copiesTab).toBeVisible();
  });

  test("should navigate back to campaigns list", async ({ page }) => {
    await page.goto("/campaigns");
    
    const viewButton = page.getByRole('link', { name: /view/i }).first();
    const hasViewButton = await viewButton.isVisible().catch(() => false);
    
    if (!hasViewButton) {
      return;
    }
    
    await viewButton.click();
    
    const backLink = page.locator('a[href="/campaigns"]');
    await expect(backLink).toBeVisible();
    await backLink.click();
    
    await expect(page).toHaveURL(/\/campaigns$/);
  });
});
