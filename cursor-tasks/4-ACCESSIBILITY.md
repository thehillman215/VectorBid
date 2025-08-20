# Cursor AI Task 4: Accessibility (A11y) Improvements

## 🎯 Project Goal
Make VectorBid fully accessible to users with disabilities, meeting WCAG 2.1 AA standards.

## 📋 Prerequisites
- **MUST COMPLETE**: Task 3 (Performance Optimization) first
- Base branch: `cursor/performance-optimization` (from previous task)

## 🔧 Git Setup
```bash
git checkout cursor/performance-optimization
git pull origin cursor/performance-optimization
git checkout -b cursor/accessibility-improvements
```

## 📁 Files to Modify

### Primary Files (MUST MODIFY):
1. `app/static/pages/landing/home.html`
2. `app/static/pages/auth/signup.html`
3. `app/static/pages/auth/login.html`
4. `app/static/js/data-flow-viz.js`
5. `app/static/js/interactive-demo.js`
6. `app/static/css/design-system.css`

### New Files to Create:
7. `app/static/js/accessibility-manager.js`
8. `app/static/css/accessibility.css`
9. `app/static/js/keyboard-navigation.js`
10. `app/static/js/screen-reader-announcements.js`

## 🎯 Specific Tasks

### Task 4.1: Semantic HTML and ARIA Labels
**File**: `app/static/pages/landing/home.html`

**Issues to Fix**:
- Missing semantic landmarks (main, nav, section, article)
- Interactive elements without proper ARIA labels
- Missing skip navigation links
- Form labels not properly associated
- Images without alt text

**Expected Changes**:
```html
<!-- Add skip navigation -->
<a href="#main-content" class="skip-nav">Skip to main content</a>

<!-- Proper landmarks -->
<nav role="navigation" aria-label="Main navigation">
    <div class="navbar">
        <!-- Navigation content -->
    </div>
</nav>

<main id="main-content" role="main">
    <!-- Hero section -->
    <section aria-labelledby="hero-heading" class="hero">
        <h1 id="hero-heading">VectorBid - World's First AI-Powered Pilot Bidding System</h1>
        <!-- Hero content -->
    </section>
    
    <!-- Demo section -->
    <section aria-labelledby="demo-heading" class="demo-section">
        <h2 id="demo-heading">See VectorBid AI in Action</h2>
        
        <!-- Demo widget with proper accessibility -->
        <div class="demo-widget" role="application" aria-label="Interactive demo">
            <button 
                aria-describedby="demo-description"
                aria-expanded="false"
                aria-controls="demo-results">
                Try Interactive Demo
            </button>
            <div id="demo-description" class="sr-only">
                This demo shows how VectorBid processes pilot preferences using AI
            </div>
            <div id="demo-results" aria-live="polite" aria-atomic="true"></div>
        </div>
    </section>
    
    <!-- Data flow visualization -->
    <section aria-labelledby="dataflow-heading">
        <h2 id="dataflow-heading">AI Data Flow Architecture</h2>
        <div 
            id="data-flow-container" 
            role="img" 
            aria-label="Interactive diagram showing VectorBid's AI data processing flow"
            aria-describedby="dataflow-description"
            tabindex="0">
        </div>
        <div id="dataflow-description" class="sr-only">
            Diagram showing four processing layers: Input layer with pilot preferences, 
            Processing layer with AI analysis, Analysis layer with optimization, 
            and Output layer with schedule recommendations
        </div>
    </section>
</main>

<!-- Footer with proper landmark -->
<footer role="contentinfo">
    <!-- Footer content -->
</footer>
```

### Task 4.2: Form Accessibility
**Files**: `app/static/pages/auth/signup.html`, `app/static/pages/auth/login.html`

**Expected Changes for Both Files**:
```html
<main role="main">
    <div class="auth-container">
        <form role="form" aria-labelledby="form-title" novalidate>
            <h2 id="form-title">Sign Up for VectorBid</h2>
            
            <!-- Email field -->
            <div class="form-group">
                <label for="email" id="email-label">
                    Email address
                    <span aria-hidden="true">*</span>
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
            
            <!-- Password field -->
            <div class="form-group">
                <label for="password" id="password-label">
                    Password
                    <span aria-hidden="true">*</span>
                </label>
                <div class="password-input-wrapper">
                    <input 
                        id="password" 
                        name="password" 
                        type="password"
                        required
                        aria-labelledby="password-label"
                        aria-describedby="password-help password-error password-strength"
                        aria-invalid="false"
                        autocomplete="new-password">
                    <button 
                        type="button" 
                        class="password-toggle"
                        aria-label="Show password"
                        aria-pressed="false">
                        <i class="fas fa-eye" aria-hidden="true"></i>
                    </button>
                </div>
                <div id="password-help" class="help-text">
                    Minimum 8 characters with letters and numbers
                </div>
                <div id="password-strength" class="password-strength" aria-live="polite"></div>
                <div id="password-error" class="error-text" role="alert" aria-live="polite"></div>
            </div>
            
            <!-- Submit button -->
            <button 
                type="submit" 
                class="submit-btn"
                aria-describedby="submit-help">
                <span class="btn-text">Create Account</span>
                <span class="btn-loading sr-only">Creating account, please wait</span>
            </button>
            <div id="submit-help" class="sr-only">
                Creates your VectorBid account and signs you in
            </div>
            
            <!-- Status announcements -->
            <div role="status" aria-live="polite" aria-atomic="true" class="sr-only" id="form-status"></div>
        </form>
    </div>
</main>
```

### Task 4.3: Data Flow Visualization Accessibility
**File**: `app/static/js/data-flow-viz.js`

**Accessibility Enhancements**:
```javascript
class DataFlowVisualization {
    constructor(containerId) {
        // ... existing code ...
        
        this.setupKeyboardNavigation();
        this.setupScreenReaderSupport();
        this.setupAccessibilityAttributes();
    }
    
    setupAccessibilityAttributes() {
        if (!this.container) return;
        
        // Make container focusable and add ARIA attributes
        this.container.setAttribute('tabindex', '0');
        this.container.setAttribute('role', 'img');
        this.container.setAttribute('aria-label', 'VectorBid AI Data Flow Diagram');
        
        // Add description
        const description = document.createElement('div');
        description.id = `${this.container.id}-description`;
        description.className = 'sr-only';
        description.textContent = this.generateAccessibilityDescription();
        this.container.parentNode.insertBefore(description, this.container.nextSibling);
        
        this.container.setAttribute('aria-describedby', description.id);
    }
    
    generateAccessibilityDescription() {
        return `Interactive diagram showing VectorBid's AI processing pipeline. 
                The system has 4 main layers: Input layer containing pilot preferences, 
                context data, and rule packs; Processing layer with NLP parser, validator, 
                optimizer, and data fusion; Analysis layer with route analyzer, scheduler 
                scorer, and strategy engine; and Output layer producing schedule candidates, 
                PBS export, and AI insights. Data flows from left to right through these layers. 
                Press Tab to navigate and Enter to interact with components.`;
    }
    
    setupKeyboardNavigation() {
        if (!this.container) return;
        
        this.focusedNodeIndex = -1;
        this.focusableNodes = [];
        
        this.container.addEventListener('keydown', (e) => {
            this.handleKeyboardNavigation(e);
        });
        
        this.container.addEventListener('focus', () => {
            if (this.focusedNodeIndex === -1 && this.focusableNodes.length > 0) {
                this.focusNode(0);
            }
        });
    }
    
    handleKeyboardNavigation(e) {
        switch (e.key) {
            case 'ArrowRight':
            case 'ArrowDown':
                e.preventDefault();
                this.focusNextNode();
                break;
            case 'ArrowLeft':
            case 'ArrowUp':
                e.preventDefault();
                this.focusPreviousNode();
                break;
            case 'Enter':
            case ' ':
                e.preventDefault();
                this.activateCurrentNode();
                break;
            case 'Home':
                e.preventDefault();
                this.focusNode(0);
                break;
            case 'End':
                e.preventDefault();
                this.focusNode(this.focusableNodes.length - 1);
                break;
            case 'Escape':
                this.container.blur();
                break;
        }
    }
    
    focusNextNode() {
        if (this.focusableNodes.length === 0) return;
        
        this.focusedNodeIndex = (this.focusedNodeIndex + 1) % this.focusableNodes.length;
        this.focusNode(this.focusedNodeIndex);
    }
    
    focusPreviousNode() {
        if (this.focusableNodes.length === 0) return;
        
        this.focusedNodeIndex = this.focusedNodeIndex <= 0 
            ? this.focusableNodes.length - 1 
            : this.focusedNodeIndex - 1;
        this.focusNode(this.focusedNodeIndex);
    }
    
    focusNode(index) {
        if (index < 0 || index >= this.focusableNodes.length) return;
        
        // Remove focus from previous node
        this.svg.selectAll('.node').classed('keyboard-focus', false);
        
        // Add focus to current node
        const node = this.focusableNodes[index];
        const nodeElement = this.svg.select(`[data-node-id="${node.id}"]`);
        nodeElement.classed('keyboard-focus', true);
        
        this.focusedNodeIndex = index;
        
        // Announce to screen readers
        this.announceNodeFocus(node);
    }
    
    activateCurrentNode() {
        if (this.focusedNodeIndex < 0) return;
        
        const node = this.focusableNodes[this.focusedNodeIndex];
        this.highlightNodePath(node);
        
        // Announce activation
        window.A11yAnnouncer.announce(
            `Activated ${node.label}. Showing related connections and data flow paths.`
        );
    }
    
    announceNodeFocus(node) {
        const announcement = `${node.label}. ${node.type} layer. 
                            ${this.getNodeDescription(node)}. 
                            ${this.focusedNodeIndex + 1} of ${this.focusableNodes.length}.`;
        
        window.A11yAnnouncer.announce(announcement);
    }
    
    getNodeDescription(node) {
        const descriptions = {
            'pilot': 'Captures pilot scheduling preferences in natural language',
            'context': 'Provides pilot profile and constraint information',
            'rules': 'Contains airline and regulatory compliance rules',
            'parser': 'Converts natural language to structured preferences using GPT-4',
            'validator': 'Ensures preferences comply with regulations and rules',
            'optimizer': 'Applies AI optimization to improve schedule outcomes',
            'fusion': 'Combines and reconciles all data sources',
            'analyzer': 'Analyzes route options and compatibility',
            'scorer': 'Scores schedule options based on preferences',
            'strategy': 'Develops optimal bidding strategy',
            'candidates': 'Generated schedule recommendations',
            'export': 'Formats data for pilot bidding system',
            'insights': 'Provides explanations and strategic advice',
            'pbs': 'External pilot bidding system',
            'dashboard': 'User interface for results and management'
        };
        
        return descriptions[node.id] || 'Processing component';
    }
    
    renderNodes() {
        // ... existing rendering code ...
        
        // Add accessibility attributes to nodes
        const nodeGroups = this.svg.selectAll('.node');
        
        nodeGroups.each(function(d) {
            const group = d3.select(this);
            group.attr('data-node-id', d.id);
            group.attr('role', 'button');
            group.attr('aria-label', `${d.label} - ${d.type} component`);
            group.attr('tabindex', '-1');
        });
        
        // Store focusable nodes
        this.focusableNodes = this.nodes.slice();
    }
    
    setupScreenReaderSupport() {
        // Create live region for dynamic announcements
        const liveRegion = document.createElement('div');
        liveRegion.id = `${this.container.id}-live`;
        liveRegion.className = 'sr-only';
        liveRegion.setAttribute('aria-live', 'polite');
        liveRegion.setAttribute('aria-atomic', 'true');
        this.container.parentNode.appendChild(liveRegion);
        
        this.liveRegion = liveRegion;
    }
}
```

### Task 4.4: Screen Reader Announcements Manager
**Create**: `app/static/js/screen-reader-announcements.js`

**Implementation**:
```javascript
class AccessibilityAnnouncer {
    constructor() {
        this.liveRegions = {
            polite: this.createLiveRegion('polite'),
            assertive: this.createLiveRegion('assertive')
        };
        
        this.announcementQueue = [];
        this.isProcessing = false;
        this.debounceTimeout = null;
    }
    
    createLiveRegion(priority) {
        const region = document.createElement('div');
        region.className = 'sr-only';
        region.setAttribute('aria-live', priority);
        region.setAttribute('aria-atomic', 'true');
        region.setAttribute('role', priority === 'assertive' ? 'alert' : 'status');
        document.body.appendChild(region);
        return region;
    }
    
    announce(message, priority = 'polite', options = {}) {
        if (!message || typeof message !== 'string') return;
        
        const announcement = {
            message: message.trim(),
            priority: priority,
            timestamp: Date.now(),
            delay: options.delay || 0,
            clear: options.clear || false
        };
        
        // Clear queue if requested
        if (options.clear) {
            this.clearQueue();
        }
        
        // Add to queue
        this.announcementQueue.push(announcement);
        
        // Process queue
        this.processQueue();
    }
    
    processQueue() {
        if (this.isProcessing || this.announcementQueue.length === 0) return;
        
        this.isProcessing = true;
        const announcement = this.announcementQueue.shift();
        
        // Apply delay if specified
        setTimeout(() => {
            this.makeAnnouncement(announcement);
            
            // Process next announcement after a short delay
            setTimeout(() => {
                this.isProcessing = false;
                this.processQueue();
            }, 100);
            
        }, announcement.delay);
    }
    
    makeAnnouncement(announcement) {
        const region = this.liveRegions[announcement.priority];
        
        if (!region) {
            console.warn('Invalid announcement priority:', announcement.priority);
            return;
        }
        
        // Clear previous announcement
        region.textContent = '';
        
        // Add new announcement (small delay ensures screen readers notice the change)
        setTimeout(() => {
            region.textContent = announcement.message;
        }, 10);
    }
    
    clearQueue() {
        this.announcementQueue = [];
    }
    
    announcePageChange(title, description) {
        this.announce(
            `Page changed to ${title}. ${description}`,
            'assertive',
            { clear: true }
        );
    }
    
    announceFormError(fieldName, errorMessage) {
        this.announce(
            `Error in ${fieldName}: ${errorMessage}`,
            'assertive'
        );
    }
    
    announceFormSuccess(message) {
        this.announce(
            `Success: ${message}`,
            'polite'
        );
    }
    
    announceLoadingStart(context) {
        this.announce(
            `Loading ${context}, please wait.`,
            'polite'
        );
    }
    
    announceLoadingComplete(context) {
        this.announce(
            `${context} loaded successfully.`,
            'polite'
        );
    }
    
    announceProgress(current, total, context) {
        this.announce(
            `${context} progress: ${current} of ${total} complete.`,
            'polite'
        );
    }
    
    destroy() {
        this.clearQueue();
        Object.values(this.liveRegions).forEach(region => {
            if (region && region.parentNode) {
                region.parentNode.removeChild(region);
            }
        });
    }
}

window.A11yAnnouncer = new AccessibilityAnnouncer();
```

### Task 4.5: Accessibility Styles
**Create**: `app/static/css/accessibility.css`

**Implementation**:
```css
/* Screen reader only content */
.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
}

/* Show on focus for skip links */
.skip-nav {
    position: absolute;
    top: -40px;
    left: 6px;
    background: #000;
    color: #fff;
    padding: 8px;
    text-decoration: none;
    border-radius: 0 0 4px 4px;
    z-index: 9999;
    transition: top 0.2s ease;
}

.skip-nav:focus {
    top: 0;
}

/* High contrast mode support */
@media (prefers-contrast: high) {
    :root {
        --color-primary: #000000;
        --color-background: #ffffff;
        --color-text: #000000;
        --color-border: #000000;
        --color-error: #cc0000;
        --color-success: #006600;
        --color-warning: #cc6600;
    }
    
    button, .btn {
        border: 2px solid #000000 !important;
    }
    
    input, select, textarea {
        border: 2px solid #000000 !important;
        background: #ffffff !important;
        color: #000000 !important;
    }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
    }
    
    .spinner-border,
    .loading-spinner {
        animation: none !important;
    }
}

/* Focus styles */
:focus {
    outline: 2px solid #3b82f6;
    outline-offset: 2px;
}

.keyboard-focus {
    outline: 3px solid #3b82f6;
    outline-offset: 4px;
}

/* Ensure interactive elements meet minimum size requirements */
button,
.btn,
a,
input[type="checkbox"],
input[type="radio"],
select {
    min-height: 44px;
    min-width: 44px;
}

/* Form validation styles */
.form-error {
    border-color: #dc2626 !important;
    box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.1) !important;
}

.form-success {
    border-color: #059669 !important;
    box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.1) !important;
}

.error-text {
    color: #dc2626;
    font-size: 0.875rem;
    margin-top: 0.25rem;
}

.error-text::before {
    content: "⚠ ";
    font-weight: bold;
}

.success-text {
    color: #059669;
    font-size: 0.875rem;
    margin-top: 0.25rem;
}

.success-text::before {
    content: "✓ ";
    font-weight: bold;
}

/* Loading states */
.btn-loading {
    position: relative;
    color: transparent !important;
}

.btn-loading::after {
    content: "";
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 20px;
    height: 20px;
    border: 2px solid transparent;
    border-top: 2px solid currentColor;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

/* Ensure sufficient color contrast */
.text-muted {
    color: #6b7280; /* Ensures 4.5:1 contrast ratio */
}

/* Password strength indicator */
.password-strength {
    margin-top: 0.25rem;
    font-size: 0.875rem;
}

.password-strength.weak {
    color: #dc2626;
}

.password-strength.medium {
    color: #d97706;
}

.password-strength.strong {
    color: #059669;
}

/* Tooltip styles for additional context */
.tooltip {
    position: relative;
    display: inline-block;
}

.tooltip .tooltip-text {
    visibility: hidden;
    width: 200px;
    background-color: #1f2937;
    color: #fff;
    text-align: center;
    border-radius: 6px;
    padding: 8px;
    font-size: 14px;
    position: absolute;
    z-index: 1000;
    bottom: 125%;
    left: 50%;
    margin-left: -100px;
    opacity: 0;
    transition: opacity 0.3s;
}

.tooltip:hover .tooltip-text,
.tooltip:focus .tooltip-text {
    visibility: visible;
    opacity: 1;
}

/* Mobile accessibility improvements */
@media (max-width: 768px) {
    .skip-nav {
        left: 4px;
        font-size: 16px; /* Prevent zoom on iOS */
    }
    
    input, select, textarea {
        font-size: 16px; /* Prevent zoom on iOS */
    }
    
    button, .btn {
        min-height: 48px; /* Larger touch targets on mobile */
        min-width: 48px;
    }
}

/* Print styles for accessibility */
@media print {
    .sr-only {
        position: static;
        width: auto;
        height: auto;
        margin: 0;
        overflow: visible;
        clip: auto;
        white-space: normal;
    }
    
    .skip-nav {
        display: none;
    }
    
    button, .btn {
        display: none;
    }
}
```

### Task 4.6: Enhanced Interactive Demo Accessibility
**File**: `app/static/js/interactive-demo.js`

**Add These Methods**:
```javascript
setupAccessibility() {
    // Add ARIA attributes to demo container
    const demoContainer = document.querySelector('.demo-widget');
    if (demoContainer) {
        demoContainer.setAttribute('role', 'application');
        demoContainer.setAttribute('aria-label', 'VectorBid AI Demo');
        demoContainer.setAttribute('aria-describedby', 'demo-description');
    }
    
    // Create description for screen readers
    const description = document.createElement('div');
    description.id = 'demo-description';
    description.className = 'sr-only';
    description.textContent = 'Interactive demonstration of VectorBid AI processing pilot preferences and generating optimized schedules';
    
    if (demoContainer) {
        demoContainer.appendChild(description);
    }
}

updateStatusAccessible(message, type = 'info') {
    // Update visual status
    this.updateStatus(message, type);
    
    // Announce to screen readers
    const priority = type === 'error' ? 'assertive' : 'polite';
    window.A11yAnnouncer.announce(message, priority);
    
    // Update ARIA live region
    const statusEl = document.getElementById('demo-status');
    if (statusEl) {
        statusEl.setAttribute('aria-live', priority);
        statusEl.textContent = message;
    }
}

async startDemo() {
    if (this.isProcessing) return;
    
    this.isProcessing = true;
    
    // Announce start of demo
    window.A11yAnnouncer.announce(
        'Starting AI demonstration. Processing your preferences now.',
        'polite'
    );
    
    try {
        const inputText = this.getDemoInputText();
        
        await this.parsePreferences(inputText);
        await this.optimizeSchedule();
        this.showResults();
        
        // Announce completion
        window.A11yAnnouncer.announce(
            'Demo complete. Your AI-optimized schedule is ready.',
            'polite'
        );
        
    } catch (error) {
        this.handleError(error);
        
        // Announce error
        window.A11yAnnouncer.announce(
            'Demo encountered an error. Please try again.',
            'assertive'
        );
    } finally {
        this.isProcessing = false;
    }
}
```

## ✅ Success Criteria

### WCAG 2.1 AA Compliance:
- [ ] All images have appropriate alt text
- [ ] Color contrast ratio ≥ 4.5:1 for normal text, ≥ 3:1 for large text
- [ ] All interactive elements are keyboard accessible
- [ ] Focus indicators are clearly visible
- [ ] Form labels are properly associated with inputs
- [ ] Error messages are announced to screen readers
- [ ] Page structure uses semantic HTML and landmarks

### Testing Requirements:
1. **Screen Reader Testing**: Test with NVDA, JAWS, or VoiceOver
2. **Keyboard Navigation**: All functionality accessible via keyboard only
3. **High Contrast Mode**: UI remains usable in high contrast mode
4. **Zoom Testing**: UI remains functional at 200% zoom level
5. **Color Blindness**: Information not conveyed by color alone

## 🔗 Chain to Next Task
After completing accessibility improvements:

```bash
git add .
git commit -m "feat: implement comprehensive accessibility improvements (WCAG 2.1 AA)

- Add semantic HTML structure with proper landmarks
- Implement keyboard navigation for all interactive elements
- Add screen reader announcements and live regions
- Ensure proper form accessibility with labels and validation
- Create accessible data visualization with keyboard support
- Add high contrast and reduced motion support
- Meet color contrast requirements and focus indicators

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin cursor/accessibility-improvements
```

**NEXT**: Proceed to `5-TESTING-INFRASTRUCTURE.md` for comprehensive testing setup.

## 📊 Testing Commands
```bash
# Accessibility testing
axe-cli http://localhost:8000/

# Screen reader simulation (if available)
npm install -g @axe-core/cli
axe http://localhost:8000/ --include-tags wcag2a,wcag2aa

# Lighthouse accessibility audit
lighthouse http://localhost:8000/ --only-categories=accessibility
```

## 🚨 Critical Requirements
- All changes must maintain existing functionality
- Color cannot be the only way to convey information
- All interactive elements must be keyboard accessible
- Screen reader announcements must be meaningful and timely
- Form validation must be accessible to assistive technologies
- Performance impact of accessibility features must be minimal