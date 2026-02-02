import { test, expect } from "@playwright/test";

test.describe("Settings Page", () => {
  test("should display settings page with header", async ({ page }) => {
    await page.goto("/settings");
    
    const heading = page.getByRole('heading', { name: /^settings$/i });
    await expect(heading).toBeVisible({ timeout: 10000 });
  });

  test("should have theme toggle options", async ({ page }) => {
    await page.goto("/settings");
    
    const heading = page.getByRole('heading', { name: /^settings$/i });
    await expect(heading).toBeVisible({ timeout: 10000 });
    
    const lightButton = page.getByRole('button', { name: /light/i });
    const darkButton = page.getByRole('button', { name: /dark/i });
    const systemButton = page.getByRole('button', { name: /system/i });
    
    await expect(lightButton).toBeVisible();
    await expect(darkButton).toBeVisible();
    await expect(systemButton).toBeVisible();
  });

  test("should toggle to dark mode", async ({ page }) => {
    await page.goto("/settings");
    
    const heading = page.getByRole('heading', { name: /^settings$/i });
    await expect(heading).toBeVisible({ timeout: 10000 });
    
    const darkButton = page.getByRole('button', { name: /dark/i });
    await expect(darkButton).toBeVisible();
    await darkButton.click();
    
    const htmlClass = await page.locator("html").getAttribute("class");
    expect(htmlClass).toContain("dark");
  });

  test("should toggle to light mode", async ({ page }) => {
    await page.goto("/settings");
    
    const heading = page.getByRole('heading', { name: /^settings$/i });
    await expect(heading).toBeVisible({ timeout: 10000 });
    
    const darkButton = page.getByRole('button', { name: /dark/i });
    await darkButton.click();
    
    const lightButton = page.getByRole('button', { name: /light/i });
    await lightButton.click();
    
    const htmlClass = await page.locator("html").getAttribute("class") || "";
    expect(htmlClass).not.toContain("dark");
  });

  test("should have API key configuration section", async ({ page }) => {
    await page.goto("/settings");
    
    const heading = page.getByRole('heading', { name: /^settings$/i });
    await expect(heading).toBeVisible({ timeout: 10000 });
    
    const openaiTextbox = page.getByRole('textbox', { name: /openai api key/i });
    await expect(openaiTextbox).toBeVisible();
    
    const falTextbox = page.getByRole('textbox', { name: /fal\.ai api key/i });
    await expect(falTextbox).toBeVisible();
  });

  test("should have save button", async ({ page }) => {
    await page.goto("/settings");
    
    const heading = page.getByRole('heading', { name: /^settings$/i });
    await expect(heading).toBeVisible({ timeout: 10000 });
    
    const saveButton = page.getByRole('button', { name: /save settings/i });
    await expect(saveButton).toBeVisible();
    await expect(saveButton).toBeEnabled();
  });
});

test.describe("Dashboard Page", () => {
  test("should display dashboard with heading", async ({ page }) => {
    await page.goto("/dashboard");
    
    const heading = page.getByRole('heading', { level: 1 });
    await expect(heading).toBeVisible({ timeout: 10000 });
  });

  test("should have navigation to campaigns", async ({ page }) => {
    await page.goto("/dashboard");
    
    const campaignsLink = page.getByRole('link', { name: /campaigns/i }).first();
    await expect(campaignsLink).toBeVisible();
  });

  test("should have quick action buttons", async ({ page }) => {
    await page.goto("/dashboard");
    
    const heading = page.getByRole('heading', { level: 1 });
    await expect(heading).toBeVisible({ timeout: 10000 });
    
    const newCampaignLink = page.getByRole('link', { name: 'New Campaign', exact: true });
    await expect(newCampaignLink).toBeVisible();
  });

  test("should display stats cards", async ({ page }) => {
    await page.goto("/dashboard");
    
    const heading = page.getByRole('heading', { level: 1 });
    await expect(heading).toBeVisible({ timeout: 10000 });
    
    const totalCampaigns = page.getByText(/total campaigns/i);
    await expect(totalCampaigns).toBeVisible();
  });
});
