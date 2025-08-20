# Cursor Handoff: Phase 1 - Core Navigation & Design System
## Foundation for World-Class SaaS Platform

---

## Overview
Transform VectorBid's foundation with a professional design system and complete navigation structure. This phase creates the infrastructure for a world-class aviation SaaS platform.

**Timeline**: 5-7 days
**Goal**: Professional, consistent foundation that supports entire website architecture

---

## Task 1: Design System Implementation

### 1.1 Create Professional CSS Design System
**File**: `app/static/css/design-system.css`

```css
/* VectorBid Professional Design System */
/* Based on aviation industry standards (ForeFlight, FlightAware) */

:root {
  /* Primary Color Palette */
  --primary-blue: #1e40af;        /* Trust, reliability */
  --primary-dark: #1e293b;        /* Professional depth */
  --accent-blue: #3b82f6;         /* Interactive elements */
  
  /* Neutral Palette */
  --gray-50: #f8fafc;             /* Page backgrounds */
  --gray-100: #f1f5f9;            /* Card backgrounds */
  --gray-200: #e2e8f0;            /* Borders */
  --gray-300: #cbd5e1;            /* Form borders */
  --gray-400: #94a3b8;            /* Placeholders */
  --gray-500: #64748b;            /* Secondary text */
  --gray-600: #475569;            /* Body text */
  --gray-700: #334155;            /* Headings */
  --gray-800: #1e293b;            /* Dark headings */
  --gray-900: #0f172a;            /* Primary headings */
  
  /* Functional Colors */
  --success: #10b981;             /* Successful bids */
  --warning: #f59e0b;             /* Warnings, constraints */
  --error: #ef4444;               /* Violations, errors */
  --info: #06b6d4;                /* Tips, information */
  
  /* Typography */
  --font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', Consolas, monospace;
  
  /* Font Sizes */
  --text-xs: 0.75rem;             /* 12px */
  --text-sm: 0.875rem;            /* 14px */
  --text-base: 1rem;              /* 16px */
  --text-lg: 1.125rem;            /* 18px */
  --text-xl: 1.25rem;             /* 20px */
  --text-2xl: 1.5rem;             /* 24px */
  --text-3xl: 1.875rem;           /* 30px */
  --text-4xl: 2.25rem;            /* 36px */
  --text-5xl: 3rem;               /* 48px */
  
  /* Spacing Scale */
  --space-1: 0.25rem;             /* 4px */
  --space-2: 0.5rem;              /* 8px */
  --space-3: 0.75rem;             /* 12px */
  --space-4: 1rem;                /* 16px */
  --space-5: 1.25rem;             /* 20px */
  --space-6: 1.5rem;              /* 24px */
  --space-8: 2rem;                /* 32px */
  --space-10: 2.5rem;             /* 40px */
  --space-12: 3rem;               /* 48px */
  --space-16: 4rem;               /* 64px */
  --space-20: 5rem;               /* 80px */
  --space-24: 6rem;               /* 96px */
  
  /* Border Radius */
  --radius-sm: 0.25rem;           /* 4px */
  --radius: 0.5rem;               /* 8px */
  --radius-lg: 0.75rem;           /* 12px */
  --radius-xl: 1rem;              /* 16px */
  
  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07), 0 2px 4px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1), 0 4px 6px rgba(0, 0, 0, 0.05);
  --shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.1), 0 10px 10px rgba(0, 0, 0, 0.04);
  
  /* Transitions */
  --transition-fast: 150ms ease-in-out;
  --transition: 200ms ease-in-out;
  --transition-slow: 300ms ease-in-out;
}

/* Base Styles */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  font-family: var(--font-family);
  font-size: 16px;
  line-height: 1.6;
  color: var(--gray-600);
  background-color: var(--gray-50);
  scroll-behavior: smooth;
}

body {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Typography */
h1, h2, h3, h4, h5, h6 {
  font-weight: 600;
  color: var(--gray-900);
  line-height: 1.2;
  margin-bottom: var(--space-4);
}

h1 { font-size: var(--text-4xl); }
h2 { font-size: var(--text-3xl); }
h3 { font-size: var(--text-2xl); }
h4 { font-size: var(--text-xl); }
h5 { font-size: var(--text-lg); }
h6 { font-size: var(--text-base); }

p {
  margin-bottom: var(--space-4);
  color: var(--gray-600);
}

a {
  color: var(--primary-blue);
  text-decoration: none;
  transition: color var(--transition);
}

a:hover {
  color: var(--accent-blue);
}

/* Utility Classes */
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--space-4);
}

.container-wide {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 var(--space-4);
}

.text-center { text-align: center; }
.text-left { text-align: left; }
.text-right { text-align: right; }

.font-medium { font-weight: 500; }
.font-semibold { font-weight: 600; }
.font-bold { font-weight: 700; }

.text-primary { color: var(--primary-blue); }
.text-success { color: var(--success); }
.text-warning { color: var(--warning); }
.text-error { color: var(--error); }
.text-gray { color: var(--gray-500); }

/* Layout Utilities */
.flex { display: flex; }
.flex-col { flex-direction: column; }
.items-center { align-items: center; }
.justify-center { justify-content: center; }
.justify-between { justify-content: space-between; }
.space-x-4 > * + * { margin-left: var(--space-4); }
.space-y-4 > * + * { margin-top: var(--space-4); }

/* Grid System */
.grid { display: grid; }
.grid-cols-1 { grid-template-columns: repeat(1, 1fr); }
.grid-cols-2 { grid-template-columns: repeat(2, 1fr); }
.grid-cols-3 { grid-template-columns: repeat(3, 1fr); }
.grid-cols-4 { grid-template-columns: repeat(4, 1fr); }
.gap-4 { gap: var(--space-4); }
.gap-6 { gap: var(--space-6); }
.gap-8 { gap: var(--space-8); }

/* Responsive Design */
@media (max-width: 768px) {
  .container {
    padding: 0 var(--space-3);
  }
  
  .grid-cols-2,
  .grid-cols-3,
  .grid-cols-4 {
    grid-template-columns: 1fr;
  }
}
```

### 1.2 Component Library Files
Create these component stylesheets:

**File**: `app/static/css/components/buttons.css`
```css
/* Button Components */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-3) var(--space-6);
  font-size: var(--text-base);
  font-weight: 500;
  border-radius: var(--radius);
  border: 1px solid transparent;
  text-decoration: none;
  cursor: pointer;
  transition: all var(--transition);
  white-space: nowrap;
}

.btn-primary {
  background-color: var(--primary-blue);
  color: white;
  border-color: var(--primary-blue);
}

.btn-primary:hover {
  background-color: var(--primary-dark);
  border-color: var(--primary-dark);
  color: white;
}

.btn-secondary {
  background-color: white;
  color: var(--gray-700);
  border-color: var(--gray-300);
}

.btn-secondary:hover {
  background-color: var(--gray-50);
  border-color: var(--gray-400);
}

.btn-outline {
  background-color: transparent;
  color: var(--primary-blue);
  border-color: var(--primary-blue);
}

.btn-outline:hover {
  background-color: var(--primary-blue);
  color: white;
}

.btn-lg {
  padding: var(--space-4) var(--space-8);
  font-size: var(--text-lg);
}

.btn-sm {
  padding: var(--space-2) var(--space-4);
  font-size: var(--text-sm);
}

.btn-icon {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
```

**File**: `app/static/css/components/cards.css`
```css
/* Card Components */
.card {
  background: white;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
  box-shadow: var(--shadow-sm);
  transition: box-shadow var(--transition);
}

.card:hover {
  box-shadow: var(--shadow-md);
}

.card-header {
  border-bottom: 1px solid var(--gray-200);
  padding-bottom: var(--space-4);
  margin-bottom: var(--space-4);
}

.card-title {
  font-size: var(--text-xl);
  font-weight: 600;
  color: var(--gray-900);
  margin-bottom: var(--space-2);
}

.card-description {
  color: var(--gray-600);
  font-size: var(--text-sm);
}

.card-content {
  flex: 1;
}

.card-footer {
  border-top: 1px solid var(--gray-200);
  padding-top: var(--space-4);
  margin-top: var(--space-6);
}

.card-interactive {
  cursor: pointer;
  transition: all var(--transition);
}

.card-interactive:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}
```

**File**: `app/static/css/components/forms.css`
```css
/* Form Components */
.form-group {
  margin-bottom: var(--space-4);
}

.form-label {
  display: block;
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--gray-700);
  margin-bottom: var(--space-2);
}

.form-input {
  width: 100%;
  padding: var(--space-3) var(--space-4);
  border: 1px solid var(--gray-300);
  border-radius: var(--radius);
  font-size: var(--text-base);
  transition: border-color var(--transition);
}

.form-input:focus {
  outline: none;
  border-color: var(--primary-blue);
  box-shadow: 0 0 0 3px rgba(30, 64, 175, 0.1);
}

.form-textarea {
  min-height: 120px;
  resize: vertical;
}

.form-select {
  background-image: url("data:image/svg+xml;charset=utf-8,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3E%3Cpath stroke='%236b7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3E%3C/svg%3E");
  background-position: right var(--space-3) center;
  background-repeat: no-repeat;
  background-size: 16px;
  padding-right: var(--space-10);
}

.form-checkbox {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.form-error {
  color: var(--error);
  font-size: var(--text-sm);
  margin-top: var(--space-1);
}

.form-help {
  color: var(--gray-500);
  font-size: var(--text-sm);
  margin-top: var(--space-1);
}
```

---

## Task 2: Navigation System Implementation

### 2.1 Header Navigation Component
**File**: `app/templates/components/header.html`

```html
<header class="site-header">
  <nav class="primary-nav">
    <div class="container">
      <div class="nav-wrapper">
        <!-- Logo -->
        <a href="/" class="logo">
          <i class="fas fa-plane" aria-hidden="true"></i>
          <span>VectorBid</span>
        </a>

        <!-- Desktop Navigation -->
        <ul class="nav-menu" id="nav-menu">
          <li class="nav-item dropdown">
            <a href="/products" class="nav-link">
              Products
              <i class="fas fa-chevron-down" aria-hidden="true"></i>
            </a>
            <ul class="dropdown-menu">
              <li><a href="/products/bid-optimizer" class="dropdown-link">
                <div class="dropdown-item">
                  <strong>Bid Optimizer</strong>
                  <span>AI-powered schedule optimization</span>
                </div>
              </a></li>
              <li><a href="/products/route-analyzer" class="dropdown-link">
                <div class="dropdown-item">
                  <strong>Route Analyzer</strong>
                  <span>Smart pattern recognition</span>
                </div>
              </a></li>
              <li><a href="/products/schedule-builder" class="dropdown-link">
                <div class="dropdown-item">
                  <strong>Schedule Builder</strong>
                  <span>Conflict-free construction</span>
                </div>
              </a></li>
              <li><a href="/products/pattern-intelligence" class="dropdown-link">
                <div class="dropdown-item">
                  <strong>Pattern Intelligence</strong>
                  <span>Predictive analytics</span>
                </div>
              </a></li>
              <li><a href="/products/mobile" class="dropdown-link">
                <div class="dropdown-item">
                  <strong>Mobile App</strong>
                  <span>Bid from anywhere</span>
                </div>
              </a></li>
              <li class="dropdown-separator"></li>
              <li><a href="/products/comparison" class="dropdown-link">Feature Comparison</a></li>
              <li><a href="/products/whats-new" class="dropdown-link">What's New</a></li>
            </ul>
          </li>

          <li class="nav-item dropdown">
            <a href="/solutions" class="nav-link">
              Solutions
              <i class="fas fa-chevron-down" aria-hidden="true"></i>
            </a>
            <ul class="dropdown-menu">
              <li class="dropdown-category">By Airline Type</li>
              <li><a href="/solutions/regional" class="dropdown-link">Regional Airlines</a></li>
              <li><a href="/solutions/major" class="dropdown-link">Major Airlines</a></li>
              <li><a href="/solutions/cargo" class="dropdown-link">Cargo Airlines</a></li>
              <li><a href="/solutions/corporate" class="dropdown-link">Corporate Aviation</a></li>
              
              <li class="dropdown-separator"></li>
              <li class="dropdown-category">By Role</li>
              <li><a href="/solutions/first-officers" class="dropdown-link">First Officers</a></li>
              <li><a href="/solutions/captains" class="dropdown-link">Captains</a></li>
              <li><a href="/solutions/check-airmen" class="dropdown-link">Check Airmen</a></li>
              
              <li class="dropdown-separator"></li>
              <li><a href="/solutions/customer-stories" class="dropdown-link">Customer Stories</a></li>
              <li><a href="/solutions/roi-calculator" class="dropdown-link">ROI Calculator</a></li>
            </ul>
          </li>

          <li class="nav-item dropdown">
            <a href="/resources" class="nav-link">
              Resources
              <i class="fas fa-chevron-down" aria-hidden="true"></i>
            </a>
            <ul class="dropdown-menu">
              <li class="dropdown-category">Getting Started</li>
              <li><a href="/resources/quick-start" class="dropdown-link">Quick Start Guide</a></li>
              <li><a href="/resources/tutorials" class="dropdown-link">Video Tutorials</a></li>
              <li><a href="/resources/demo" class="dropdown-link">Interactive Demo</a></li>
              
              <li class="dropdown-separator"></li>
              <li class="dropdown-category">Documentation</li>
              <li><a href="/resources/user-guide" class="dropdown-link">User Guide</a></li>
              <li><a href="/resources/api" class="dropdown-link">API Reference</a></li>
              <li><a href="/resources/integrations" class="dropdown-link">Integrations</a></li>
              
              <li class="dropdown-separator"></li>
              <li class="dropdown-category">Support</li>
              <li><a href="/support" class="dropdown-link">Help Center</a></li>
              <li><a href="/community" class="dropdown-link">Community</a></li>
              <li><a href="/status" class="dropdown-link">System Status</a></li>
            </ul>
          </li>

          <li class="nav-item">
            <a href="/pricing" class="nav-link">Pricing</a>
          </li>
        </ul>

        <!-- Auth Actions -->
        <div class="nav-actions">
          <a href="/login" class="btn btn-secondary">Login</a>
          <a href="/signup" class="btn btn-primary">Start Free Trial</a>
        </div>

        <!-- Mobile Menu Toggle -->
        <button class="mobile-menu-toggle" id="mobile-menu-toggle" aria-label="Toggle mobile menu">
          <span class="hamburger-line"></span>
          <span class="hamburger-line"></span>
          <span class="hamburger-line"></span>
        </button>
      </div>
    </div>
  </nav>
</header>
```

### 2.2 Navigation Styles
**File**: `app/static/css/components/navigation.css`

```css
/* Navigation Styles */
.site-header {
  background: white;
  border-bottom: 1px solid var(--gray-200);
  position: sticky;
  top: 0;
  z-index: 1000;
  box-shadow: var(--shadow-sm);
}

.primary-nav {
  height: 72px;
}

.nav-wrapper {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
}

.logo {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--primary-blue);
  text-decoration: none;
}

.logo i {
  font-size: var(--text-2xl);
}

.nav-menu {
  display: flex;
  align-items: center;
  gap: var(--space-8);
  list-style: none;
  margin: 0;
  padding: 0;
}

.nav-item {
  position: relative;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-2) 0;
  color: var(--gray-700);
  font-weight: 500;
  text-decoration: none;
  transition: color var(--transition);
}

.nav-link:hover {
  color: var(--primary-blue);
}

.nav-link i {
  font-size: var(--text-xs);
  transition: transform var(--transition);
}

/* Dropdown Menus */
.dropdown-menu {
  position: absolute;
  top: 100%;
  left: 0;
  min-width: 280px;
  background: white;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  padding: var(--space-2) 0;
  list-style: none;
  margin: 0;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-10px);
  transition: all var(--transition);
  z-index: 1000;
}

.dropdown:hover .dropdown-menu {
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
}

.dropdown:hover .nav-link i {
  transform: rotate(180deg);
}

.dropdown-category {
  padding: var(--space-2) var(--space-4);
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--gray-500);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.dropdown-link {
  display: block;
  padding: var(--space-3) var(--space-4);
  color: var(--gray-700);
  text-decoration: none;
  transition: background-color var(--transition);
}

.dropdown-link:hover {
  background-color: var(--gray-50);
  color: var(--primary-blue);
}

.dropdown-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.dropdown-item span {
  font-size: var(--text-sm);
  color: var(--gray-500);
}

.dropdown-separator {
  height: 1px;
  background: var(--gray-200);
  margin: var(--space-2) 0;
}

.nav-actions {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

/* Mobile Menu */
.mobile-menu-toggle {
  display: none;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  width: 40px;
  height: 40px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
}

.hamburger-line {
  width: 24px;
  height: 2px;
  background: var(--gray-700);
  margin: 2px 0;
  transition: all var(--transition);
}

/* Mobile Responsive */
@media (max-width: 1024px) {
  .nav-menu {
    gap: var(--space-4);
  }
  
  .dropdown-menu {
    min-width: 240px;
  }
}

@media (max-width: 768px) {
  .nav-menu,
  .nav-actions {
    display: none;
  }
  
  .mobile-menu-toggle {
    display: flex;
  }
  
  /* Mobile menu overlay styles to be implemented */
  .mobile-menu-active .nav-menu {
    display: flex;
    position: fixed;
    top: 72px;
    left: 0;
    right: 0;
    bottom: 0;
    background: white;
    flex-direction: column;
    padding: var(--space-6);
    z-index: 999;
  }
  
  .mobile-menu-active .hamburger-line:nth-child(1) {
    transform: rotate(45deg) translate(5px, 5px);
  }
  
  .mobile-menu-active .hamburger-line:nth-child(2) {
    opacity: 0;
  }
  
  .mobile-menu-active .hamburger-line:nth-child(3) {
    transform: rotate(-45deg) translate(7px, -6px);
  }
}
```

### 2.3 Navigation JavaScript
**File**: `app/static/js/navigation.js`

```javascript
// Navigation Functionality
class Navigation {
  constructor() {
    this.mobileMenuToggle = document.getElementById('mobile-menu-toggle');
    this.navMenu = document.getElementById('nav-menu');
    this.dropdowns = document.querySelectorAll('.dropdown');
    
    this.init();
  }
  
  init() {
    this.setupMobileMenu();
    this.setupDropdowns();
    this.setupKeyboardNavigation();
  }
  
  setupMobileMenu() {
    if (this.mobileMenuToggle) {
      this.mobileMenuToggle.addEventListener('click', () => {
        document.body.classList.toggle('mobile-menu-active');
      });
    }
    
    // Close mobile menu when clicking outside
    document.addEventListener('click', (e) => {
      if (!e.target.closest('.primary-nav')) {
        document.body.classList.remove('mobile-menu-active');
      }
    });
  }
  
  setupDropdowns() {
    this.dropdowns.forEach(dropdown => {
      const menu = dropdown.querySelector('.dropdown-menu');
      let hoverTimeout;
      
      dropdown.addEventListener('mouseenter', () => {
        clearTimeout(hoverTimeout);
        menu.style.display = 'block';
      });
      
      dropdown.addEventListener('mouseleave', () => {
        hoverTimeout = setTimeout(() => {
          menu.style.display = 'none';
        }, 200);
      });
    });
  }
  
  setupKeyboardNavigation() {
    // ESC key closes dropdowns and mobile menu
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        document.body.classList.remove('mobile-menu-active');
        this.dropdowns.forEach(dropdown => {
          dropdown.querySelector('.dropdown-menu').style.display = 'none';
        });
      }
    });
  }
}

// Initialize navigation when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new Navigation();
});
```

---

## Task 3: Layout Templates

### 3.1 Marketing Layout Template
**File**: `app/templates/layouts/marketing.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}VectorBid - AI-Powered Pilot Bidding Assistant{% endblock %}</title>
    
    <!-- Meta Tags -->
    <meta name="description" content="{% block description %}Turn your preferences into optimized PBS layers in minutes. Contract and FAR-aware suggestions, personas, and instant exports.{% endblock %}">
    
    <!-- Open Graph -->
    <meta property="og:title" content="{% block og_title %}{{ self.title() }}{% endblock %}">
    <meta property="og:description" content="{% block og_description %}{{ self.description() }}{% endblock %}">
    <meta property="og:image" content="{% block og_image %}/static/images/og-vectorbid.svg{% endblock %}">
    <meta property="og:type" content="website">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{{ self.og_title() }}">
    <meta name="twitter:description" content="{{ self.og_description() }}">
    <meta name="twitter:image" content="{{ self.og_image() }}">
    
    <!-- Favicon -->
    <link rel="icon" type="image/svg+xml" href="/static/images/favicon.svg">
    
    <!-- Stylesheets -->
    <link rel="stylesheet" href="/static/css/design-system.css">
    <link rel="stylesheet" href="/static/css/components/buttons.css">
    <link rel="stylesheet" href="/static/css/components/cards.css">
    <link rel="stylesheet" href="/static/css/components/forms.css">
    <link rel="stylesheet" href="/static/css/components/navigation.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    
    {% block extra_head %}{% endblock %}
</head>
<body>
    <!-- Header -->
    {% include 'components/header.html' %}
    
    <!-- Main Content -->
    <main class="main-content">
        {% block content %}{% endblock %}
    </main>
    
    <!-- Footer -->
    {% include 'components/footer.html' %}
    
    <!-- Scripts -->
    <script src="/static/js/navigation.js"></script>
    {% block extra_scripts %}{% endblock %}
</body>
</html>
```

### 3.2 Application Layout Template
**File**: `app/templates/layouts/application.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Dashboard - VectorBid{% endblock %}</title>
    
    <!-- Favicon -->
    <link rel="icon" type="image/svg+xml" href="/static/images/favicon.svg">
    
    <!-- Stylesheets -->
    <link rel="stylesheet" href="/static/css/design-system.css">
    <link rel="stylesheet" href="/static/css/components/buttons.css">
    <link rel="stylesheet" href="/static/css/components/cards.css">
    <link rel="stylesheet" href="/static/css/components/forms.css">
    <link rel="stylesheet" href="/static/css/components/navigation.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    
    {% block extra_head %}{% endblock %}
</head>
<body class="app-layout">
    <!-- App Header -->
    {% include 'components/app-header.html' %}
    
    <!-- App Layout -->
    <div class="app-container">
        <!-- Sidebar (if applicable) -->
        {% if show_sidebar %}
        <aside class="app-sidebar">
            {% include 'components/sidebar.html' %}
        </aside>
        {% endif %}
        
        <!-- Main Content -->
        <main class="app-main">
            {% block content %}{% endblock %}
        </main>
    </div>
    
    <!-- Scripts -->
    <script src="/static/js/navigation.js"></script>
    <script src="/static/js/app.js"></script>
    {% block extra_scripts %}{% endblock %}
</body>
</html>
```

---

## Task 4: FastAPI Route Structure

### 4.1 Update Main Application
**File**: `app/main.py` (Update existing)

```python
# Add these imports and route includes
from app.routes.marketing import router as marketing_router
from app.routes.products import router as products_router
from app.routes.solutions import router as solutions_router

# Add route inclusions
app.include_router(marketing_router, tags=["Marketing"])
app.include_router(products_router, prefix="/products", tags=["Products"])
app.include_router(solutions_router, prefix="/solutions", tags=["Solutions"])
```

### 4.2 Create Marketing Routes
**File**: `app/routes/marketing.py` (New file)

```python
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Professional home page"""
    return templates.TemplateResponse("pages/home.html", {"request": request})

@router.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    """About VectorBid page"""
    return templates.TemplateResponse("pages/about.html", {"request": request})

@router.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    """Pricing plans page"""
    return templates.TemplateResponse("pages/pricing.html", {"request": request})

@router.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    """Contact information page"""
    return templates.TemplateResponse("pages/contact.html", {"request": request})
```

### 4.3 Create Products Routes
**File**: `app/routes/products.py` (New file)

```python
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def products_overview(request: Request):
    """Products overview page"""
    return templates.TemplateResponse("pages/products/index.html", {"request": request})

@router.get("/bid-optimizer", response_class=HTMLResponse)
async def bid_optimizer(request: Request):
    """Bid Optimizer product page"""
    return templates.TemplateResponse("pages/products/bid-optimizer.html", {"request": request})

@router.get("/route-analyzer", response_class=HTMLResponse)
async def route_analyzer(request: Request):
    """Route Analyzer product page"""
    return templates.TemplateResponse("pages/products/route-analyzer.html", {"request": request})

@router.get("/schedule-builder", response_class=HTMLResponse)
async def schedule_builder(request: Request):
    """Schedule Builder product page"""
    return templates.TemplateResponse("pages/products/schedule-builder.html", {"request": request})

@router.get("/pattern-intelligence", response_class=HTMLResponse)
async def pattern_intelligence(request: Request):
    """Pattern Intelligence product page"""
    return templates.TemplateResponse("pages/products/pattern-intelligence.html", {"request": request})

@router.get("/mobile", response_class=HTMLResponse)
async def mobile_app(request: Request):
    """Mobile App product page"""
    return templates.TemplateResponse("pages/products/mobile.html", {"request": request})
```

---

## Implementation Guidelines

### Quality Standards
1. **Pixel Perfect**: Match professional aviation software standards
2. **Responsive Design**: Mobile-first approach, tablet-optimized
3. **Performance**: <2 second page loads, smooth animations
4. **Accessibility**: WCAG 2.1 AA compliance, keyboard navigation
5. **Consistency**: Use design system for all components

### Testing Requirements
1. **Cross-browser**: Chrome, Firefox, Safari, Edge
2. **Mobile Testing**: iOS Safari, Android Chrome
3. **Navigation Testing**: All dropdown menus, mobile menu
4. **Performance Testing**: Lighthouse scores >90

### Success Criteria
- [ ] Complete design system implemented
- [ ] All navigation menus functional
- [ ] Mobile responsive design working
- [ ] Route structure supports full site map
- [ ] Page load times <2 seconds
- [ ] Professional aviation-grade polish

This foundation will support the entire VectorBid website architecture transformation. Every subsequent phase will build on this solid, professional foundation.

**Timeline**: 5-7 days for complete implementation and testing.