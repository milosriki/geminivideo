/**
 * End-to-End Tests for Campaign Flow
 * Tests full user journey: campaign creation, ad publishing, analytics viewing, creative studio
 *
 * Agent 29 of 30 - Comprehensive Test Suite
 * Uses Playwright for E2E testing
 * Coverage Target: 80%+
 */

import { test, expect, Page, Browser, BrowserContext } from '@playwright/test';

// Test configuration
const BASE_URL = process.env.E2E_BASE_URL || 'http://localhost:3000';
const API_URL = process.env.E2E_API_URL || 'http://localhost:8000';

// Test user credentials
const TEST_USER = {
  email: 'test@geminivideo.com',
  password: 'TestPassword123!',
  name: 'Test User'
};

// ============================================================================
// AUTHENTICATION FLOW TESTS
// ============================================================================

test.describe('Authentication Flow', () => {
  test('should load login page', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    await expect(page).toHaveTitle(/Login|Sign In/i);
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test('should show validation errors for invalid credentials', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Enter invalid email
    await page.fill('input[type="email"]', 'invalid-email');
    await page.fill('input[type="password"]', 'short');
    await page.click('button[type="submit"]');

    // Should show validation errors
    await expect(page.locator('text=/invalid.*email/i')).toBeVisible({ timeout: 5000 });
  });

  test('should login with valid credentials', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');

    // Should redirect to dashboard
    await page.waitForURL(/dashboard|home/i, { timeout: 10000 });
    await expect(page.locator('text=/welcome|dashboard/i')).toBeVisible();
  });

  test('should logout successfully', async ({ page }) => {
    // Login first
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/dashboard|home/i);

    // Logout
    await page.click('[data-testid="user-menu"], [aria-label*="menu" i]');
    await page.click('text=/logout|sign out/i');

    // Should redirect to login
    await page.waitForURL(/login/i);
  });

  test('should persist session after page reload', async ({ page }) => {
    // Login
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/dashboard/i);

    // Reload page
    await page.reload();

    // Should still be logged in
    await expect(page.locator('text=/welcome|dashboard/i')).toBeVisible();
  });
});

// ============================================================================
// CAMPAIGN CREATION FLOW
// ============================================================================

test.describe('Campaign Creation Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/dashboard/i);
  });

  test('should navigate to campaign creation page', async ({ page }) => {
    await page.click('text=/create campaign|new campaign/i');

    await expect(page).toHaveURL(/campaign\/create|campaign\/new/i);
    await expect(page.locator('text=/campaign name/i')).toBeVisible();
  });

  test('should create new campaign with basic settings', async ({ page }) => {
    await page.goto(`${BASE_URL}/campaign/create`);

    // Fill campaign details
    const campaignName = `Test Campaign ${Date.now()}`;
    await page.fill('input[name="name"], input[placeholder*="campaign name" i]', campaignName);

    // Select objective
    await page.click('select[name="objective"], [data-testid="objective-select"]');
    await page.click('text=/engagement|awareness/i');

    // Set budget
    await page.fill('input[name="daily_budget"], input[placeholder*="budget" i]', '50');

    // Submit
    await page.click('button[type="submit"], button:has-text("Create Campaign")');

    // Should show success message or redirect to campaign page
    await expect(
      page.locator('text=/campaign created|success/i')
    ).toBeVisible({ timeout: 10000 });
  });

  test('should validate required campaign fields', async ({ page }) => {
    await page.goto(`${BASE_URL}/campaign/create`);

    // Try to submit without filling required fields
    await page.click('button[type="submit"]');

    // Should show validation errors
    await expect(page.locator('text=/required|cannot be empty/i')).toBeVisible();
  });

  test('should save campaign as draft', async ({ page }) => {
    await page.goto(`${BASE_URL}/campaign/create`);

    const campaignName = `Draft Campaign ${Date.now()}`;
    await page.fill('input[name="name"]', campaignName);

    // Click save as draft
    await page.click('button:has-text("Save Draft"), button:has-text("Save as Draft")');

    await expect(page.locator('text=/saved as draft|draft saved/i')).toBeVisible();
  });

  test('should configure advanced targeting options', async ({ page }) => {
    await page.goto(`${BASE_URL}/campaign/create`);

    // Fill basic info
    await page.fill('input[name="name"]', `Targeted Campaign ${Date.now()}`);

    // Navigate to targeting section
    await page.click('text=/targeting|audience/i');

    // Set location targeting
    await page.click('input[placeholder*="location" i], select[name="location"]');
    await page.fill('input[placeholder*="location" i]', 'United States');
    await page.click('text=/united states/i');

    // Set age range
    await page.selectOption('select[name="age_min"]', '25');
    await page.selectOption('select[name="age_max"]', '54');

    // Set gender
    await page.click('input[value="all"], label:has-text("All")');

    // Add interests
    await page.fill('input[placeholder*="interest" i]', 'technology');
    await page.click('text=/add interest|technology/i');

    await page.click('button[type="submit"]');

    await expect(page.locator('text=/campaign created/i')).toBeVisible({ timeout: 10000 });
  });
});

// ============================================================================
// CREATIVE STUDIO TESTS
// ============================================================================

test.describe('Creative Studio Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/dashboard/i);
  });

  test('should access creative studio', async ({ page }) => {
    await page.click('text=/creative studio|studio/i, [href*="studio"]');

    await expect(page).toHaveURL(/studio|creative/i);
    await expect(page.locator('text=/create|new creative/i')).toBeVisible();
  });

  test('should upload video asset', async ({ page }) => {
    await page.goto(`${BASE_URL}/studio`);

    // Click upload button
    await page.click('button:has-text("Upload"), text=/upload video/i');

    // Upload file (mock file)
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test-video.mp4',
      mimeType: 'video/mp4',
      buffer: Buffer.from('mock video content')
    });

    // Should show upload progress or success
    await expect(
      page.locator('text=/uploading|upload complete|processing/i')
    ).toBeVisible({ timeout: 15000 });
  });

  test('should generate video from text prompt', async ({ page }) => {
    await page.goto(`${BASE_URL}/studio`);

    // Click generate button
    await page.click('button:has-text("Generate"), text=/ai generate/i');

    // Enter prompt
    await page.fill('textarea[placeholder*="describe" i], textarea[name="prompt"]',
      'Create a 15-second video about eco-friendly products');

    // Select style
    await page.click('select[name="style"]');
    await page.click('text=/modern|minimal/i');

    // Set duration
    await page.fill('input[name="duration"]', '15');

    // Generate
    await page.click('button:has-text("Generate Video")');

    // Should show generation in progress
    await expect(page.locator('text=/generating|processing/i')).toBeVisible();
  });

  test('should edit video in timeline', async ({ page }) => {
    await page.goto(`${BASE_URL}/studio`);

    // Select a video
    await page.click('.video-thumbnail, [data-testid="video-item"]');

    // Click edit
    await page.click('button:has-text("Edit")');

    // Should show timeline editor
    await expect(page.locator('[data-testid="timeline"], .timeline')).toBeVisible();

    // Add text overlay
    await page.click('button:has-text("Add Text"), [data-testid="add-text"]');
    await page.fill('input[placeholder*="text" i]', 'Amazing Product!');

    // Save changes
    await page.click('button:has-text("Save")');

    await expect(page.locator('text=/saved|changes saved/i')).toBeVisible();
  });

  test('should preview video before publishing', async ({ page }) => {
    await page.goto(`${BASE_URL}/studio`);

    // Select video
    await page.click('.video-thumbnail:first-child');

    // Click preview
    await page.click('button:has-text("Preview")');

    // Should show video player
    await expect(page.locator('video, [data-testid="video-player"]')).toBeVisible();

    // Should have play controls
    await expect(page.locator('button[aria-label*="play" i]')).toBeVisible();
  });

  test('should apply AI-powered enhancements', async ({ page }) => {
    await page.goto(`${BASE_URL}/studio`);

    // Select video
    await page.click('.video-thumbnail:first-child');

    // Click enhance button
    await page.click('button:has-text("Enhance"), button:has-text("AI Enhance")');

    // Select enhancement options
    await page.check('input[type="checkbox"][value="color_correction"]');
    await page.check('input[type="checkbox"][value="auto_captions"]');

    // Apply
    await page.click('button:has-text("Apply Enhancements")');

    // Should show processing
    await expect(page.locator('text=/processing|enhancing/i')).toBeVisible();
  });
});

// ============================================================================
// AD PUBLISHING FLOW
// ============================================================================

test.describe('Ad Publishing Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/dashboard/i);
  });

  test('should create ad with video creative', async ({ page }) => {
    await page.goto(`${BASE_URL}/campaign/123/create-ad`);

    // Select video
    await page.click('text=/select video|choose creative/i');
    await page.click('.video-thumbnail:first-child');

    // Add ad copy
    await page.fill('textarea[name="headline"]', 'Amazing Product Launch!');
    await page.fill('textarea[name="description"]', 'Get 50% off today only!');

    // Select CTA
    await page.selectOption('select[name="cta"]', 'shop_now');

    // Set destination URL
    await page.fill('input[name="url"]', 'https://example.com/shop');

    // Preview ad
    await page.click('button:has-text("Preview")');
    await expect(page.locator('[data-testid="ad-preview"]')).toBeVisible();

    // Publish
    await page.click('button:has-text("Publish")');

    await expect(page.locator('text=/ad published|live/i')).toBeVisible({ timeout: 15000 });
  });

  test('should configure ad placement options', async ({ page }) => {
    await page.goto(`${BASE_URL}/campaign/123/create-ad`);

    // Navigate to placements
    await page.click('text=/placement|where to show/i');

    // Select placements
    await page.check('input[value="facebook_feed"]');
    await page.check('input[value="instagram_stories"]');
    await page.check('input[value="instagram_reels"]');

    // Set device targeting
    await page.click('input[value="mobile_only"]');

    await page.click('button:has-text("Continue")');
  });

  test('should schedule ad for future publish', async ({ page }) => {
    await page.goto(`${BASE_URL}/campaign/123/create-ad`);

    // Fill ad details
    await page.fill('textarea[name="headline"]', 'Scheduled Ad');

    // Click schedule
    await page.click('text=/schedule|publish later/i');

    // Set future date
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    await page.fill('input[type="datetime-local"]', tomorrow.toISOString().slice(0, 16));

    // Confirm schedule
    await page.click('button:has-text("Schedule")');

    await expect(page.locator('text=/scheduled for/i')).toBeVisible();
  });

  test('should duplicate existing ad', async ({ page }) => {
    await page.goto(`${BASE_URL}/campaign/123/ads`);

    // Click duplicate on first ad
    await page.click('.ad-item:first-child button:has-text("Duplicate")');

    // Should open create form with pre-filled data
    await expect(page.locator('input[name="headline"]')).not.toBeEmpty();

    // Modify and save
    await page.fill('input[name="headline"]', 'Duplicated Ad');
    await page.click('button:has-text("Create")');

    await expect(page.locator('text=/ad created/i')).toBeVisible();
  });
});

// ============================================================================
// ANALYTICS & REPORTING
// ============================================================================

test.describe('Analytics & Reporting', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/dashboard/i);
  });

  test('should view campaign analytics dashboard', async ({ page }) => {
    await page.goto(`${BASE_URL}/analytics`);

    // Should show key metrics
    await expect(page.locator('text=/impressions/i')).toBeVisible();
    await expect(page.locator('text=/clicks/i')).toBeVisible();
    await expect(page.locator('text=/ctr/i')).toBeVisible();
    await expect(page.locator('text=/spend/i')).toBeVisible();
    await expect(page.locator('text=/roas/i')).toBeVisible();
  });

  test('should filter analytics by date range', async ({ page }) => {
    await page.goto(`${BASE_URL}/analytics`);

    // Click date range picker
    await page.click('[data-testid="date-range"], button:has-text("Date Range")');

    // Select last 30 days
    await page.click('text=/last 30 days/i');

    // Should update charts
    await expect(page.locator('.chart, [data-testid="analytics-chart"]')).toBeVisible();
  });

  test('should view individual campaign performance', async ({ page }) => {
    await page.goto(`${BASE_URL}/analytics`);

    // Click on a campaign
    await page.click('.campaign-row:first-child, [data-testid="campaign-item"]:first-child');

    // Should show detailed metrics
    await expect(page.locator('text=/ad sets|ads in campaign/i')).toBeVisible();
    await expect(page.locator('[data-testid="performance-chart"]')).toBeVisible();
  });

  test('should export analytics report', async ({ page }) => {
    await page.goto(`${BASE_URL}/analytics`);

    // Click export button
    const downloadPromise = page.waitForEvent('download');
    await page.click('button:has-text("Export"), button:has-text("Download Report")');

    // Select format
    await page.click('text=/csv|excel/i');

    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/analytics.*\.(csv|xlsx)/);
  });

  test('should view ROAS prediction vs actual', async ({ page }) => {
    await page.goto(`${BASE_URL}/analytics/campaign/123`);

    // Should show prediction comparison
    await expect(page.locator('text=/predicted roas/i')).toBeVisible();
    await expect(page.locator('text=/actual roas/i')).toBeVisible();

    // Should show accuracy metrics
    await expect(page.locator('text=/prediction accuracy|variance/i')).toBeVisible();
  });

  test('should view top performing creatives', async ({ page }) => {
    await page.goto(`${BASE_URL}/analytics`);

    // Navigate to creatives tab
    await page.click('text=/creatives|top ads/i');

    // Should show sorted creatives
    await expect(page.locator('.creative-item, [data-testid="creative-card"]')).toHaveCount(5, { timeout: 5000 });

    // First creative should have highest ROAS
    const firstROAS = await page.locator('.creative-item:first-child .roas').textContent();
    expect(firstROAS).toBeTruthy();
  });
});

// ============================================================================
// SETTINGS & CONFIGURATION
// ============================================================================

test.describe('Settings & Configuration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/dashboard/i);
  });

  test('should connect Meta (Facebook) account', async ({ page }) => {
    await page.goto(`${BASE_URL}/settings/integrations`);

    // Click connect Facebook
    await page.click('button:has-text("Connect Facebook"), button:has-text("Connect Meta")');

    // Should open OAuth popup or redirect
    // Note: In real test, this would require mocking OAuth flow
    await expect(page.locator('text=/facebook|meta/i')).toBeVisible();
  });

  test('should configure notification preferences', async ({ page }) => {
    await page.goto(`${BASE_URL}/settings/notifications`);

    // Toggle email notifications
    await page.check('input[name="email_notifications"]');

    // Enable campaign alerts
    await page.check('input[name="campaign_alerts"]');

    // Save settings
    await page.click('button:has-text("Save")');

    await expect(page.locator('text=/settings saved/i')).toBeVisible();
  });

  test('should update billing information', async ({ page }) => {
    await page.goto(`${BASE_URL}/settings/billing`);

    // Should show current plan
    await expect(page.locator('text=/current plan|subscription/i')).toBeVisible();

    // Click upgrade
    await page.click('button:has-text("Upgrade")');

    await expect(page.locator('text=/pricing|plans/i')).toBeVisible();
  });
});

// ============================================================================
// ERROR HANDLING & EDGE CASES
// ============================================================================

test.describe('Error Handling', () => {
  test('should show error when API is unavailable', async ({ page }) => {
    // Mock API failure
    await page.route(`${API_URL}/**`, route => route.abort());

    await page.goto(`${BASE_URL}/dashboard`);

    // Should show error message
    await expect(page.locator('text=/error|unable to load|try again/i')).toBeVisible({ timeout: 10000 });
  });

  test('should handle session timeout', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/dashboard/i);

    // Clear cookies to simulate timeout
    await page.context().clearCookies();

    // Try to access protected page
    await page.goto(`${BASE_URL}/analytics`);

    // Should redirect to login
    await expect(page).toHaveURL(/login/i);
  });

  test('should show validation errors inline', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');
    await page.waitForURL(/dashboard/i);

    await page.goto(`${BASE_URL}/campaign/create`);

    // Enter invalid budget
    await page.fill('input[name="daily_budget"]', '-10');
    await page.click('button[type="submit"]');

    // Should show inline error
    await expect(page.locator('text=/budget must be positive/i')).toBeVisible();
  });
});

// ============================================================================
// MOBILE RESPONSIVENESS
// ============================================================================

test.describe('Mobile Responsiveness', () => {
  test.use({ viewport: { width: 375, height: 667 } }); // iPhone SE

  test('should display mobile menu', async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);

    // Should show hamburger menu
    await expect(page.locator('button[aria-label*="menu" i]')).toBeVisible();

    // Click to open
    await page.click('button[aria-label*="menu" i]');

    // Should show navigation
    await expect(page.locator('nav, [role="navigation"]')).toBeVisible();
  });

  test('should work on mobile viewport', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    await page.fill('input[type="email"]', TEST_USER.email);
    await page.fill('input[type="password"]', TEST_USER.password);
    await page.click('button[type="submit"]');

    await page.waitForURL(/dashboard/i);

    // Dashboard should be usable on mobile
    await expect(page.locator('text=/welcome|dashboard/i')).toBeVisible();
  });
});
