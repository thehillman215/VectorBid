// VectorBid Screen Reader Announcements Manager
// Provides accessible announcements for dynamic content and user interactions

class AccessibilityAnnouncer {
    constructor() {
        this.liveRegions = {
            polite: this.createLiveRegion('polite'),
            assertive: this.createLiveRegion('assertive')
        };
        
        this.announcementQueue = [];
        this.isProcessing = false;
        this.debounceTimeout = null;
        this.lastAnnouncement = '';
        this.lastAnnouncementTime = 0;
        
        // Configuration
        this.config = {
            maxQueueSize: 10,
            debounceDelay: 100,
            duplicateThreshold: 1000, // ms
            enableLogging: window.location.hostname === 'localhost'
        };
        
        this.setupKeyboardShortcuts();
    }
    
    createLiveRegion(priority) {
        const region = document.createElement('div');
        region.className = 'sr-only';
        region.setAttribute('aria-live', priority);
        region.setAttribute('aria-atomic', 'true');
        region.setAttribute('role', priority === 'assertive' ? 'alert' : 'status');
        region.id = `a11y-live-${priority}`;
        
        // Ensure it's added to the document
        if (document.body) {
            document.body.appendChild(region);
        } else {
            document.addEventListener('DOMContentLoaded', () => {
                document.body.appendChild(region);
            });
        }
        
        return region;
    }
    
    announce(message, priority = 'polite', options = {}) {
        if (!message || typeof message !== 'string') {
            console.warn('AccessibilityAnnouncer: Invalid message provided');
            return;
        }
        
        const cleanMessage = message.trim();
        if (!cleanMessage) return;
        
        // Prevent duplicate announcements within threshold
        const now = Date.now();
        if (cleanMessage === this.lastAnnouncement && 
            (now - this.lastAnnouncementTime) < this.config.duplicateThreshold) {
            this.log('Duplicate announcement prevented:', cleanMessage);
            return;
        }
        
        const announcement = {
            message: cleanMessage,
            priority: priority,
            timestamp: now,
            delay: options.delay || 0,
            clear: options.clear || false,
            force: options.force || false,
            interrupt: options.interrupt || false
        };
        
        // Clear queue if requested
        if (options.clear) {
            this.clearQueue();
        }
        
        // Interrupt current processing if requested
        if (options.interrupt && this.isProcessing) {
            this.clearQueue();
            this.isProcessing = false;
        }
        
        // Manage queue size
        if (this.announcementQueue.length >= this.config.maxQueueSize) {
            // Remove oldest non-critical announcements
            const criticalTypes = ['assertive', 'alert'];
            let removed = false;
            
            for (let i = 0; i < this.announcementQueue.length; i++) {
                if (!criticalTypes.includes(this.announcementQueue[i].priority)) {
                    this.announcementQueue.splice(i, 1);
                    removed = true;
                    break;
                }
            }
            
            if (!removed) {
                // If all are critical, remove oldest
                this.announcementQueue.shift();
            }
        }
        
        // Add to queue
        this.announcementQueue.push(announcement);
        
        this.log('Announcement queued:', cleanMessage, priority);
        
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
            
            // Update tracking
            this.lastAnnouncement = announcement.message;
            this.lastAnnouncementTime = announcement.timestamp;
            
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
            console.warn('AccessibilityAnnouncer: Invalid announcement priority:', announcement.priority);
            return;
        }
        
        // Clear previous announcement
        region.textContent = '';
        
        // Add new announcement (small delay ensures screen readers notice the change)
        setTimeout(() => {
            region.textContent = announcement.message;
            this.log('Announced:', announcement.message, announcement.priority);
        }, 10);
    }
    
    clearQueue() {
        this.announcementQueue = [];
        this.log('Announcement queue cleared');
    }
    
    // Convenience methods for common announcement types
    announcePageChange(title, description = '') {
        const message = description 
            ? `Page changed to ${title}. ${description}`
            : `Page changed to ${title}`;
            
        this.announce(message, 'assertive', { clear: true });
    }
    
    announceFormError(fieldName, errorMessage) {
        this.announce(
            `Error in ${fieldName}: ${errorMessage}`,
            'assertive',
            { interrupt: true }
        );
    }
    
    announceFormSuccess(message) {
        this.announce(
            `Success: ${message}`,
            'polite'
        );
    }
    
    announceFormValidation(fieldName, isValid, message = '') {
        if (isValid) {
            this.announce(
                `${fieldName} is valid`,
                'polite'
            );
        } else {
            this.announceFormError(fieldName, message);
        }
    }
    
    announceLoadingStart(context, details = '') {
        const message = details 
            ? `Loading ${context}. ${details}`
            : `Loading ${context}, please wait.`;
            
        this.announce(message, 'polite');
    }
    
    announceLoadingComplete(context) {
        this.announce(
            `${context} loaded successfully.`,
            'polite'
        );
    }
    
    announceLoadingError(context, error = '') {
        const message = error 
            ? `Failed to load ${context}. ${error}`
            : `Failed to load ${context}. Please try again.`;
            
        this.announce(message, 'assertive');
    }
    
    announceProgress(current, total, context = 'Progress') {
        const percentage = Math.round((current / total) * 100);
        this.announce(
            `${context}: ${percentage}% complete. ${current} of ${total}.`,
            'polite'
        );
    }
    
    announceInteraction(action, element = '', result = '') {
        let message = `${action}`;
        
        if (element) {
            message += ` ${element}`;
        }
        
        if (result) {
            message += `. ${result}`;
        }
        
        this.announce(message, 'polite');
    }
    
    announceNavigation(direction, currentItem, totalItems) {
        this.announce(
            `${direction}. ${currentItem} of ${totalItems}.`,
            'polite'
        );
    }
    
    announceModal(action, title = '') {
        let message;
        
        switch (action) {
            case 'opened':
                message = title ? `${title} dialog opened` : 'Dialog opened';
                break;
            case 'closed':
                message = title ? `${title} dialog closed` : 'Dialog closed';
                break;
            default:
                message = `Dialog ${action}`;
        }
        
        this.announce(message, 'assertive');
    }
    
    announceSort(column, direction) {
        this.announce(
            `Table sorted by ${column}, ${direction}`,
            'polite'
        );
    }
    
    announceFilter(filterType, value, resultCount) {
        this.announce(
            `Filtered by ${filterType}: ${value}. ${resultCount} results found.`,
            'polite'
        );
    }
    
    announceSelection(itemType, count, action = 'selected') {
        const itemLabel = count === 1 ? itemType : `${itemType}s`;
        this.announce(
            `${count} ${itemLabel} ${action}`,
            'polite'
        );
    }
    
    // Keyboard shortcuts for accessibility testing
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Alt + Shift + A = Test announcement
            if (e.altKey && e.shiftKey && e.key === 'A') {
                e.preventDefault();
                this.announce('Accessibility announcer is working properly', 'assertive');
            }
            
            // Alt + Shift + Q = Show queue status
            if (e.altKey && e.shiftKey && e.key === 'Q') {
                e.preventDefault();
                this.announce(`${this.announcementQueue.length} announcements in queue`, 'polite');
            }
        });
    }
    
    // Status and debugging methods
    getStatus() {
        return {
            queueLength: this.announcementQueue.length,
            isProcessing: this.isProcessing,
            lastAnnouncement: this.lastAnnouncement,
            lastAnnouncementTime: this.lastAnnouncementTime,
            regionsAvailable: Object.keys(this.liveRegions).every(key => 
                this.liveRegions[key] && this.liveRegions[key].parentNode
            )
        };
    }
    
    log(message, ...args) {
        if (this.config.enableLogging) {
            console.debug('[A11y Announcer]', message, ...args);
        }
    }
    
    // Test methods for accessibility validation
    testAnnouncements() {
        this.announce('Testing polite announcement', 'polite');
        
        setTimeout(() => {
            this.announce('Testing assertive announcement', 'assertive');
        }, 1000);
        
        setTimeout(() => {
            this.announceFormError('test field', 'this is a test error');
        }, 2000);
        
        setTimeout(() => {
            this.announceFormSuccess('Test form submitted successfully');
        }, 3000);
    }
    
    // Public API for dynamic announcement configuration
    updateConfig(newConfig) {
        this.config = { ...this.config, ...newConfig };
    }
    
    // Check if screen reader might be active
    isScreenReaderLikely() {
        // Heuristic checks for screen reader presence
        return (
            window.navigator.userAgent.includes('NVDA') ||
            window.navigator.userAgent.includes('JAWS') ||
            window.speechSynthesis ||
            document.body.classList.contains('sr-active') ||
            window.getComputedStyle(document.documentElement).getPropertyValue('--screen-reader-detected') === 'true'
        );
    }
    
    // Enhanced announcement for complex interactions
    announceComplex(parts, priority = 'polite', options = {}) {
        const message = Array.isArray(parts) ? parts.join('. ') : parts;
        this.announce(message, priority, options);
    }
    
    // Cleanup method
    destroy() {
        this.clearQueue();
        
        Object.values(this.liveRegions).forEach(region => {
            if (region && region.parentNode) {
                region.parentNode.removeChild(region);
            }
        });
        
        this.liveRegions = {};
    }
}

// Initialize global accessibility announcer
window.A11yAnnouncer = new AccessibilityAnnouncer();

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AccessibilityAnnouncer;
}

// Auto-test on load in development
if (window.location.hostname === 'localhost' && window.location.search.includes('a11y-test')) {
    window.addEventListener('load', () => {
        setTimeout(() => {
            window.A11yAnnouncer.testAnnouncements();
        }, 2000);
    });
}
