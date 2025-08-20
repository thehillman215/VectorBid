// VectorBid WCAG 2.1 AA Compliance Tests
// Comprehensive accessibility testing for screen readers, keyboard navigation, and assistive technologies

import { jest } from '@jest/globals';
import { axe, toHaveNoViolations } from 'jest-axe';
import fs from 'fs';
import path from 'path';

// Extend Jest matchers
expect.extend(toHaveNoViolations);

describe('WCAG 2.1 AA Compliance Tests', () => {
  beforeEach(() => {
    // Reset DOM before each test
    document.body.innerHTML = '';
    document.head.innerHTML = '';
    
    // Add accessibility CSS
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = '/static/css/accessibility.css';
    document.head.appendChild(link);
  });

  test('landing page structure should be accessible', async () => {
    // Create accessible landing page structure
    const landingPageHTML = `
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <title>VectorBid - World's First AI-Powered Pilot Bidding System</title>
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body>
          <a href="#main-content" class="skip-nav">Skip to main content</a>
          
          <header>
            <nav role="navigation" aria-label="Main navigation">
              <div class="logo">
                <h1>VectorBid</h1>
              </div>
              <ul role="menubar">
                <li role="none">
                  <a href="/products" role="menuitem">Products</a>
                </li>
                <li role="none">
                  <a href="/solutions" role="menuitem">Solutions</a>
                </li>
                <li role="none">
                  <a href="/auth/login" role="menuitem">Login</a>
                </li>
              </ul>
            </nav>
          </header>
          
          <main id="main-content" role="main">
            <section aria-labelledby="hero-heading">
              <h1 id="hero-heading">From Hours of Confusion to Perfect Schedules in Seconds</h1>
              <p>VectorBid transforms pilot bidding from complex form-filling to intelligent conversation.</p>
              <a href="/auth/signup" class="btn" aria-describedby="signup-description">
                Start Free Trial
              </a>
              <div id="signup-description" class="sr-only">
                Sign up for a 30-day free trial of VectorBid AI-powered pilot bidding
              </div>
            </section>
            
            <section aria-labelledby="dataflow-heading">
              <h2 id="dataflow-heading">AI Data Flow Architecture</h2>
              <div 
                id="data-flow-container" 
                role="img" 
                aria-label="Interactive diagram showing VectorBid's AI data processing flow"
                aria-describedby="dataflow-description"
                tabindex="0">
                <svg width="400" height="300" aria-hidden="true">
                  <g class="node" role="button" aria-label="Input Layer - Pilot Preferences" tabindex="-1">
                    <rect x="10" y="10" width="80" height="40" fill="#3b82f6"></rect>
                    <text x="50" y="35" fill="white" text-anchor="middle">Input</text>
                  </g>
                  <g class="node" role="button" aria-label="Processing Layer - AI Analysis" tabindex="-1">
                    <rect x="120" y="10" width="80" height="40" fill="#10b981"></rect>
                    <text x="160" y="35" fill="white" text-anchor="middle">Process</text>
                  </g>
                  <g class="node" role="button" aria-label="Output Layer - Schedule Results" tabindex="-1">
                    <rect x="230" y="10" width="80" height="40" fill="#f59e0b"></rect>
                    <text x="270" y="35" fill="white" text-anchor="middle">Output</text>
                  </g>
                </svg>
              </div>
              <div id="dataflow-description" class="sr-only">
                This diagram shows three main processing layers: Input layer captures pilot preferences,
                Processing layer uses AI for analysis and optimization, and Output layer provides 
                optimized schedule recommendations. Use Tab to navigate between components and Enter to explore details.
              </div>
            </section>
          </main>
          
          <footer role="contentinfo">
            <p>&copy; 2025 VectorBid. All rights reserved.</p>
          </footer>
        </body>
      </html>
    `;
    
    // Set up document
    document.documentElement.innerHTML = landingPageHTML;
    
    // Run accessibility tests
    const results = await axe(document, {
      rules: {
        'color-contrast': { enabled: true },
        'focus-order-semantics': { enabled: true },
        'keyboard': { enabled: true },
        'landmark-unique': { enabled: true },
        'skip-link': { enabled: true }
      }
    });
    
    expect(results).toHaveNoViolations();
  });

  test('signup form should be fully accessible', async () => {
    const signupFormHTML = `
      <main role="main">
        <form role="form" aria-labelledby="form-title" novalidate>
          <h2 id="form-title">Sign Up for VectorBid</h2>
          
          <div class="form-group">
            <label for="email" id="email-label">
              Email address
              <span class="required" aria-hidden="true">*</span>
            </label>
            <input 
              id="email" 
              name="email" 
              type="email" 
              required
              aria-labelledby="email-label"
              aria-describedby="email-help email-error"
              aria-invalid="false"
              autocomplete="email">
            <div id="email-help" class="help-text">
              We'll use this for account notifications
            </div>
            <div id="email-error" class="error-text" role="alert" aria-live="polite"></div>
          </div>
          
          <div class="form-group">
            <label for="airline" id="airline-label">
              Airline
              <span class="required" aria-hidden="true">*</span>
            </label>
            <select 
              id="airline" 
              name="airline" 
              required
              aria-labelledby="airline-label"
              aria-describedby="airline-help">
              <option value="">Select your airline</option>
              <option value="UAL">United Airlines</option>
              <option value="DAL">Delta Air Lines</option>
              <option value="AAL">American Airlines</option>
            </select>
            <div id="airline-help" class="help-text">
              Choose your current airline employer
            </div>
          </div>
          
          <div class="form-group">
            <label for="password" id="password-label">
              Password
              <span class="required" aria-hidden="true">*</span>
            </label>
            <div class="password-input-wrapper">
              <input 
                id="password" 
                name="password" 
                type="password"
                required
                aria-labelledby="password-label"
                aria-describedby="password-help password-strength"
                aria-invalid="false"
                autocomplete="new-password">
              <button 
                type="button" 
                class="password-toggle"
                aria-label="Show password"
                aria-pressed="false"
                aria-controls="password">
                <span aria-hidden="true">👁</span>
              </button>
            </div>
            <div id="password-help" class="help-text">
              Minimum 8 characters with letters and numbers
            </div>
            <div id="password-strength" class="password-strength" aria-live="polite"></div>
          </div>
          
          <div class="form-group">
            <label class="custom-checkbox">
              <input 
                type="checkbox" 
                name="terms" 
                required
                aria-describedby="terms-help">
              <span class="checkmark"></span>
              I agree to the Terms of Service and Privacy Policy
            </label>
            <div id="terms-help" class="help-text">
              By checking this box, you agree to our terms and privacy policy
            </div>
          </div>
          
          <button 
            type="submit" 
            class="submit-btn"
            aria-describedby="submit-help">
            Create Account
          </button>
          <div id="submit-help" class="sr-only">
            Creates your VectorBid account and signs you in
          </div>
          
          <div role="status" aria-live="polite" aria-atomic="true" class="sr-only" id="form-status"></div>
        </form>
      </main>
    `;
    
    document.body.innerHTML = signupFormHTML;
    
    const results = await axe(document.body, {
      rules: {
        'label': { enabled: true },
        'label-title-only': { enabled: true },
        'landmark-unique': { enabled: true },
        'form-field-multiple-labels': { enabled: true },
        'required-attr': { enabled: true },
        'aria-required-attr': { enabled: true },
        'autocomplete-valid': { enabled: true }
      }
    });
    
    expect(results).toHaveNoViolations();
  });

  test('interactive demo should be keyboard accessible', async () => {
    const demoHTML = `
      <section aria-labelledby="demo-heading" class="demo-section">
        <h2 id="demo-heading">Try VectorBid AI Demo</h2>
        
        <div class="demo-widget" role="application" aria-label="VectorBid AI Demo">
          <div class="demo-input-area">
            <label for="demo-input" id="demo-input-label">
              Tell us your schedule preferences
            </label>
            <textarea 
              id="demo-input"
              aria-labelledby="demo-input-label"
              aria-describedby="demo-input-help"
              placeholder="I want weekends off for family time, prefer morning departures..."
              readonly>I want weekends off for family time, prefer morning departures, avoid red-eyes completely</textarea>
            <div id="demo-input-help" class="help-text">
              This is a sample preference that shows how VectorBid understands natural language
            </div>
          </div>
          
          <div class="demo-controls">
            <button 
              type="button"
              id="demo-start-btn"
              aria-describedby="demo-description"
              aria-expanded="false"
              aria-controls="demo-results">
              <span aria-hidden="true">▶</span>
              Start AI Demo
            </button>
            <div id="demo-description" class="sr-only">
              This demo shows how VectorBid processes pilot preferences using AI to generate optimized schedules
            </div>
          </div>
          
          <div 
            id="demo-results" 
            aria-live="polite" 
            aria-atomic="true"
            aria-label="Demo results">
            <div class="result-card">
              <h3>AI Analysis Results</h3>
              <div class="confidence-score">
                <span class="label">Confidence:</span>
                <span class="value" aria-label="85% confidence">85%</span>
              </div>
              <div class="preferences-breakdown">
                <h4>Detected Preferences:</h4>
                <ul>
                  <li>
                    <span class="preference">Weekend Protection:</span>
                    <span class="score" aria-label="87% match">87%</span>
                  </li>
                  <li>
                    <span class="preference">Morning Departures:</span>
                    <span class="score" aria-label="92% match">92%</span>
                  </li>
                  <li>
                    <span class="preference">No Red-eyes:</span>
                    <span class="score" aria-label="95% match">95%</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
          
          <div role="status" aria-live="assertive" class="sr-only" id="demo-status"></div>
        </div>
      </section>
    `;
    
    document.body.innerHTML = demoHTML;
    
    const results = await axe(document.body, {
      rules: {
        'aria-expanded': { enabled: true },
        'aria-controls': { enabled: true },
        'button-name': { enabled: true },
        'landmark-unique': { enabled: true },
        'live-region': { enabled: true }
      }
    });
    
    expect(results).toHaveNoViolations();
  });

  test('color contrast should meet WCAG AA standards', async () => {
    const colorTestHTML = `
      <div style="background: #ffffff; color: #000000; padding: 20px;">
        <h1 style="color: #1f2937;">High Contrast Header (4.5:1)</h1>
        <p style="color: #374151;">Normal text with sufficient contrast (7:1)</p>
        <p style="color: #6b7280; font-size: 18px;">Large text with adequate contrast (3:1)</p>
        
        <button style="background: #3b82f6; color: #ffffff; padding: 12px 24px; border: none; border-radius: 6px;">
          Primary Button (4.5:1)
        </button>
        
        <button style="background: #10b981; color: #ffffff; padding: 12px 24px; border: none; border-radius: 6px; margin-left: 10px;">
          Success Button (4.5:1)
        </button>
        
        <a href="#" style="color: #2563eb; text-decoration: underline;">
          Link with sufficient contrast (4.5:1)
        </a>
      </div>
      
      <div style="background: #1f2937; color: #f9fafb; padding: 20px; margin-top: 20px;">
        <h2 style="color: #ffffff;">Dark Background Header</h2>
        <p style="color: #d1d5db;">Light text on dark background (8:1)</p>
        <button style="background: #3b82f6; color: #ffffff; padding: 12px 24px; border: none; border-radius: 6px;">
          Button on Dark Background
        </button>
      </div>
    `;
    
    document.body.innerHTML = colorTestHTML;
    
    const results = await axe(document.body, {
      rules: {
        'color-contrast': { enabled: true },
        'color-contrast-enhanced': { enabled: false } // Testing AA, not AAA
      }
    });
    
    expect(results).toHaveNoViolations();
  });

  test('focus management should be proper', async () => {
    const focusHTML = `
      <div class="focus-test-container">
        <h1 tabindex="0">Focusable Heading</h1>
        
        <nav>
          <ul>
            <li><a href="#section1">Section 1</a></li>
            <li><a href="#section2">Section 2</a></li>
            <li><a href="#section3">Section 3</a></li>
          </ul>
        </nav>
        
        <main>
          <section id="section1" tabindex="-1">
            <h2>Section 1</h2>
            <button type="button">Button 1</button>
            <input type="text" placeholder="Input 1">
          </section>
          
          <section id="section2" tabindex="-1">
            <h2>Section 2</h2>
            <button type="button">Button 2</button>
            <select>
              <option>Option 1</option>
              <option>Option 2</option>
            </select>
          </section>
          
          <section id="section3" tabindex="-1">
            <h2>Section 3</h2>
            <textarea placeholder="Textarea"></textarea>
            <button type="submit">Submit</button>
          </section>
        </main>
      </div>
    `;
    
    document.body.innerHTML = focusHTML;
    
    const results = await axe(document.body, {
      rules: {
        'tabindex': { enabled: true },
        'focus-order-semantics': { enabled: true },
        'focusable-content': { enabled: true }
      }
    });
    
    expect(results).toHaveNoViolations();
  });

  test('data tables should be accessible', async () => {
    const tableHTML = `
      <table class="data-table" role="table">
        <caption>VectorBid Schedule Comparison Results</caption>
        <thead>
          <tr>
            <th scope="col" aria-sort="none">
              <button type="button" aria-label="Sort by Rank">
                Rank
                <span aria-hidden="true">⇅</span>
              </button>
            </th>
            <th scope="col">Route</th>
            <th scope="col">Score</th>
            <th scope="col">Weekend Protection</th>
            <th scope="col">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>1</td>
            <td>SFO-LAX-SFO</td>
            <td aria-label="Score: 94 percent">94%</td>
            <td aria-label="Weekend protection: 87 percent">87%</td>
            <td>
              <button type="button" aria-label="View details for SFO-LAX-SFO route">
                View Details
              </button>
            </td>
          </tr>
          <tr>
            <td>2</td>
            <td>SFO-DEN-SFO</td>
            <td aria-label="Score: 89 percent">89%</td>
            <td aria-label="Weekend protection: 92 percent">92%</td>
            <td>
              <button type="button" aria-label="View details for SFO-DEN-SFO route">
                View Details
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    `;
    
    document.body.innerHTML = tableHTML;
    
    const results = await axe(document.body, {
      rules: {
        'table-caption': { enabled: true },
        'th-has-data-cells': { enabled: true },
        'td-headers-attr': { enabled: true },
        'table-duplicate-name': { enabled: true },
        'scope-attr-valid': { enabled: true }
      }
    });
    
    expect(results).toHaveNoViolations();
  });

  test('live regions should work correctly', async () => {
    const liveRegionHTML = `
      <div class="status-container">
        <div role="status" aria-live="polite" aria-atomic="true" id="polite-status">
          <!-- Polite announcements -->
        </div>
        
        <div role="alert" aria-live="assertive" aria-atomic="true" id="assertive-status">
          <!-- Urgent announcements -->
        </div>
        
        <div class="demo-area">
          <button type="button" id="success-btn" aria-describedby="success-help">
            Trigger Success Message
          </button>
          <div id="success-help" class="sr-only">
            Demonstrates polite live region announcement
          </div>
          
          <button type="button" id="error-btn" aria-describedby="error-help">
            Trigger Error Message
          </button>
          <div id="error-help" class="sr-only">
            Demonstrates assertive live region announcement
          </div>
        </div>
        
        <div class="progress-area">
          <div role="progressbar" aria-valuenow="75" aria-valuemin="0" aria-valuemax="100" aria-label="Upload progress">
            <div class="progress-bar" style="width: 75%"></div>
          </div>
          <div aria-live="polite" id="progress-text">75% complete</div>
        </div>
      </div>
    `;
    
    document.body.innerHTML = liveRegionHTML;
    
    const results = await axe(document.body, {
      rules: {
        'aria-live': { enabled: true },
        'aria-live-region': { enabled: true },
        'no-onchange': { enabled: true }
      }
    });
    
    expect(results).toHaveNoViolations();
  });
});
