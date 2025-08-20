// VectorBid Landing Page E2E Tests
// Critical user journey testing with accessibility and performance validation

import { test, expect } from '@playwright/test';
import { injectAxe, checkA11y } from 'axe-playwright';

test.describe('VectorBid Landing Page', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to landing page
    await page.goto('/');
    
    // Inject axe for accessibility testing
    await injectAxe(page);
    
    // Wait for critical resources to load
    await page.waitForLoadState('networkidle');
  });

  test('should load and display core elements', async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/VectorBid.*AI.*Pilot.*Bidding/i);
    
    // Check hero section
    const heroHeading = page.locator('h1#hero-heading');
    await expect(heroHeading).toBeVisible();
    await expect(heroHeading).toContainText(/VectorBid|Hours of Confusion|Perfect Schedules/i);
    
    // Check navigation
    const navigation = page.locator('nav[role="navigation"]');
    await expect(navigation).toBeVisible();
    
    // Check main content area
    const mainContent = page.locator('main#main-content');
    await expect(mainContent).toBeVisible();
    
    // Check footer
    const footer = page.locator('footer[role="contentinfo"]');
    await expect(footer).toBeVisible();
  });

  test('should have accessible navigation with skip links', async ({ page }) => {
    // Test skip navigation
    await page.keyboard.press('Tab');
    
    const skipLink = page.locator('.skip-nav');
    if (await skipLink.count() > 0) {
      await expect(skipLink).toBeFocused();
      
      // Test skip link functionality
      await skipLink.click();
      const mainContent = page.locator('#main-content');
      await expect(mainContent).toBeFocused();
    }
    
    // Test keyboard navigation through main elements
    await page.keyboard.press('Tab');
    await page.keyboard.press('Tab');
    
    // Check that focus is visible
    const focusedElement = page.locator(':focus');
    await expect(focusedElement).toBeVisible();
  });

  test('should pass accessibility standards', async ({ page }) => {
    // Check for accessibility violations
    await checkA11y(page, null, {
      detailedReport: true,
      detailedReportOptions: { html: true },
      rules: {
        // Customize rules for our specific implementation
        'color-contrast': { enabled: true },
        'focus-order-semantics': { enabled: true },
        'keyboard': { enabled: true },
        'landmark-no-duplicate-banner': { enabled: true },
        'landmark-no-duplicate-contentinfo': { enabled: true },
        'skip-link': { enabled: true }
      }
    });
  });

  test('should display data flow visualization', async ({ page }) => {
    // Find data flow section
    const dataFlowSection = page.locator('section[aria-labelledby="dataflow-heading"]');
    await expect(dataFlowSection).toBeVisible();
    
    // Check section heading
    const sectionHeading = page.locator('#dataflow-heading');
    await expect(sectionHeading).toContainText('AI Data Flow Architecture');
    
    // Check data flow container
    const dataFlowContainer = page.locator('#data-flow-container');
    await expect(dataFlowContainer).toBeVisible();
    await expect(dataFlowContainer).toHaveAttribute('role', 'img');
    await expect(dataFlowContainer).toHaveAttribute('aria-label');
    
    // Test keyboard accessibility
    await dataFlowContainer.focus();
    await expect(dataFlowContainer).toBeFocused();
    
    // Test demo button
    const demoButton = page.locator('#flow-demo-btn');
    await expect(demoButton).toBeVisible();
    await expect(demoButton).toContainText('Start Data Flow Demo');
  });

  test('should handle interactive demo workflow', async ({ page }) => {
    // Find demo section
    const demoSection = page.locator('.demo-preview').first();
    await expect(demoSection).toBeVisible();
    
    // Find and click demo button
    const demoButton = demoSection.locator('button').first();
    await expect(demoButton).toBeVisible();
    
    // Start demo
    await demoButton.click();
    
    // Check for loading state (should appear quickly)
    await expect(page.locator('.loading-overlay, .spinner-border, [aria-live]')).toBeVisible({ timeout: 5000 });
    
    // Wait for demo to process (with reasonable timeout)
    await page.waitForTimeout(3000);
    
    // Check for completion state or error handling
    const statusElements = page.locator('#demo-status, .toast, [role="status"], [role="alert"]');
    await expect(statusElements.first()).toBeVisible({ timeout: 15000 });
  });

  test('should be mobile responsive', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Hero section should be visible and readable
    const heroHeading = page.locator('h1#hero-heading');
    await expect(heroHeading).toBeVisible();
    
    // Navigation should be accessible
    const navigation = page.locator('nav[role="navigation"]');
    await expect(navigation).toBeVisible();
    
    // Check touch target sizes (minimum 44px)
    const interactiveElements = page.locator('button, .btn, a[role="button"], input, select');
    const elements = await interactiveElements.all();
    
    for (const element of elements.slice(0, 5)) { // Test first 5 elements
      const box = await element.boundingBox();
      if (box && await element.isVisible()) {
        expect(box.height).toBeGreaterThanOrEqual(44);
        // For some elements, width might be full-width, so only check if it's a small element
        if (box.width < 200) {
          expect(box.width).toBeGreaterThanOrEqual(44);
        }
      }
    }
    
    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(heroHeading).toBeVisible();
  });

  test('should meet performance benchmarks', async ({ page }) => {
    // Navigate and measure performance
    const startTime = Date.now();
    await page.goto('/', { waitUntil: 'networkidle' });
    const loadTime = Date.now() - startTime;
    
    // Basic load time check (should be under 5 seconds for E2E test)
    expect(loadTime).toBeLessThan(5000);
    
    // Check Core Web Vitals using Performance API
    const vitals = await page.evaluate(() => {
      return new Promise((resolve) => {
        const vitals = {};
        
        // Get navigation timing
        const navigation = performance.getEntriesByType('navigation')[0];
        if (navigation) {
          vitals.loadTime = navigation.loadEventEnd - navigation.fetchStart;
          vitals.domContentLoaded = navigation.domContentLoadedEventEnd - navigation.fetchStart;
        }
        
        // Try to get LCP
        let lcpObserver;
        try {
          lcpObserver = new PerformanceObserver((list) => {
            const entries = list.getEntries();
            const lastEntry = entries[entries.length - 1];
            vitals.lcp = lastEntry.startTime;
            lcpObserver.disconnect();
            resolve(vitals);
          });
          lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
          
          // Fallback timeout
          setTimeout(() => {
            if (lcpObserver) lcpObserver.disconnect();
            resolve(vitals);
          }, 3000);
        } catch (error) {
          resolve(vitals);
        }
      });
    });
    
    // Performance assertions
    if (vitals.loadTime) {
      expect(vitals.loadTime).toBeLessThan(4000); // 4 seconds
    }
    
    if (vitals.lcp) {
      expect(vitals.lcp).toBeLessThan(3000); // 3 seconds for E2E (more lenient than production)
    }
  });

  test('should handle errors gracefully', async ({ page }) => {
    // Test with network disabled for parts of the app
    await page.route('**/api/**', route => route.abort());
    
    // Try to interact with demo
    const demoButton = page.locator('.demo-preview button').first();
    if (await demoButton.count() > 0) {
      await demoButton.click();
      
      // Should show error handling
      await expect(page.locator('.toast, [role="alert"], .error-text')).toBeVisible({ timeout: 10000 });
    }
    
    // Re-enable network
    await page.unroute('**/api/**');
  });

  test('should support keyboard-only navigation', async ({ page }) => {
    let tabCount = 0;
    const maxTabs = 20;
    
    // Tab through interactive elements
    while (tabCount < maxTabs) {
      await page.keyboard.press('Tab');
      tabCount++;
      
      const focusedElement = page.locator(':focus');
      if (await focusedElement.count() > 0) {
        // Element should be visible when focused
        await expect(focusedElement).toBeVisible();
        
        // Test activation with keyboard
        const tagName = await focusedElement.getAttribute('tagName') || await focusedElement.evaluate(el => el.tagName);
        if (tagName && ['BUTTON', 'A'].includes(tagName.toUpperCase())) {
          // Test that Enter/Space work (without actually activating to avoid disrupting test flow)
          break;
        }
      }
    }
    
    // Should be able to navigate back with Shift+Tab
    await page.keyboard.press('Shift+Tab');
    const backFocusedElement = page.locator(':focus');
    await expect(backFocusedElement).toBeVisible();
  });

  test('should work with reduced motion preferences', async ({ page }) => {
    // Set reduced motion preference
    await page.emulateMedia({ reducedMotion: 'reduce' });
    
    // Reload page with reduced motion
    await page.reload();
    
    // Check that animations are disabled or minimal
    const animatedElements = page.locator('[class*="animate"], [style*="animation"], .loading-spinner');
    
    if (await animatedElements.count() > 0) {
      // Animations should either be removed or very short
      const element = animatedElements.first();
      const animationDuration = await element.evaluate(el => {
        const style = getComputedStyle(el);
        return style.animationDuration;
      });
      
      // Should be very short or none
      expect(['0s', '0.01ms', 'none', '']).toContain(animationDuration);
    }
  });
});
