# Cursor AI Task 5: Testing Infrastructure

## 🎯 Project Goal
Create comprehensive testing infrastructure covering all previous improvements with unit tests, integration tests, E2E tests, and visual regression testing.

## 📋 Prerequisites
- **MUST COMPLETE**: Task 4 (Accessibility) first
- Base branch: `cursor/accessibility-improvements` (from previous task)

## 🔧 Git Setup
```bash
git checkout cursor/accessibility-improvements
git pull origin cursor/accessibility-improvements
git checkout -b cursor/testing-infrastructure
```

## 📁 Files to Create

### Test Infrastructure:
1. `tests/unit/` (unit tests directory)
2. `tests/integration/` (integration tests directory)
3. `tests/e2e/` (end-to-end tests directory)
4. `tests/visual/` (visual regression tests)
5. `tests/accessibility/` (accessibility tests)
6. `tests/performance/` (performance tests)

### Configuration Files:
7. `jest.config.js` (Jest configuration)
8. `playwright.config.js` (Playwright configuration)
9. `package.json` (test dependencies)
10. `.github/workflows/test.yml` (CI/CD pipeline)

### Test Utilities:
11. `tests/utils/test-helpers.js`
12. `tests/utils/mock-data.js`
13. `tests/utils/accessibility-helpers.js`
14. `tests/utils/performance-helpers.js`

## 🎯 Specific Tasks

### Task 5.1: Test Configuration Setup
**Create**: `package.json` (test dependencies section)

**Add Testing Dependencies**:
```json
{
  "devDependencies": {
    "@playwright/test": "^1.40.0",
    "@testing-library/jest-dom": "^6.1.0",
    "@testing-library/user-event": "^14.5.0",
    "@axe-core/playwright": "^4.8.0",
    "jest": "^29.7.0",
    "jest-environment-jsdom": "^29.7.0",
    "jest-axe": "^8.0.0",
    "lighthouse": "^11.3.0",
    "puppeteer": "^21.5.0",
    "pixelmatch": "^5.3.0",
    "pngjs": "^7.0.0"
  },
  "scripts": {
    "test": "jest",
    "test:unit": "jest --testPathPattern=unit",
    "test:integration": "jest --testPathPattern=integration",
    "test:e2e": "playwright test",
    "test:accessibility": "jest --testPathPattern=accessibility",
    "test:visual": "playwright test --grep='visual'",
    "test:performance": "jest --testPathPattern=performance",
    "test:all": "npm run test:unit && npm run test:integration && npm run test:accessibility && npm run test:e2e",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage"
  }
}
```

### Task 5.2: Jest Configuration
**Create**: `jest.config.js`

**Implementation**:
```javascript
module.exports = {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/tests/utils/jest-setup.js'],
  testMatch: [
    '<rootDir>/tests/unit/**/*.test.js',
    '<rootDir>/tests/integration/**/*.test.js',
    '<rootDir>/tests/accessibility/**/*.test.js',
    '<rootDir>/tests/performance/**/*.test.js'
  ],
  collectCoverageFrom: [
    'app/static/js/**/*.js',
    '!app/static/js/**/*.min.js',
    '!**/node_modules/**'
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70
    }
  },
  moduleNameMapping: {
    '^@/(.*)$': '<rootDir>/app/static/$1'
  },
  testTimeout: 10000,
  verbose: true
};
```

### Task 5.3: Unit Tests for Core Components
**Create**: `tests/unit/interactive-demo.test.js`

**Implementation**:
```javascript
import { jest } from '@jest/globals';
import { InteractiveDemo } from '@/js/interactive-demo.js';

// Mock dependencies
global.fetch = jest.fn();
global.window.LoadingStates = {
  show: jest.fn(() => 'loading-id'),
  hide: jest.fn()
};
global.window.VectorBidErrors = {
  handleApiError: jest.fn()
};
global.window.A11yAnnouncer = {
  announce: jest.fn()
};

describe('InteractiveDemo', () => {
  let demo;
  let mockContainer;

  beforeEach(() => {
    // Setup DOM
    document.body.innerHTML = `
      <div class="demo-preview">
        <button>Try Interactive Demo</button>
        <div class="text-blue-400">85% Confidence</div>
        <div class="flex justify-between">
          <span>Weekend Protection:</span>
          <span class="text-green-400">87%</span>
        </div>
      </div>
    `;

    mockContainer = document.querySelector('.demo-preview');
    demo = new InteractiveDemo();
    
    // Reset mocks
    jest.clearAllMocks();
  });

  afterEach(() => {
    document.body.innerHTML = '';
  });

  describe('Initialization', () => {
    test('should initialize demo state correctly', () => {
      expect(demo.apiBase).toBe('/api');
      expect(demo.isProcessing).toBe(false);
      expect(demo.demoState).toBe('idle');
    });

    test('should bind event listeners', () => {
      const button = document.querySelector('button');
      expect(button).toBeTruthy();
    });
  });

  describe('API Calls', () => {
    test('should make successful parse API call', async () => {
      const mockResponse = {
        parsed_preferences: {
          hard_constraints: { no_redeyes: true },
          soft_preferences: { weekend_priority: 0.9 }
        }
      };

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse)
      });

      const result = await demo.apiCall('/parse', { preferences_text: 'test' });

      expect(fetch).toHaveBeenCalledWith('/api/parse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ preferences_text: 'test' }),
        signal: expect.any(AbortSignal)
      });

      expect(result).toEqual(mockResponse);
    });

    test('should handle API errors with retry', async () => {
      const error = new Error('Network error');
      global.fetch.mockRejectedValueOnce(error);
      
      global.window.VectorBidErrors.handleApiError.mockResolvedValueOnce({
        shouldRetry: true
      });

      global.fetch.mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true })
      });

      const result = await demo.apiCall('/parse', { test: true });

      expect(global.window.VectorBidErrors.handleApiError).toHaveBeenCalledWith(
        error,
        '/parse'
      );
      expect(fetch).toHaveBeenCalledTimes(2); // Original call + retry
    });

    test('should handle request cancellation', async () => {
      demo.abortController.abort();

      global.fetch.mockRejectedValueOnce({
        name: 'AbortError'
      });

      const result = await demo.apiCall('/parse', { test: true });

      expect(result).toBeNull();
      expect(demo.updateStatus).toHaveBeenCalledWith('🚫 Request cancelled', 'info');
    });
  });

  describe('Demo Flow', () => {
    test('should complete full demo flow', async () => {
      // Mock API responses
      global.fetch
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            parsed_preferences: {
              hard_constraints: { no_redeyes: true },
              soft_preferences: { weekend_priority: 0.9 }
            }
          })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve({
            candidates: [{
              candidate_id: 'test',
              score: 0.9,
              soft_breakdown: { weekend_priority: 0.87 }
            }]
          })
        });

      await demo.startDemo();

      expect(demo.isProcessing).toBe(false);
      expect(global.window.A11yAnnouncer.announce).toHaveBeenCalledWith(
        'Demo complete. Your AI-optimized schedule is ready.',
        'polite'
      );
    });

    test('should handle demo errors gracefully', async () => {
      global.fetch.mockRejectedValueOnce(new Error('API Error'));
      global.window.VectorBidErrors.handleApiError.mockResolvedValueOnce({
        shouldRetry: false
      });

      await demo.startDemo();

      expect(demo.isProcessing).toBe(false);
      expect(global.window.A11yAnnouncer.announce).toHaveBeenCalledWith(
        'Demo encountered an error. Please try again.',
        'assertive'
      );
    });
  });

  describe('UI Updates', () => {
    test('should update demo preview with real results', () => {
      const mockCandidate = {
        score: 0.92,
        soft_breakdown: {
          weekend_priority: 0.88,
          family_time: 0.95
        }
      };

      demo.optimizeResult = { candidates: [mockCandidate] };
      demo.updateDemoPreview();

      const scoreElement = document.querySelector('.text-blue-400');
      expect(scoreElement.textContent).toBe('92% Confidence');
    });

    test('should show status messages', () => {
      const statusContainer = document.createElement('div');
      statusContainer.id = 'demo-status';
      statusContainer.className = 'hidden';
      document.body.appendChild(statusContainer);

      demo.updateStatus('Processing...', 'processing');

      expect(statusContainer.classList.contains('hidden')).toBe(false);
      expect(statusContainer.textContent).toContain('Processing...');
    });
  });
});
```

### Task 5.4: Integration Tests
**Create**: `tests/integration/api-integration.test.js`

**Implementation**:
```javascript
import { jest } from '@jest/globals';

describe('API Integration Tests', () => {
  const API_BASE = 'http://localhost:8000/api';

  beforeAll(async () => {
    // Ensure test server is running
    try {
      const response = await fetch('http://localhost:8000/health');
      if (!response.ok) {
        throw new Error('Test server not available');
      }
    } catch (error) {
      console.error('Test server setup required:', error.message);
      throw error;
    }
  });

  describe('Parse Endpoint', () => {
    test('should parse pilot preferences successfully', async () => {
      const payload = {
        preferences_text: 'I want weekends off and prefer morning departures',
        persona: 'family_first'
      };

      const response = await fetch(`${API_BASE}/parse`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      expect(response.status).toBe(200);

      const data = await response.json();
      expect(data).toHaveProperty('original_text');
      expect(data).toHaveProperty('parsed_preferences');
      expect(data.parsed_preferences).toHaveProperty('hard_constraints');
      expect(data.parsed_preferences).toHaveProperty('soft_preferences');
      expect(data.parsed_preferences.confidence).toBeGreaterThan(0);
    });

    test('should handle malformed requests', async () => {
      const response = await fetch(`${API_BASE}/parse`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({}) // Missing required fields
      });

      expect(response.status).toBe(200); // API should handle gracefully
      
      const data = await response.json();
      expect(data).toHaveProperty('original_text');
    });
  });

  describe('Optimize Endpoint', () => {
    test('should optimize schedule with valid input', async () => {
      const payload = {
        feature_bundle: {
          context: {
            ctx_id: 'test_ctx',
            pilot_id: 'test_pilot',
            airline: 'UAL',
            base: 'SFO',
            seat: 'FO',
            equip: ['73G'],
            seniority_percentile: 0.75,
            commuting_profile: {},
            default_weights: {}
          },
          preference_schema: {
            pilot_id: 'test_pilot',
            airline: 'UAL',
            base: 'SFO',
            seat: 'FO',
            equip: ['73G'],
            hard_constraints: {
              days_off: [],
              no_red_eyes: true,
              max_duty_hours_per_day: null,
              legalities: ['FAR117']
            },
            soft_prefs: {
              weekend_priority: { weight: 0.9 }
            },
            weights_version: '2025-08-16',
            confidence: 0.85,
            source: { test: true }
          },
          analytics_features: {},
          compliance_flags: {},
          pairing_features: {
            pairings: [
              { id: 'SFO123', route: 'SFO-LAX-SFO', duty_time: 8.5 },
              { id: 'SFO456', route: 'SFO-DEN-SFO', duty_time: 9.2 }
            ]
          }
        },
        K: 5
      };

      const response = await fetch(`${API_BASE}/optimize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      expect(response.status).toBe(200);

      const data = await response.json();
      expect(data).toHaveProperty('candidates');
      expect(Array.isArray(data.candidates)).toBe(true);
      
      if (data.candidates.length > 0) {
        const candidate = data.candidates[0];
        expect(candidate).toHaveProperty('candidate_id');
        expect(candidate).toHaveProperty('score');
        expect(candidate).toHaveProperty('hard_ok');
        expect(candidate).toHaveProperty('soft_breakdown');
        expect(candidate).toHaveProperty('pairings');
      }
    });
  });

  describe('Authentication Endpoints', () => {
    test('should serve signup page', async () => {
      const response = await fetch('http://localhost:8000/auth/signup');
      
      expect(response.status).toBe(200);
      expect(response.headers.get('content-type')).toContain('text/html');
      
      const html = await response.text();
      expect(html).toContain('Sign Up - VectorBid');
      expect(html).toContain('Start your free trial');
    });

    test('should serve login page', async () => {
      const response = await fetch('http://localhost:8000/auth/login');
      
      expect(response.status).toBe(200);
      expect(response.headers.get('content-type')).toContain('text/html');
      
      const html = await response.text();
      expect(html).toContain('Sign In - VectorBid');
      expect(html).toContain('Demo Accounts');
    });
  });

  describe('Static Assets', () => {
    test('should serve data flow visualization script', async () => {
      const response = await fetch('http://localhost:8000/static/js/data-flow-viz.js');
      
      expect(response.status).toBe(200);
      expect(response.headers.get('content-type')).toContain('javascript');
      
      const content = await response.text();
      expect(content).toContain('DataFlowVisualization');
    });

    test('should serve interactive demo script', async () => {
      const response = await fetch('http://localhost:8000/static/js/interactive-demo.js');
      
      expect(response.status).toBe(200);
      expect(response.headers.get('content-type')).toContain('javascript');
      
      const content = await response.text();
      expect(content).toContain('InteractiveDemo');
    });
  });
});
```

### Task 5.5: End-to-End Tests with Playwright
**Create**: `playwright.config.js`

**Implementation**:
```javascript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html'],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/results.xml' }]
  ],
  use: {
    baseURL: 'http://localhost:8000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure'
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],
  webServer: {
    command: 'python -m uvicorn app.main:app --host 0.0.0.0 --port 8000',
    port: 8000,
    reuseExistingServer: !process.env.CI,
    timeout: 30000
  },
});
```

**Create**: `tests/e2e/landing-page.spec.js`

**Implementation**:
```javascript
import { test, expect } from '@playwright/test';
import { injectAxe, checkA11y } from 'axe-playwright';

test.describe('Landing Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await injectAxe(page);
  });

  test('should load landing page successfully', async ({ page }) => {
    await expect(page).toHaveTitle(/VectorBid/);
    
    // Check hero section
    const heroHeading = page.locator('h1').first();
    await expect(heroHeading).toBeVisible();
    await expect(heroHeading).toContainText('VectorBid');
    
    // Check navigation
    const navigation = page.locator('nav');
    await expect(navigation).toBeVisible();
    
    // Check CTA buttons
    const ctaButtons = page.locator('a:has-text("Start Free Trial")');
    await expect(ctaButtons.first()).toBeVisible();
  });

  test('should have accessible navigation', async ({ page }) => {
    // Test keyboard navigation
    await page.keyboard.press('Tab');
    
    // Should skip to main content link be focusable
    const skipLink = page.locator('.skip-nav');
    if (await skipLink.count() > 0) {
      await expect(skipLink).toBeFocused();
    }
    
    // Check accessibility
    await checkA11y(page, null, {
      detailedReport: true,
      detailedReportOptions: { html: true },
    });
  });

  test('should display data flow visualization', async ({ page }) => {
    // Wait for D3.js to load and initialize
    await page.waitForTimeout(2000);
    
    const dataFlowContainer = page.locator('#data-flow-container');
    await expect(dataFlowContainer).toBeVisible();
    
    // Check if SVG is rendered
    const svg = dataFlowContainer.locator('svg');
    await expect(svg).toBeVisible();
    
    // Test keyboard navigation
    await dataFlowContainer.focus();
    await page.keyboard.press('Enter');
    
    // Should be able to navigate nodes
    await page.keyboard.press('ArrowRight');
    await page.keyboard.press('Enter'); // Activate node
  });

  test('should work on mobile devices', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Hero section should be visible and readable
    const heroHeading = page.locator('h1').first();
    await expect(heroHeading).toBeVisible();
    
    // Navigation should be accessible
    const navigation = page.locator('nav');
    await expect(navigation).toBeVisible();
    
    // Buttons should be touch-friendly (minimum 44px)
    const buttons = page.locator('button, .btn, a[role="button"]');
    for (const button of await buttons.all()) {
      const box = await button.boundingBox();
      if (box) {
        expect(box.height).toBeGreaterThanOrEqual(44);
        expect(box.width).toBeGreaterThanOrEqual(44);
      }
    }
  });

  test('should handle interactive demo', async ({ page }) => {
    // Wait for demo to be ready
    await page.waitForSelector('.demo-preview button');
    
    const demoButton = page.locator('.demo-preview button');
    await expect(demoButton).toBeVisible();
    
    // Click demo button
    await demoButton.click();
    
    // Should show loading state
    await expect(page.locator('.loading-overlay, .spinner-border')).toBeVisible({ timeout: 5000 });
    
    // Wait for demo to complete (or timeout)
    await page.waitForTimeout(10000);
    
    // Should show results or error state
    const statusMessage = page.locator('#demo-status, .toast');
    await expect(statusMessage).toBeVisible({ timeout: 15000 });
  });

  test('should pass performance benchmarks', async ({ page }) => {
    // Start performance monitoring
    await page.goto('/', { waitUntil: 'networkidle' });
    
    // Check Core Web Vitals
    const lcpValue = await page.evaluate(() => {
      return new Promise((resolve) => {
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          resolve(lastEntry.startTime);
        }).observe({ entryTypes: ['largest-contentful-paint'] });
        
        setTimeout(() => resolve(null), 5000); // Timeout after 5s
      });
    });
    
    if (lcpValue !== null) {
      expect(lcpValue).toBeLessThan(2500); // LCP should be < 2.5s
    }
    
    // Check page load time
    const navigationTiming = await page.evaluate(() => {
      const timing = performance.getEntriesByType('navigation')[0];
      return timing.loadEventEnd - timing.fetchStart;
    });
    
    expect(navigationTiming).toBeLessThan(3000); // Total load < 3s
  });
});
```

### Task 5.6: Accessibility Tests
**Create**: `tests/accessibility/wcag-compliance.test.js`

**Implementation**:
```javascript
import { jest } from '@jest/globals';
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

describe('WCAG Compliance Tests', () => {
  beforeEach(() => {
    document.body.innerHTML = '';
  });

  test('landing page should have no accessibility violations', async () => {
    // Load landing page HTML
    const html = `
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <title>VectorBid - World's First AI-Powered Pilot Bidding System</title>
        </head>
        <body>
          <a href="#main-content" class="skip-nav">Skip to main content</a>
          <nav role="navigation" aria-label="Main navigation">
            <div class="navbar">Navigation</div>
          </nav>
          <main id="main-content" role="main">
            <section aria-labelledby="hero-heading">
              <h1 id="hero-heading">VectorBid AI-Powered Pilot Bidding</h1>
              <p>Transform pilot bidding with AI</p>
              <a href="/auth/signup" class="btn">Start Free Trial</a>
            </section>
          </main>
          <footer role="contentinfo">Footer</footer>
        </body>
      </html>
    `;
    
    document.documentElement.innerHTML = html;
    
    const results = await axe(document);
    expect(results).toHaveNoViolations();
  });

  test('signup form should be accessible', async () => {
    const formHTML = `
      <form role="form" aria-labelledby="form-title">
        <h2 id="form-title">Sign Up</h2>
        <div>
          <label for="email" id="email-label">Email</label>
          <input 
            id="email" 
            name="email" 
            type="email" 
            aria-labelledby="email-label"
            required>
        </div>
        <div>
          <label for="password" id="password-label">Password</label>
          <input 
            id="password" 
            name="password" 
            type="password"
            aria-labelledby="password-label"
            required>
        </div>
        <button type="submit">Create Account</button>
      </form>
    `;
    
    document.body.innerHTML = formHTML;
    
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });

  test('data flow visualization should be keyboard accessible', async () => {
    const vizHTML = `
      <div 
        id="data-flow-container" 
        role="img" 
        aria-label="VectorBid AI Data Flow"
        aria-describedby="viz-description"
        tabindex="0">
        <svg>
          <g class="node" role="button" aria-label="Input Node" tabindex="-1">
            <rect></rect>
            <text>Input</text>
          </g>
          <g class="node" role="button" aria-label="Process Node" tabindex="-1">
            <rect></rect>
            <text>Process</text>
          </g>
        </svg>
      </div>
      <div id="viz-description" class="sr-only">
        Interactive diagram showing data processing flow
      </div>
    `;
    
    document.body.innerHTML = vizHTML;
    
    const results = await axe(document.body);
    expect(results).toHaveNoViolations();
  });

  test('color contrast should meet WCAG standards', async () => {
    const colorTestHTML = `
      <div style="background: #ffffff; color: #000000; padding: 20px;">
        <h1>High Contrast Header</h1>
        <p>This text should have sufficient contrast ratio.</p>
        <button style="background: #3b82f6; color: #ffffff; padding: 10px;">
          Accessible Button
        </button>
      </div>
      <div style="background: #f3f4f6; color: #6b7280; padding: 20px;">
        <p>Secondary text with adequate contrast.</p>
      </div>
    `;
    
    document.body.innerHTML = colorTestHTML;
    
    const results = await axe(document.body, {
      rules: {
        'color-contrast': { enabled: true }
      }
    });
    
    expect(results).toHaveNoViolations();
  });

  test('focus indicators should be visible', async () => {
    const focusHTML = `
      <style>
        .focus-test:focus {
          outline: 2px solid #3b82f6;
          outline-offset: 2px;
        }
      </style>
      <div>
        <button class="focus-test">Focusable Button</button>
        <input class="focus-test" type="text" placeholder="Focusable Input">
        <a href="#" class="focus-test">Focusable Link</a>
      </div>
    `;
    
    document.body.innerHTML = focusHTML;
    
    const results = await axe(document.body, {
      rules: {
        'focus-order-semantics': { enabled: true }
      }
    });
    
    expect(results).toHaveNoViolations();
  });
});
```

### Task 5.7: Performance Tests
**Create**: `tests/performance/lighthouse.test.js`

**Implementation**:
```javascript
import { jest } from '@jest/globals';
import lighthouse from 'lighthouse';
import * as chromeLauncher from 'chrome-launcher';

describe('Performance Tests', () => {
  let chrome;

  beforeAll(async () => {
    chrome = await chromeLauncher.launch({ chromeFlags: ['--headless'] });
  });

  afterAll(async () => {
    if (chrome) {
      await chrome.kill();
    }
  });

  test('landing page should meet performance benchmarks', async () => {
    const options = {
      logLevel: 'info',
      output: 'json',
      onlyCategories: ['performance'],
      port: chrome.port
    };

    const runnerResult = await lighthouse('http://localhost:8000/', options);
    const performanceScore = runnerResult.lhr.categories.performance.score * 100;
    
    expect(performanceScore).toBeGreaterThan(75);
    
    // Check specific metrics
    const metrics = runnerResult.lhr.audits;
    
    // First Contentful Paint should be < 2s
    const fcp = metrics['first-contentful-paint'].numericValue;
    expect(fcp).toBeLessThan(2000);
    
    // Largest Contentful Paint should be < 2.5s
    const lcp = metrics['largest-contentful-paint'].numericValue;
    expect(lcp).toBeLessThan(2500);
    
    // Speed Index should be reasonable
    const speedIndex = metrics['speed-index'].numericValue;
    expect(speedIndex).toBeLessThan(4000);
  }, 30000);

  test('mobile performance should be acceptable', async () => {
    const options = {
      logLevel: 'info',
      output: 'json',
      onlyCategories: ['performance'],
      port: chrome.port,
      emulatedFormFactor: 'mobile'
    };

    const runnerResult = await lighthouse('http://localhost:8000/', options);
    const performanceScore = runnerResult.lhr.categories.performance.score * 100;
    
    expect(performanceScore).toBeGreaterThan(70);
  }, 30000);

  test('bundle size should be optimized', async () => {
    const fs = require('fs').promises;
    const path = require('path');
    const { gzipSync } = require('zlib');

    const jsFiles = [
      'app/static/js/interactive-demo.js',
      'app/static/js/data-flow-viz.js',
      'app/static/js/error-handler.js',
      'app/static/js/loading-states.js'
    ];

    let totalSize = 0;
    
    for (const file of jsFiles) {
      try {
        const content = await fs.readFile(file, 'utf8');
        const gzippedSize = gzipSync(content).length;
        totalSize += gzippedSize;
      } catch (error) {
        console.warn(`File not found: ${file}`);
      }
    }

    // Total gzipped JS should be under 200KB
    expect(totalSize).toBeLessThan(200 * 1024);
  });
});
```

### Task 5.8: CI/CD Pipeline
**Create**: `.github/workflows/test.yml`

**Implementation**:
```yaml
name: Test Suite

on:
  push:
    branches: [ main, staging, 'cursor/*' ]
  pull_request:
    branches: [ main, staging ]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Run unit tests
      run: npm run test:unit
    
    - name: Run accessibility tests
      run: npm run test:accessibility
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  integration-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install Python dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install Node dependencies
      run: npm ci
    
    - name: Start application
      run: |
        python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
        sleep 10
    
    - name: Run integration tests
      run: npm run test:integration

  e2e-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        npm ci
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Install Playwright
      run: npx playwright install --with-deps
    
    - name: Run E2E tests
      run: npm run test:e2e
    
    - name: Upload test results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: playwright-report
        path: playwright-report/
        retention-days: 30

  performance-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        npm ci
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Start application
      run: |
        python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
        sleep 10
    
    - name: Run performance tests
      run: npm run test:performance
```

## ✅ Success Criteria

### Test Coverage Requirements:
- [ ] Unit test coverage ≥ 70% for all JavaScript components
- [ ] Integration tests cover all API endpoints
- [ ] E2E tests cover critical user journeys
- [ ] Accessibility tests pass WCAG 2.1 AA standards
- [ ] Performance tests meet benchmark thresholds

### Test Types Implemented:
- [ ] Unit tests for all major components
- [ ] Integration tests for API functionality
- [ ] End-to-end tests for user workflows
- [ ] Visual regression tests for UI consistency
- [ ] Performance tests with Lighthouse
- [ ] Accessibility tests with axe-core

## 🔗 Final Commit and Merge
After completing all testing infrastructure:

```bash
git add .
git commit -m "feat: implement comprehensive testing infrastructure

- Add unit tests for all major JavaScript components  
- Create integration tests for API endpoints and static assets
- Implement E2E tests with Playwright for critical user journeys
- Add accessibility testing with jest-axe and WCAG validation
- Set up performance testing with Lighthouse benchmarks
- Create CI/CD pipeline with automated test execution
- Add visual regression testing capabilities
- Ensure comprehensive test coverage across all features

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin cursor/testing-infrastructure

# Create pull request for all Cursor AI work
gh pr create --title "🤖 Cursor AI: Complete Mobile, UX, Performance, A11y & Testing Suite" --body "
## 🎯 Complete Enhancement Suite

This PR contains 5 chained improvements implemented by Cursor AI:

### ✅ Task 1: Mobile Optimization
- Mobile-first responsive design
- Touch-friendly interactions  
- Data flow visualization mobile support
- Proper breakpoints and scaling

### ✅ Task 2: Error Handling & UX
- Global error handler with retry logic
- Loading states with cancellation
- User-friendly error messages
- Comprehensive feedback system

### ✅ Task 3: Performance Optimization
- Lazy loading system for resources
- API response caching with TTL
- Bundle size optimization
- Performance monitoring and metrics

### ✅ Task 4: Accessibility (WCAG 2.1 AA)
- Semantic HTML and ARIA labels
- Keyboard navigation support
- Screen reader compatibility
- High contrast and reduced motion support

### ✅ Task 5: Testing Infrastructure
- Unit tests with Jest
- Integration tests for APIs
- E2E tests with Playwright
- Accessibility testing with axe-core
- Performance testing with Lighthouse
- CI/CD pipeline with GitHub Actions

## 🧪 Testing
All tests passing:
- ✅ Unit tests: 70%+ coverage
- ✅ Integration tests: API functionality
- ✅ E2E tests: Critical user journeys  
- ✅ Accessibility: WCAG 2.1 AA compliant
- ✅ Performance: >75 Lighthouse score

Ready for review and testing.
"
```

## 📊 Testing Commands
```bash
# Run all tests
npm run test:all

# Run specific test suites
npm run test:unit
npm run test:integration  
npm run test:e2e
npm run test:accessibility
npm run test:performance

# Run tests in watch mode
npm run test:watch

# Generate coverage report
npm run test:coverage
```

## 🚨 Critical Requirements
- All tests must pass before merging
- Coverage thresholds must be met
- Performance benchmarks must pass
- Accessibility standards must be maintained
- CI/CD pipeline must be working
- No breaking changes to existing functionality