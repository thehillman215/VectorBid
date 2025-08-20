// Playwright Configuration for VectorBid E2E Testing
// Cross-browser end-to-end testing setup with accessibility and performance testing

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  // Test directory
  testDir: './tests/e2e',
  
  // Run tests in parallel
  fullyParallel: true,
  
  // Forbid test.only on CI
  forbidOnly: !!process.env.CI,
  
  // Retry configuration
  retries: process.env.CI ? 2 : 0,
  
  // Worker configuration
  workers: process.env.CI ? 1 : undefined,
  
  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'test-results/results.json' }],
    ['junit', { outputFile: 'test-results/results.xml' }],
    ['list'],
    process.env.CI ? ['github'] : ['line']
  ],
  
  // Global test configuration
  use: {
    // Base URL for tests
    baseURL: 'http://localhost:8000',
    
    // Trace configuration
    trace: 'on-first-retry',
    
    // Screenshot configuration
    screenshot: 'only-on-failure',
    
    // Video configuration
    video: 'retain-on-failure',
    
    // Action timeout
    actionTimeout: 30000,
    
    // Navigation timeout
    navigationTimeout: 30000,
    
    // Ignore HTTPS errors
    ignoreHTTPSErrors: true,
    
    // Viewport size
    viewport: { width: 1280, height: 720 },
    
    // User agent
    userAgent: 'VectorBid-Test-Agent'
  },
  
  // Test projects for different browsers and devices
  projects: [
    // Desktop browsers
    {
      name: 'chromium',
      use: { 
        ...devices['Desktop Chrome'],
        // Enable accessibility testing
        contextOptions: {
          reducedMotion: 'reduce'
        }
      },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    
    // Mobile devices
    {
      name: 'Mobile Chrome',
      use: { 
        ...devices['Pixel 5'],
        // Mobile-specific settings
        hasTouch: true,
        isMobile: true
      },
    },
    {
      name: 'Mobile Safari',
      use: { 
        ...devices['iPhone 12'],
        hasTouch: true,
        isMobile: true
      },
    },
    
    // Tablet devices
    {
      name: 'Tablet',
      use: {
        ...devices['iPad Pro'],
        hasTouch: true
      }
    },
    
    // Accessibility testing project
    {
      name: 'accessibility',
      use: {
        ...devices['Desktop Chrome'],
        contextOptions: {
          reducedMotion: 'reduce',
          forcedColors: 'active',
          colorScheme: 'dark'
        }
      },
      testMatch: ['**/*a11y*.spec.js', '**/*accessibility*.spec.js']
    },
    
    // Performance testing project
    {
      name: 'performance',
      use: {
        ...devices['Desktop Chrome'],
        launchOptions: {
          args: ['--enable-gpu-benchmarking', '--enable-threaded-compositing']
        }
      },
      testMatch: ['**/*performance*.spec.js', '**/*perf*.spec.js']
    }
  ],
  
  // Web server configuration
  webServer: {
    command: 'python -m uvicorn app.main:app --host 0.0.0.0 --port 8000',
    port: 8000,
    reuseExistingServer: !process.env.CI,
    timeout: 30000,
    env: {
      NODE_ENV: 'test',
      PYTHONPATH: '.'
    }
  },
  
  // Test output directory
  outputDir: 'test-results/',
  
  // Global setup and teardown
  globalSetup: './tests/utils/global-setup.js',
  globalTeardown: './tests/utils/global-teardown.js',
  
  // Test timeout
  timeout: 60000,
  
  // Expect timeout
  expect: {
    timeout: 10000,
    toHaveScreenshot: {
      mode: 'binary',
      animations: 'disabled'
    },
    toMatchSnapshot: {
      mode: 'binary'
    }
  },
  
  // Metadata
  metadata: {
    'test-framework': 'Playwright',
    'app-name': 'VectorBid',
    'environment': process.env.NODE_ENV || 'test'
  }
});
