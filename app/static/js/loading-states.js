// VectorBid Loading State Manager
// Comprehensive loading state management with cancellation and mobile optimization

class LoadingStateManager {
    constructor() {
        this.activeLoading = new Map();
        this.loadingQueue = new Set();
        this.globalLoadingCount = 0;
        this.isMobile = window.innerWidth < 768;
        this.createGlobalSpinner();
        this.setupResponsiveHandler();
        this.initializeProgressBars();
    }
    
    /**
     * Show loading state for a specific element or globally
     * @param {string|Element} element - Element or selector to show loading for
     * @param {string} message - Loading message to display
     * @param {Object} options - Configuration options
     * @returns {string} Loading ID for later removal
     */
    show(element, message = 'Loading...', options = {}) {
        const loadingId = this.generateId();
        this.activeLoading.set(loadingId, {
            element,
            message,
            options,
            startTime: Date.now()
        });
        
        // Handle different element types
        if (typeof element === 'string') {
            element = document.querySelector(element);
        }
        
        if (!element && !options.global) {
            console.warn('LoadingStateManager: Element not found, falling back to global loading');
            options.global = true;
        }
        
        if (options.global) {
            return this.showGlobalLoading(loadingId, message, options);
        }
        
        return this.showElementLoading(element, loadingId, message, options);
    }
    
    showElementLoading(element, loadingId, message, options) {
        if (!element) return loadingId;
        
        // Store original position
        const originalPosition = getComputedStyle(element).position;
        if (originalPosition === 'static') {
            element.style.position = 'relative';
            element.setAttribute('data-original-position', 'static');
        }
        
        // Create loading overlay
        const overlay = document.createElement('div');
        overlay.className = this.getOverlayClasses(options);
        overlay.setAttribute('data-loading-id', loadingId);
        overlay.setAttribute('role', 'status');
        overlay.setAttribute('aria-live', 'polite');
        overlay.setAttribute('aria-label', message);
        
        const loadingContent = this.createLoadingContent(message, options);
        overlay.appendChild(loadingContent);
        
        // Add to element
        element.appendChild(overlay);
        
        // Disable form elements if it's a form
        if (element.tagName === 'FORM' || element.querySelector('form')) {
            this.disableFormElements(element, loadingId);
        }
        
        // Handle cancellation
        if (options.showCancel && options.onCancel) {
            this.setupCancellation(overlay, loadingId, options.onCancel);
        }
        
        // Auto-timeout
        if (options.timeout) {
            setTimeout(() => {
                if (this.activeLoading.has(loadingId)) {
                    this.hide(loadingId);
                    if (options.onTimeout) {
                        options.onTimeout();
                    }
                }
            }, options.timeout);
        }
        
        // Animate in
        this.animateIn(overlay);
        
        return loadingId;
    }
    
    showGlobalLoading(loadingId, message, options) {
        this.globalLoadingCount++;
        
        let globalOverlay = document.getElementById('global-loading-overlay');
        
        if (!globalOverlay) {
            globalOverlay = document.createElement('div');
            globalOverlay.id = 'global-loading-overlay';
            globalOverlay.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center backdrop-blur-sm';
            globalOverlay.setAttribute('role', 'status');
            globalOverlay.setAttribute('aria-live', 'polite');
            
            const modalContent = document.createElement('div');
            modalContent.className = this.isMobile 
                ? 'bg-white rounded-lg p-6 m-4 max-w-sm w-full text-center shadow-2xl'
                : 'bg-white rounded-lg p-8 max-w-md w-full text-center shadow-2xl';
            modalContent.id = 'global-loading-content';
            
            globalOverlay.appendChild(modalContent);
            document.body.appendChild(globalOverlay);
            
            // Prevent body scroll
            document.body.style.overflow = 'hidden';
        }
        
        // Update content
        const content = globalOverlay.querySelector('#global-loading-content');
        content.innerHTML = this.createLoadingContent(message, {
            ...options,
            isGlobal: true
        }).innerHTML;
        
        // Setup cancellation for global loading
        if (options.showCancel && options.onCancel) {
            this.setupCancellation(content, loadingId, options.onCancel);
        }
        
        // Show with animation
        globalOverlay.style.opacity = '0';
        globalOverlay.style.display = 'flex';
        
        requestAnimationFrame(() => {
            globalOverlay.style.opacity = '1';
            globalOverlay.style.transform = 'scale(1)';
        });
        
        return loadingId;
    }
    
    createLoadingContent(message, options = {}) {
        const content = document.createElement('div');
        content.className = 'loading-content text-center';
        
        const spinnerType = options.spinnerType || 'default';
        const showProgress = options.showProgress;
        const isGlobal = options.isGlobal;
        
        let spinnerHtml = '';
        
        switch (spinnerType) {
            case 'pulse':
                spinnerHtml = `
                    <div class="loading-pulse flex space-x-1 justify-center mb-4">
                        <div class="w-3 h-3 bg-blue-600 rounded-full animate-pulse"></div>
                        <div class="w-3 h-3 bg-blue-600 rounded-full animate-pulse" style="animation-delay: 0.1s"></div>
                        <div class="w-3 h-3 bg-blue-600 rounded-full animate-pulse" style="animation-delay: 0.2s"></div>
                    </div>
                `;
                break;
            case 'bars':
                spinnerHtml = `
                    <div class="loading-bars flex space-x-1 justify-center mb-4">
                        <div class="w-1 h-6 bg-blue-600 animate-bounce"></div>
                        <div class="w-1 h-6 bg-blue-600 animate-bounce" style="animation-delay: 0.1s"></div>
                        <div class="w-1 h-6 bg-blue-600 animate-bounce" style="animation-delay: 0.2s"></div>
                        <div class="w-1 h-6 bg-blue-600 animate-bounce" style="animation-delay: 0.3s"></div>
                    </div>
                `;
                break;
            default:
                const spinnerSize = isGlobal ? 'h-12 w-12' : 'h-8 w-8';
                spinnerHtml = `
                    <div class="spinner-border ${spinnerSize} border-b-2 border-blue-600 rounded-full animate-spin mx-auto mb-4"></div>
                `;
        }
        
        const progressHtml = showProgress ? `
            <div class="progress-container mb-4">
                <div class="w-full bg-gray-200 rounded-full h-2">
                    <div class="bg-blue-600 h-2 rounded-full transition-all duration-300" id="progress-bar-${Date.now()}" style="width: 0%"></div>
                </div>
            </div>
        ` : '';
        
        const messageHtml = `
            <h3 class="text-lg font-semibold mb-2 text-gray-800">${this.getLoadingTitle(options)}</h3>
            <p class="text-gray-600 mb-4">${message}</p>
        `;
        
        const cancelHtml = options.showCancel ? `
            <button class="cancel-loading px-4 py-2 text-sm text-gray-500 hover:text-gray-700 underline transition-colors">
                <i class="fas fa-times mr-1"></i>Cancel
            </button>
        ` : '';
        
        content.innerHTML = `
            ${spinnerHtml}
            ${progressHtml}
            ${messageHtml}
            ${cancelHtml}
        `;
        
        return content;
    }
    
    getLoadingTitle(options) {
        if (options.title) return options.title;
        
        const titles = {
            api: 'Processing Request',
            upload: 'Uploading Files',
            download: 'Downloading Data',
            save: 'Saving Changes',
            delete: 'Deleting Item',
            auth: 'Authenticating',
            validate: 'Validating Data',
            optimize: 'AI Processing'
        };
        
        return titles[options.type] || 'Loading';
    }
    
    setupCancellation(container, loadingId, onCancel) {
        const cancelBtn = container.querySelector('.cancel-loading');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                this.hide(loadingId);
                if (onCancel) {
                    onCancel();
                }
            });
        }
    }
    
    disableFormElements(element, loadingId) {
        const formElements = element.querySelectorAll('input, button, select, textarea');
        const disabledElements = [];
        
        formElements.forEach(el => {
            if (!el.disabled) {
                el.disabled = true;
                disabledElements.push(el);
            }
        });
        
        // Store for re-enabling later
        this.activeLoading.get(loadingId).disabledElements = disabledElements;
    }
    
    getOverlayClasses(options) {
        const baseClasses = 'loading-overlay absolute inset-0 flex items-center justify-center z-40 transition-opacity duration-200';
        
        const backgroundClasses = options.transparent 
            ? 'bg-transparent'
            : 'bg-white bg-opacity-90 backdrop-blur-sm';
            
        return `${baseClasses} ${backgroundClasses}`;
    }
    
    animateIn(overlay) {
        overlay.style.opacity = '0';
        overlay.style.transform = 'scale(0.95)';
        
        requestAnimationFrame(() => {
            overlay.style.opacity = '1';
            overlay.style.transform = 'scale(1)';
        });
    }
    
    /**
     * Hide loading state by ID
     * @param {string} loadingId - ID of loading state to hide
     */
    hide(loadingId) {
        if (!this.activeLoading.has(loadingId)) {
            console.warn('LoadingStateManager: Attempted to hide non-existent loading state:', loadingId);
            return;
        }
        
        const loadingData = this.activeLoading.get(loadingId);
        const overlay = document.querySelector(`[data-loading-id="${loadingId}"]`);
        
        if (overlay) {
            this.animateOut(overlay, () => {
                overlay.remove();
                this.restoreElement(loadingData);
            });
        } else if (loadingData.options.global) {
            this.hideGlobalLoading();
        }
        
        this.activeLoading.delete(loadingId);
    }
    
    hideGlobalLoading() {
        this.globalLoadingCount = Math.max(0, this.globalLoadingCount - 1);
        
        if (this.globalLoadingCount === 0) {
            const globalOverlay = document.getElementById('global-loading-overlay');
            if (globalOverlay) {
                this.animateOut(globalOverlay, () => {
                    globalOverlay.remove();
                    document.body.style.overflow = '';
                });
            }
        }
    }
    
    animateOut(element, callback) {
        element.style.opacity = '0';
        element.style.transform = 'scale(0.95)';
        
        setTimeout(() => {
            if (callback) callback();
        }, 200);
    }
    
    restoreElement(loadingData) {
        if (loadingData.disabledElements) {
            loadingData.disabledElements.forEach(el => {
                el.disabled = false;
            });
        }
        
        // Restore original position if we changed it
        if (typeof loadingData.element === 'object' && loadingData.element.hasAttribute('data-original-position')) {
            loadingData.element.style.position = loadingData.element.getAttribute('data-original-position');
            loadingData.element.removeAttribute('data-original-position');
        }
    }
    
    /**
     * Hide all active loading states
     */
    hideAll() {
        // Hide element-specific loading states
        document.querySelectorAll('.loading-overlay').forEach(overlay => {
            overlay.remove();
        });
        
        // Hide global loading
        const globalOverlay = document.getElementById('global-loading-overlay');
        if (globalOverlay) {
            globalOverlay.remove();
            document.body.style.overflow = '';
        }
        
        // Restore all disabled elements
        this.activeLoading.forEach(loadingData => {
            this.restoreElement(loadingData);
        });
        
        this.activeLoading.clear();
        this.globalLoadingCount = 0;
    }
    
    /**
     * Update progress for a loading state
     * @param {string} loadingId - Loading ID
     * @param {number} progress - Progress percentage (0-100)
     * @param {string} message - Optional new message
     */
    updateProgress(loadingId, progress, message) {
        const progressBar = document.querySelector(`#progress-bar-${loadingId}`);
        if (progressBar) {
            progressBar.style.width = `${Math.min(100, Math.max(0, progress))}%`;
        }
        
        if (message) {
            const loadingData = this.activeLoading.get(loadingId);
            if (loadingData) {
                const overlay = document.querySelector(`[data-loading-id="${loadingId}"]`);
                const messageEl = overlay?.querySelector('p');
                if (messageEl) {
                    messageEl.textContent = message;
                }
            }
        }
    }
    
    /**
     * Check if a loading state is active
     * @param {string} loadingId - Loading ID to check
     * @returns {boolean}
     */
    isActive(loadingId) {
        return this.activeLoading.has(loadingId);
    }
    
    /**
     * Get all active loading states
     * @returns {Array} Array of loading state information
     */
    getActiveStates() {
        return Array.from(this.activeLoading.entries()).map(([id, data]) => ({
            id,
            message: data.message,
            duration: Date.now() - data.startTime,
            options: data.options
        }));
    }
    
    generateId() {
        return 'loading_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    }
    
    setupResponsiveHandler() {
        window.addEventListener('resize', () => {
            this.isMobile = window.innerWidth < 768;
            
            // Update global loading modal if active
            const globalContent = document.getElementById('global-loading-content');
            if (globalContent) {
                globalContent.className = this.isMobile 
                    ? 'bg-white rounded-lg p-6 m-4 max-w-sm w-full text-center shadow-2xl'
                    : 'bg-white rounded-lg p-8 max-w-md w-full text-center shadow-2xl';
            }
        });
    }
    
    createGlobalSpinner() {
        // Inject necessary CSS for loading states
        if (!document.getElementById('loading-states-css')) {
            const style = document.createElement('style');
            style.id = 'loading-states-css';
            style.textContent = `
                .spinner-border {
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
                    animation: fadeIn 0.2s ease-out;
                }
                
                @keyframes fadeIn {
                    from {
                        opacity: 0;
                        transform: scale(0.95);
                    }
                    to {
                        opacity: 1;
                        transform: scale(1);
                    }
                }
                
                .loading-pulse .animate-pulse {
                    animation: pulse 1.5s infinite;
                }
                
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.3; }
                }
                
                .loading-bars .animate-bounce {
                    animation: bounce 1s infinite;
                }
                
                @keyframes bounce {
                    0%, 100% { transform: translateY(0); }
                    50% { transform: translateY(-10px); }
                }
                
                /* Mobile optimizations */
                @media (max-width: 768px) {
                    .loading-overlay {
                        padding: 1rem;
                    }
                    
                    .loading-content h3 {
                        font-size: 1rem;
                    }
                    
                    .loading-content p {
                        font-size: 0.875rem;
                    }
                }
                
                /* High contrast mode support */
                @media (prefers-contrast: high) {
                    .loading-overlay {
                        background-color: rgba(255, 255, 255, 0.95) !important;
                        border: 2px solid #000;
                    }
                    
                    .spinner-border {
                        border-top-color: #000 !important;
                    }
                }
                
                /* Reduced motion support */
                @media (prefers-reduced-motion: reduce) {
                    .spinner-border,
                    .animate-spin,
                    .animate-pulse,
                    .animate-bounce {
                        animation: none !important;
                    }
                    
                    .loading-overlay {
                        animation: none !important;
                        opacity: 1 !important;
                        transform: none !important;
                    }
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    initializeProgressBars() {
        // Set up progress bar utility methods
        this.progressBars = new Map();
    }
    
    /**
     * Simulate progress for better UX during long operations
     * @param {string} loadingId - Loading ID
     * @param {number} duration - Expected duration in ms
     * @param {Function} onComplete - Callback when complete
     */
    simulateProgress(loadingId, duration = 5000, onComplete) {
        let progress = 0;
        const increment = 100 / (duration / 100);
        
        const interval = setInterval(() => {
            progress += increment;
            
            if (progress >= 95) {
                clearInterval(interval);
                return;
            }
            
            this.updateProgress(loadingId, progress);
        }, 100);
        
        // Complete progress when operation finishes
        const originalComplete = onComplete;
        onComplete = () => {
            clearInterval(interval);
            this.updateProgress(loadingId, 100);
            setTimeout(() => {
                if (originalComplete) originalComplete();
            }, 200);
        };
        
        return onComplete;
    }
    
    /**
     * Clean up and destroy the loading manager
     */
    destroy() {
        this.hideAll();
        
        const style = document.getElementById('loading-states-css');
        if (style) {
            style.remove();
        }
        
        this.activeLoading.clear();
        this.loadingQueue.clear();
    }
}

// Initialize global loading manager
window.LoadingStates = new LoadingStateManager();

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LoadingStateManager;
}
