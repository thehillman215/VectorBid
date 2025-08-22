// VectorBid Global Error Handler
// Comprehensive error handling with retry logic, user feedback, and mobile optimization

class VectorBidErrorHandler {
    constructor() {
        this.setupGlobalHandlers();
        this.retryAttempts = new Map();
        this.maxRetries = 3;
        this.networkStatus = 'online';
        this.createNetworkStatusIndicator();
        this.initializeErrorReporting();
    }
    
    setupGlobalHandlers() {
        // Catch unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            this.handleError(event.reason, 'unhandled_promise');
            event.preventDefault(); // Prevent default browser behavior
        });
        
        // Catch JavaScript errors
        window.addEventListener('error', (event) => {
            console.error('JavaScript error:', event.error);
            this.handleError(event.error, 'javascript_error', {
                filename: event.filename,
                lineno: event.lineno,
                colno: event.colno
            });
        });
        
        // Network status monitoring
        window.addEventListener('offline', () => {
            this.networkStatus = 'offline';
            this.showNetworkError('offline');
        });
        
        window.addEventListener('online', () => {
            this.networkStatus = 'online';
            this.hideNetworkError();
            this.showSuccessMessage('Connection restored', 2000);
        });
        
        // Monitor fetch requests for network errors
        this.interceptFetch();
    }
    
    interceptFetch() {
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            try {
                const response = await originalFetch.apply(this, args);
                return response;
            } catch (error) {
                // Network error detected
                if (error.name === 'TypeError' && error.message.includes('fetch')) {
                    this.handleNetworkError(error, args[0]);
                }
                throw error;
            }
        };
    }
    
    async handleApiError(error, endpoint, options = {}) {
        const retryKey = `${endpoint}_${options.requestId || Date.now()}`;
        const currentRetries = this.retryAttempts.get(retryKey) || 0;
        
        // Check if this is a retryable error
        if (currentRetries < this.maxRetries && this.isRetryableError(error)) {
            this.retryAttempts.set(retryKey, currentRetries + 1);
            this.showRetryMessage(endpoint, currentRetries + 1);
            
            // Exponential backoff with jitter
            const baseDelay = Math.pow(2, currentRetries) * 1000;
            const jitter = Math.random() * 1000;
            const delay = baseDelay + jitter;
            
            await this.delay(delay);
            
            return { shouldRetry: true, retryKey, attempt: currentRetries + 1 };
        }
        
        // Final failure - clean up retry tracking
        this.retryAttempts.delete(retryKey);
        
        // Show user-friendly error message
        const errorMessage = this.getErrorMessage(error, endpoint);
        this.showErrorMessage(errorMessage);
        
        // Log detailed error for debugging
        this.logError(error, endpoint, currentRetries);
        
        return { shouldRetry: false, finalFailure: true };
    }
    
    isRetryableError(error) {
        // HTTP status codes that warrant retry
        const retryableStatuses = [408, 429, 500, 502, 503, 504];
        
        // Network-related errors
        const networkErrors = ['NetworkError', 'TypeError', 'TimeoutError'];
        
        return (
            retryableStatuses.includes(error.status) || 
            networkErrors.includes(error.name) ||
            error.message.includes('fetch') ||
            error.message.includes('network') ||
            this.networkStatus === 'offline'
        );
    }
    
    getErrorMessage(error, endpoint) {
        // Specific error messages for different endpoints
        const endpointMessages = {
            '/api/parse': 'Unable to process your preferences. Please check your input and try again.',
            '/api/optimize': 'Schedule optimization failed. Please verify your preferences and try again.',
            '/api/validate': 'Validation failed. Please check your inputs.',
            '/auth/signup': 'Account creation failed. Please verify your information is correct.',
            '/auth/login': 'Login failed. Please check your email and password.',
            '/auth/forgot-password': 'Password reset failed. Please try again.',
            'default': 'Something went wrong. Please try again in a moment.'
        };
        
        // Status-specific messages
        const statusMessages = {
            400: 'Invalid request. Please check your input.',
            401: 'Authentication required. Please log in.',
            403: 'Access denied. You don\'t have permission for this action.',
            404: 'The requested resource was not found.',
            429: 'Too many requests. Please wait a moment and try again.',
            500: 'Server error. Our team has been notified.',
            502: 'Service temporarily unavailable. Please try again.',
            503: 'Service temporarily unavailable. Please try again.',
            504: 'Request timeout. Please try again.'
        };
        
        // Check for specific status code messages first
        if (error.status && statusMessages[error.status]) {
            return statusMessages[error.status];
        }
        
        // Then check endpoint-specific messages
        for (const [path, message] of Object.entries(endpointMessages)) {
            if (endpoint.includes(path)) {
                return message;
            }
        }
        
        return endpointMessages.default;
    }
    
    showErrorMessage(message, duration = 5000, options = {}) {
        const errorDiv = this.createToast(message, 'error', {
            dismissible: true,
            action: options.action,
            ...options
        });
        
        this.displayToast(errorDiv, duration);
        return errorDiv;
    }
    
    showSuccessMessage(message, duration = 3000, options = {}) {
        const successDiv = this.createToast(message, 'success', {
            dismissible: true,
            ...options
        });
        
        this.displayToast(successDiv, duration);
        return successDiv;
    }
    
    showRetryMessage(endpoint, attempt) {
        const endpointName = endpoint.split('/').pop() || 'request';
        const message = `Retrying ${endpointName}... (attempt ${attempt}/${this.maxRetries})`;
        
        const retryDiv = this.createToast(message, 'retry', {
            dismissible: false,
            showSpinner: true
        });
        
        this.displayToast(retryDiv, 2500);
        return retryDiv;
    }
    
    createToast(message, type, options = {}) {
        const toast = document.createElement('div');
        const isMobile = window.innerWidth < 768;
        
        // Mobile-first responsive classes
        const baseClasses = isMobile 
            ? 'toast fixed top-4 left-4 right-4 z-50 p-4 rounded-lg shadow-lg'
            : 'toast fixed top-4 right-4 z-50 max-w-sm p-4 rounded-lg shadow-lg';
            
        toast.className = `${baseClasses} transform transition-all duration-300 ease-out`;
        
        const colors = {
            error: 'bg-red-500 text-white border-l-4 border-red-700',
            retry: 'bg-yellow-500 text-white border-l-4 border-yellow-700', 
            success: 'bg-green-500 text-white border-l-4 border-green-700',
            info: 'bg-blue-500 text-white border-l-4 border-blue-700',
            warning: 'bg-orange-500 text-white border-l-4 border-orange-700'
        };
        
        toast.className += ` ${colors[type]}`;
        
        const iconHtml = options.showSpinner 
            ? '<div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-3"></div>'
            : `<i class="fas fa-${this.getIcon(type)} mr-3"></i>`;
        
        const actionHtml = options.action 
            ? `<button class="toast-action ml-3 underline text-sm opacity-90 hover:opacity-100">${options.action.text}</button>`
            : '';
            
        const dismissHtml = options.dismissible
            ? '<button class="toast-dismiss ml-auto pl-3 opacity-75 hover:opacity-100"><i class="fas fa-times"></i></button>'
            : '';
        
        toast.innerHTML = `
            <div class="flex items-center ${isMobile ? 'text-center justify-center' : ''}">
                ${iconHtml}
                <span class="flex-1">${message}</span>
                ${actionHtml}
                ${dismissHtml}
            </div>
        `;
        
        // Add event listeners
        if (options.dismissible) {
            toast.querySelector('.toast-dismiss')?.addEventListener('click', () => {
                this.dismissToast(toast);
            });
        }
        
        if (options.action && options.action.callback) {
            toast.querySelector('.toast-action')?.addEventListener('click', () => {
                options.action.callback();
                this.dismissToast(toast);
            });
        }
        
        return toast;
    }
    
    displayToast(toast, duration) {
        document.body.appendChild(toast);
        
        // Trigger animation
        requestAnimationFrame(() => {
            toast.style.transform = 'translateX(0) scale(1)';
            toast.style.opacity = '1';
        });
        
        // Auto-dismiss if duration specified
        if (duration > 0) {
            setTimeout(() => {
                this.dismissToast(toast);
            }, duration);
        }
    }
    
    dismissToast(toast) {
        if (!toast || !toast.parentNode) return;
        
        toast.style.transform = 'translateX(100%) scale(0.95)';
        toast.style.opacity = '0';
        
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 300);
    }
    
    getIcon(type) {
        const icons = {
            error: 'exclamation-triangle',
            retry: 'sync-alt',
            success: 'check-circle',
            info: 'info-circle',
            warning: 'exclamation-circle'
        };
        return icons[type] || 'info-circle';
    }
    
    createNetworkStatusIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'network-status-indicator';
        indicator.className = 'network-status fixed top-0 left-0 right-0 z-50 text-center py-2 text-sm font-medium transform -translate-y-full transition-transform duration-300';
        document.body.appendChild(indicator);
    }
    
    showNetworkError(type = 'offline') {
        const indicator = document.getElementById('network-status-indicator');
        if (!indicator) return;
        
        const messages = {
            offline: 'You are offline. Some features may not work.',
            slow: 'Slow connection detected. Please be patient.',
            reconnecting: 'Reconnecting...'
        };
        
        const colors = {
            offline: 'bg-red-500 text-white',
            slow: 'bg-yellow-500 text-white',
            reconnecting: 'bg-blue-500 text-white'
        };
        
        indicator.textContent = messages[type];
        indicator.className = indicator.className.replace(/bg-\w+-\d+/, colors[type]);
        indicator.style.transform = 'translateY(0)';
    }
    
    hideNetworkError() {
        const indicator = document.getElementById('network-status-indicator');
        if (indicator) {
            indicator.style.transform = 'translateY(-100%)';
        }
    }
    
    handleNetworkError(error, url) {
        console.warn('Network error detected:', error, 'URL:', url);
        
        if (this.networkStatus === 'online') {
            this.showNetworkError('slow');
            setTimeout(() => this.hideNetworkError(), 3000);
        }
    }
    
    handleError(error, context, metadata = {}) {
        const errorInfo = {
            message: error.message || 'Unknown error',
            stack: error.stack,
            context,
            metadata,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            url: window.location.href
        };
        
        console.error('VectorBid Error:', errorInfo);
        
        // Don't show user notification for certain error types
        const silentErrors = ['unhandled_promise', 'javascript_error'];
        if (!silentErrors.includes(context)) {
            this.showErrorMessage('An unexpected error occurred. Please try refreshing the page.');
        }
    }
    
    logError(error, endpoint, retryCount) {
        const errorLog = {
            endpoint,
            error: {
                message: error.message,
                status: error.status,
                name: error.name
            },
            retryCount,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent
        };
        
        console.error('API Error Log:', errorLog);
        
        // In production, send to error tracking service
        if (window.location.hostname !== 'localhost') {
            // Example: send to error tracking service
            // this.sendToErrorService(errorLog);
        }
    }
    
    initializeErrorReporting() {
        // Set up initial toast styles
        if (!document.getElementById('toast-styles')) {
            const style = document.createElement('style');
            style.id = 'toast-styles';
            style.textContent = `
                .toast {
                    transform: translateX(100%) scale(0.95);
                    opacity: 0;
                    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
                    backdrop-filter: blur(10px);
                }
                
                .toast-action:hover {
                    text-decoration: underline;
                }
                
                .toast-dismiss:hover {
                    opacity: 1 !important;
                }
                
                @media (max-width: 768px) {
                    .toast {
                        margin: 0 1rem;
                        max-width: calc(100vw - 2rem);
                    }
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    // Public API for manual error reporting
    reportError(message, context = 'manual', options = {}) {
        this.showErrorMessage(message, options.duration, options);
    }
    
    reportSuccess(message, options = {}) {
        this.showSuccessMessage(message, options.duration, options);
    }
    
    // Cleanup method
    destroy() {
        const indicator = document.getElementById('network-status-indicator');
        if (indicator) {
            indicator.remove();
        }
        
        document.querySelectorAll('.toast').forEach(toast => toast.remove());
        
        this.retryAttempts.clear();
    }
}

// Initialize global error handler
window.VectorBidErrors = new VectorBidErrorHandler();

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VectorBidErrorHandler;
}
