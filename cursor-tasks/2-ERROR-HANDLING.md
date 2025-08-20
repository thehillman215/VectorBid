# Cursor AI Task 2: Error Handling & UX Improvements

## 🎯 Project Goal
Implement comprehensive error handling, loading states, and user feedback throughout the application.

## 📋 Prerequisites
- **MUST COMPLETE**: Task 1 (Mobile Optimization) first
- Base branch: `cursor/mobile-optimization` (from previous task)

## 🔧 Git Setup
```bash
git checkout cursor/mobile-optimization
git pull origin cursor/mobile-optimization
git checkout -b cursor/error-handling-ux
```

## 📁 Files to Modify

### Primary Files (MUST MODIFY):
1. `app/static/js/interactive-demo.js`
2. `app/static/pages/auth/signup.html`
3. `app/static/pages/auth/login.html`
4. `app/static/js/data-flow-viz.js`
5. `app/static/app.js` (main SPA JavaScript)

### New Files to Create:
6. `app/static/js/error-handler.js`
7. `app/static/js/loading-states.js`
8. `app/static/css/feedback-components.css`

## 🎯 Specific Tasks

### Task 2.1: Global Error Handler
**Create**: `app/static/js/error-handler.js`

**Implementation**:
```javascript
class VectorBidErrorHandler {
    constructor() {
        this.setupGlobalHandlers();
        this.retryAttempts = new Map();
        this.maxRetries = 3;
    }
    
    setupGlobalHandlers() {
        // Catch unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.handleError(event.reason, 'unhandled_promise');
        });
        
        // Catch JavaScript errors
        window.addEventListener('error', (event) => {
            this.handleError(event.error, 'javascript_error');
        });
        
        // Network error detection
        window.addEventListener('offline', () => {
            this.showNetworkError('offline');
        });
        
        window.addEventListener('online', () => {
            this.hideNetworkError();
        });
    }
    
    async handleApiError(error, endpoint, options = {}) {
        const retryKey = `${endpoint}_${Date.now()}`;
        const currentRetries = this.retryAttempts.get(retryKey) || 0;
        
        if (currentRetries < this.maxRetries && this.isRetryableError(error)) {
            this.retryAttempts.set(retryKey, currentRetries + 1);
            this.showRetryMessage(endpoint, currentRetries + 1);
            
            // Exponential backoff
            const delay = Math.pow(2, currentRetries) * 1000;
            await this.delay(delay);
            
            return { shouldRetry: true, retryKey };
        }
        
        this.showErrorMessage(this.getErrorMessage(error, endpoint));
        return { shouldRetry: false };
    }
    
    isRetryableError(error) {
        const retryableStatuses = [408, 429, 500, 502, 503, 504];
        return retryableStatuses.includes(error.status) || 
               error.name === 'NetworkError' ||
               error.message.includes('fetch');
    }
    
    getErrorMessage(error, endpoint) {
        const errorMessages = {
            '/api/parse': 'Failed to parse your preferences. Please try again.',
            '/api/optimize': 'Schedule optimization failed. Please check your preferences.',
            '/auth/signup': 'Account creation failed. Please verify your information.',
            '/auth/login': 'Login failed. Please check your credentials.',
            'default': 'Something went wrong. Please try again.'
        };
        
        return errorMessages[endpoint] || errorMessages.default;
    }
    
    showErrorMessage(message, duration = 5000) {
        const errorDiv = this.createToast(message, 'error');
        document.body.appendChild(errorDiv);
        
        setTimeout(() => errorDiv.remove(), duration);
    }
    
    showRetryMessage(endpoint, attempt) {
        const message = `Retrying ${endpoint.split('/').pop()}... (${attempt}/${this.maxRetries})`;
        const retryDiv = this.createToast(message, 'retry');
        document.body.appendChild(retryDiv);
        
        setTimeout(() => retryDiv.remove(), 2000);
    }
    
    createToast(message, type) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type} fixed top-4 right-4 z-50 max-w-sm p-4 rounded-lg shadow-lg transform transition-transform duration-300`;
        
        const colors = {
            error: 'bg-red-500 text-white',
            retry: 'bg-yellow-500 text-white', 
            success: 'bg-green-500 text-white',
            info: 'bg-blue-500 text-white'
        };
        
        toast.className += ` ${colors[type]}`;
        toast.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-${this.getIcon(type)} mr-2"></i>
                <span>${message}</span>
            </div>
        `;
        
        return toast;
    }
    
    getIcon(type) {
        const icons = {
            error: 'exclamation-triangle',
            retry: 'sync-alt fa-spin',
            success: 'check',
            info: 'info'
        };
        return icons[type];
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Initialize global error handler
window.VectorBidErrors = new VectorBidErrorHandler();
```

### Task 2.2: Loading States Manager
**Create**: `app/static/js/loading-states.js`

**Implementation**:
```javascript
class LoadingStateManager {
    constructor() {
        this.activeLoading = new Set();
        this.createGlobalSpinner();
    }
    
    show(element, message = 'Loading...', options = {}) {
        const loadingId = this.generateId();
        this.activeLoading.add(loadingId);
        
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (!element) return loadingId;
        
        // Create loading overlay
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center z-40';
        overlay.setAttribute('data-loading-id', loadingId);
        
        overlay.innerHTML = `
            <div class="loading-content text-center">
                <div class="spinner-border animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
                <p class="text-sm text-gray-600">${message}</p>
                ${options.showCancel ? '<button class="cancel-loading mt-2 text-xs text-gray-500 underline">Cancel</button>' : ''}
            </div>
        `;
        
        // Position relative if not already
        if (getComputedStyle(element).position === 'static') {
            element.style.position = 'relative';
        }
        
        element.appendChild(overlay);
        
        // Handle cancel if enabled
        if (options.showCancel && options.onCancel) {
            overlay.querySelector('.cancel-loading').addEventListener('click', () => {
                options.onCancel();
                this.hide(loadingId);
            });
        }
        
        return loadingId;
    }
    
    hide(loadingId) {
        if (!this.activeLoading.has(loadingId)) return;
        
        const overlay = document.querySelector(`[data-loading-id="${loadingId}"]`);
        if (overlay) {
            overlay.remove();
        }
        
        this.activeLoading.delete(loadingId);
    }
    
    hideAll() {
        document.querySelectorAll('.loading-overlay').forEach(overlay => {
            overlay.remove();
        });
        this.activeLoading.clear();
    }
    
    generateId() {
        return 'loading_' + Math.random().toString(36).substr(2, 9);
    }
    
    createGlobalSpinner() {
        const style = document.createElement('style');
        style.textContent = `
            .spinner-border {
                width: 2rem;
                height: 2rem;
                border: 0.25em solid transparent;
                border-top: 0.25em solid currentColor;
                border-radius: 50%;
                animation: spin 1s linear infinite;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .loading-overlay {
                backdrop-filter: blur(2px);
            }
        `;
        document.head.appendChild(style);
    }
}

// Initialize global loading manager
window.LoadingStates = new LoadingStateManager();
```

### Task 2.3: Enhanced Interactive Demo Error Handling
**File**: `app/static/js/interactive-demo.js`

**Modifications Required**:
```javascript
// Replace existing apiCall method
async apiCall(endpoint, payload) {
    const loadingId = window.LoadingStates.show(
        document.querySelector('.demo-preview'), 
        'AI is processing your request...',
        { 
            showCancel: true, 
            onCancel: () => this.cancelCurrentRequest() 
        }
    );
    
    try {
        const response = await fetch(`${this.apiBase}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload),
            signal: this.abortController.signal
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        window.LoadingStates.hide(loadingId);
        return data;
        
    } catch (error) {
        window.LoadingStates.hide(loadingId);
        
        if (error.name === 'AbortError') {
            this.updateStatus('🚫 Request cancelled', 'info');
            return null;
        }
        
        const retryResult = await window.VectorBidErrors.handleApiError(error, endpoint);
        
        if (retryResult.shouldRetry) {
            return this.apiCall(endpoint, payload); // Retry
        }
        
        throw error; // Final failure
    }
}

// Add abort controller for cancellation
constructor() {
    // ... existing code ...
    this.abortController = new AbortController();
}

cancelCurrentRequest() {
    this.abortController.abort();
    this.abortController = new AbortController();
    this.isProcessing = false;
}
```

### Task 2.4: Authentication Error Improvements
**Files**: `app/static/pages/auth/signup.html`, `app/static/pages/auth/login.html`

**Add to both files before closing `</body>`**:
```html
<script src="/static/js/error-handler.js"></script>
<script src="/static/js/loading-states.js"></script>
<script>
// Enhanced form submission with proper error handling
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('form');
    const submitBtn = form.querySelector('button[type="submit"]');
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Show loading state
        const loadingId = window.LoadingStates.show(
            form.parentElement, 
            'Creating your account...'
        );
        
        // Disable form during submission
        const formElements = form.querySelectorAll('input, button, select');
        formElements.forEach(el => el.disabled = true);
        
        try {
            await simulateApiCall();
            
            // Success handling
            window.LoadingStates.hide(loadingId);
            showSuccessMessage('Account created successfully!');
            
            setTimeout(() => {
                window.location.href = '/demo';
            }, 2000);
            
        } catch (error) {
            window.LoadingStates.hide(loadingId);
            
            // Re-enable form
            formElements.forEach(el => el.disabled = false);
            
            // Let global error handler manage the error
            await window.VectorBidErrors.handleApiError(error, '/auth/signup');
            
        }
    });
    
    async function simulateApiCall() {
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        // Simulate random failures for testing
        if (Math.random() < 0.3) {
            throw new Error('Validation failed');
        }
    }
});
</script>
```

### Task 2.5: Feedback Components CSS
**Create**: `app/static/css/feedback-components.css`

**Implementation**:
```css
/* Toast notifications */
.toast {
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
    border-left: 4px solid;
    animation: slideInRight 0.3s ease-out;
}

.toast-error { border-left-color: #ef4444; }
.toast-success { border-left-color: #10b981; }
.toast-warning { border-left-color: #f59e0b; }
.toast-info { border-left-color: #3b82f6; }

@keyframes slideInRight {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

/* Loading states */
.loading-overlay {
    transition: opacity 0.2s ease-in-out;
}

.loading-content {
    background: white;
    padding: 1.5rem;
    border-radius: 0.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
}

/* Form validation states */
.form-error {
    border-color: #ef4444 !important;
    box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1) !important;
}

.form-success {
    border-color: #10b981 !important;
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1) !important;
}

.error-message {
    color: #ef4444;
    font-size: 0.875rem;
    margin-top: 0.25rem;
}

.success-message {
    color: #10b981;
    font-size: 0.875rem;
    margin-top: 0.25rem;
}

/* Network status indicator */
.network-status {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 9999;
    padding: 0.5rem;
    text-align: center;
    font-size: 0.875rem;
    font-weight: 500;
    transform: translateY(-100%);
    transition: transform 0.3s ease-in-out;
}

.network-status.offline {
    background-color: #ef4444;
    color: white;
    transform: translateY(0);
}

.network-status.reconnecting {
    background-color: #f59e0b;
    color: white;
    transform: translateY(0);
}

/* Button loading states */
.btn-loading {
    position: relative;
    pointer-events: none;
}

.btn-loading::after {
    content: '';
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    width: 1rem;
    height: 1rem;
    border: 2px solid transparent;
    border-top: 2px solid currentColor;
    border-radius: 50%;
    animation: spin 1s linear infinite;
}

/* Mobile optimizations */
@media (max-width: 768px) {
    .toast {
        left: 1rem;
        right: 1rem;
        max-width: none;
    }
    
    .loading-content {
        padding: 1rem;
    }
    
    .network-status {
        font-size: 0.75rem;
        padding: 0.375rem;
    }
}
```

## ✅ Success Criteria

### Testing Requirements:
1. **Error scenarios**: Test network failures, API errors, validation failures
2. **Loading states**: Verify all async operations show appropriate loading feedback
3. **Retry logic**: Confirm exponential backoff and retry limits work
4. **Mobile compatibility**: Ensure error messages display properly on mobile
5. **Accessibility**: Error messages are announced by screen readers

### Specific Validations:
- [ ] Network disconnection shows appropriate offline message
- [ ] API failures trigger retry mechanism with proper backoff
- [ ] Form submissions show loading states and handle errors gracefully
- [ ] Data flow visualization handles errors without breaking
- [ ] Demo interactions provide clear feedback for all states
- [ ] Error messages are user-friendly and actionable
- [ ] Loading states are cancelable where appropriate

## 🔗 Chain to Next Task
After completing error handling improvements:

```bash
git add .
git commit -m "feat: implement comprehensive error handling and UX improvements

- Add global error handler with retry logic and exponential backoff
- Implement loading state manager with cancellation support
- Enhance form submissions with proper error handling
- Add user-friendly error messages and retry mechanisms
- Create feedback components for consistent UX
- Improve mobile error display and interaction

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin cursor/error-handling-ux
```

**NEXT**: Proceed to `3-PERFORMANCE-OPTIMIZATION.md` for performance improvements.

## 📊 Testing Commands
```bash
# Test error scenarios
# Disable network in browser dev tools and test functionality
# Use browser's network throttling to test slow connections

# Test retry logic
# Temporarily break API endpoints and verify retry behavior

# Performance impact test
curl -w "Total time: %{time_total}s\n" http://localhost:8000/
```

## 🚨 Critical Requirements
- All error messages must be user-friendly (no technical jargon)
- Loading states must not block critical functionality
- Retry logic must not overwhelm the server
- Error handling must work on all supported browsers
- Mobile error display must be touch-friendly