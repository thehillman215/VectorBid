// VectorBid Performance Monitor
// Comprehensive performance monitoring with Web Vitals, resource tracking, and analytics

class PerformanceMonitor {
    constructor(namespace = 'VectorBid') {
        this.namespace = namespace;
        this.metrics = new Map();
        this.marks = new Map();
        this.measures = new Map();
        this.observers = [];
        this.resourceCache = new Map();
        this.navigationMetrics = {};
        this.webVitals = {};
        this.customMetrics = new Map();
        
        // Configuration
        this.config = {
            enableDetailedLogging: window.location.hostname === 'localhost',
            maxMetricHistory: 100,
            reportingInterval: 30000, // 30 seconds
            enableWebVitals: true,
            enableResourceMonitoring: true,
            enableMemoryMonitoring: true,
            enableNetworkMonitoring: true
        };
        
        this.init();
    }
    
    init() {
        this.setupPerformanceObservers();
        this.startResourceMonitoring();
        this.startMemoryMonitoring();
        this.startNetworkMonitoring();
        this.setupWebVitalsTracking();
        this.setupNavigationTracking();
        this.setupErrorTracking();
        
        this.mark('performance-monitor-initialized');
        
        // Start periodic reporting
        this.startPeriodicReporting();
    }
    
    mark(name, detail = {}) {
        const markName = `${this.namespace}:${name}`;
        const timestamp = performance.now();
        
        try {
            if ('performance' in window && 'mark' in performance) {
                performance.mark(markName, { detail });
            }
        } catch (error) {
            console.warn('Performance mark failed:', error);
        }
        
        this.marks.set(name, {
            timestamp: timestamp,
            detail: detail,
            realTime: Date.now()
        });
        
        this.logEvent('MARK', name, { timestamp, detail });
    }
    
    measure(name, startMark, endMark = null) {
        const measureName = `${this.namespace}:${name}`;
        const startMarkName = startMark ? `${this.namespace}:${startMark}` : undefined;
        const endMarkName = endMark ? `${this.namespace}:${endMark}` : undefined;
        
        let duration = null;
        
        try {
            if ('performance' in window && 'measure' in performance) {
                const measure = performance.measure(measureName, startMarkName, endMarkName);
                duration = measure.duration;
            }
        } catch (error) {
            console.warn('Performance measure failed:', error);
        }
        
        // Fallback measurement
        if (!duration) {
            const startTime = this.marks.get(startMark)?.timestamp || 0;
            const endTime = endMark ? this.marks.get(endMark)?.timestamp : performance.now();
            duration = endTime - startTime;
        }
        
        if (duration !== null) {
            this.measures.set(name, {
                duration: duration,
                startTime: this.marks.get(startMark)?.timestamp || 0,
                timestamp: performance.now(),
                realTime: Date.now()
            });
            
            this.recordMetric(`Measure.${name}`, duration, 'ms');
            this.logEvent('MEASURE', name, { duration });
        }
        
        return duration;
    }
    
    setupPerformanceObservers() {
        if (!('PerformanceObserver' in window)) return;
        
        try {
            // Navigation timing
            this.observeEntryType('navigation', (entries) => {
                entries.forEach(entry => this.processNavigationTiming(entry));
            });
            
            // Resource timing
            this.observeEntryType('resource', (entries) => {
                entries.forEach(entry => this.processResourceTiming(entry));
            });
            
            // Long tasks
            this.observeEntryType('longtask', (entries) => {
                entries.forEach(entry => this.processLongTask(entry));
            });
            
            // Layout shifts
            this.observeEntryType('layout-shift', (entries) => {
                entries.forEach(entry => this.processLayoutShift(entry));
            });
            
            // Largest contentful paint
            this.observeEntryType('largest-contentful-paint', (entries) => {
                const lastEntry = entries[entries.length - 1];
                this.webVitals.LCP = lastEntry.startTime;
                this.recordMetric('WebVitals.LCP', lastEntry.startTime, 'ms');
            });
            
            // First input delay (requires user interaction)
            this.observeEntryType('first-input', (entries) => {
                const firstInput = entries[0];
                this.webVitals.FID = firstInput.processingStart - firstInput.startTime;
                this.recordMetric('WebVitals.FID', this.webVitals.FID, 'ms');
            });
            
        } catch (error) {
            console.warn('Performance observer setup failed:', error);
        }
    }
    
    observeEntryType(entryType, callback) {
        try {
            const observer = new PerformanceObserver((list) => {
                callback(list.getEntries());
            });
            
            observer.observe({ entryTypes: [entryType] });
            this.observers.push(observer);
        } catch (error) {
            console.warn(`Failed to observe ${entryType}:`, error);
        }
    }
    
    processNavigationTiming(entry) {
        const timing = {
            'DNS_Lookup': entry.domainLookupEnd - entry.domainLookupStart,
            'TCP_Connection': entry.connectEnd - entry.connectStart,
            'TLS_Handshake': entry.secureConnectionStart > 0 ? entry.connectEnd - entry.secureConnectionStart : 0,
            'TTFB': entry.responseStart - entry.requestStart,
            'Response_Download': entry.responseEnd - entry.responseStart,
            'DOM_Processing': entry.domContentLoadedEventStart - entry.responseEnd,
            'Load_Complete': entry.loadEventEnd - entry.loadEventStart,
            'Total_Load_Time': entry.loadEventEnd - entry.fetchStart,
            'DOM_Interactive': entry.domInteractive - entry.fetchStart,
            'DOM_Content_Loaded': entry.domContentLoadedEventEnd - entry.fetchStart
        };
        
        // Record individual timing metrics
        Object.entries(timing).forEach(([name, value]) => {
            if (value >= 0) {
                this.recordMetric(`Navigation.${name}`, value, 'ms');
            }
        });
        
        this.navigationMetrics = { ...timing, timestamp: Date.now() };
        this.logEvent('NAVIGATION', 'timing', timing);
    }
    
    processResourceTiming(entry) {
        const resourceType = this.getResourceType(entry.name);
        const size = entry.transferSize || entry.encodedBodySize || 0;
        const loadTime = entry.responseEnd - entry.startTime;
        
        // Track resource metrics
        this.recordMetric(`Resource.${resourceType}.LoadTime`, loadTime, 'ms');
        this.recordMetric(`Resource.${resourceType}.Size`, size, 'bytes');
        
        // Detect slow resources
        if (loadTime > 1000) { // Slower than 1 second
            this.recordMetric('Resource.SlowLoads', 1, 'count');
            this.logEvent('SLOW_RESOURCE', entry.name, { loadTime, size, resourceType });
        }
        
        // Track failed resources
        if (entry.responseStatus >= 400 || entry.responseStatus === 0) {
            this.recordMetric('Resource.FailedLoads', 1, 'count');
            this.logEvent('FAILED_RESOURCE', entry.name, { status: entry.responseStatus, resourceType });
        }
        
        // Cache resource info for analysis
        this.resourceCache.set(entry.name, {
            type: resourceType,
            size: size,
            loadTime: loadTime,
            timestamp: Date.now()
        });
    }
    
    processLongTask(entry) {
        this.recordMetric('LongTask.Duration', entry.duration, 'ms');
        this.recordMetric('LongTask.Count', 1, 'count');
        
        if (entry.duration > 100) { // Very long task
            this.logEvent('LONG_TASK', 'blocking', { duration: entry.duration });
        }
    }
    
    processLayoutShift(entry) {
        if (!entry.hadRecentInput) {
            this.webVitals.CLS = (this.webVitals.CLS || 0) + entry.value;
            this.recordMetric('WebVitals.CLS', this.webVitals.CLS);
            
            if (entry.value > 0.1) {
                this.recordMetric('LayoutShift.Significant', 1, 'count');
                this.logEvent('LAYOUT_SHIFT', 'significant', { value: entry.value });
            }
        }
    }
    
    getResourceType(url) {
        const urlLower = url.toLowerCase();
        
        if (urlLower.includes('.js') || urlLower.includes('javascript')) return 'JavaScript';
        if (urlLower.includes('.css') || urlLower.includes('stylesheet')) return 'CSS';
        if (urlLower.match(/\.(png|jpg|jpeg|gif|svg|webp|avif)$/i)) return 'Image';
        if (urlLower.includes('font') || urlLower.match(/\.(woff|woff2|ttf|eot)$/i)) return 'Font';
        if (urlLower.includes('/api/') || urlLower.includes('json')) return 'API';
        if (urlLower.includes('.html')) return 'Document';
        if (urlLower.includes('video') || urlLower.match(/\.(mp4|webm|ogg)$/i)) return 'Video';
        if (urlLower.includes('audio') || urlLower.match(/\.(mp3|wav|ogg)$/i)) return 'Audio';
        
        return 'Other';
    }
    
    recordMetric(name, value, unit = 'ms') {
        if (!this.metrics.has(name)) {
            this.metrics.set(name, []);
        }
        
        const measurements = this.metrics.get(name);
        measurements.push({
            value: value,
            timestamp: performance.now(),
            realTime: Date.now(),
            unit: unit
        });
        
        // Keep only recent measurements
        if (measurements.length > this.config.maxMetricHistory) {
            measurements.splice(0, measurements.length - this.config.maxMetricHistory);
        }
        
        // Record custom metric
        this.customMetrics.set(name, value);
    }
    
    startResourceMonitoring() {
        if (!this.config.enableResourceMonitoring) return;
        
        // Monitor overall resource usage
        setInterval(() => {
            const resources = performance.getEntriesByType('resource');
            const totalSize = resources.reduce((sum, r) => sum + (r.transferSize || 0), 0);
            const totalResources = resources.length;
            
            this.recordMetric('Resource.TotalSize', totalSize, 'bytes');
            this.recordMetric('Resource.TotalCount', totalResources, 'count');
        }, 30000);
    }
    
    startMemoryMonitoring() {
        if (!this.config.enableMemoryMonitoring || !('memory' in performance)) return;
        
        const monitorMemory = () => {
            try {
                const memory = performance.memory;
                this.recordMetric('Memory.Used', memory.usedJSHeapSize, 'bytes');
                this.recordMetric('Memory.Total', memory.totalJSHeapSize, 'bytes');
                this.recordMetric('Memory.Limit', memory.jsHeapSizeLimit, 'bytes');
                
                const usagePercent = (memory.usedJSHeapSize / memory.jsHeapSizeLimit) * 100;
                this.recordMetric('Memory.UsagePercent', usagePercent, 'percent');
                
                // Alert on high memory usage
                if (usagePercent > 80) {
                    this.logEvent('MEMORY_WARNING', 'high_usage', { usagePercent });
                }
            } catch (error) {
                console.warn('Memory monitoring failed:', error);
            }
        };
        
        monitorMemory();
        setInterval(monitorMemory, 10000); // Every 10 seconds
    }
    
    startNetworkMonitoring() {
        if (!this.config.enableNetworkMonitoring || !('connection' in navigator)) return;
        
        const monitorConnection = () => {
            try {
                const connection = navigator.connection;
                this.recordMetric('Network.EffectiveType', this.connectionTypeToNumber(connection.effectiveType), 'level');
                this.recordMetric('Network.Downlink', connection.downlink || 0, 'mbps');
                this.recordMetric('Network.RTT', connection.rtt || 0, 'ms');
                
                if (connection.saveData) {
                    this.recordMetric('Network.SaveData', 1, 'boolean');
                }
            } catch (error) {
                console.warn('Network monitoring failed:', error);
            }
        };
        
        monitorConnection();
        
        // Monitor connection changes
        if ('addEventListener' in navigator.connection) {
            navigator.connection.addEventListener('change', monitorConnection);
        }
    }
    
    connectionTypeToNumber(effectiveType) {
        const types = { 'slow-2g': 1, '2g': 2, '3g': 3, '4g': 4, '5g': 5 };
        return types[effectiveType] || 0;
    }
    
    setupWebVitalsTracking() {
        if (!this.config.enableWebVitals) return;
        
        // Track Time to First Byte
        const observer = new PerformanceObserver((list) => {
            const navigationEntry = list.getEntries()[0];
            if (navigationEntry) {
                const ttfb = navigationEntry.responseStart - navigationEntry.requestStart;
                this.webVitals.TTFB = ttfb;
                this.recordMetric('WebVitals.TTFB', ttfb, 'ms');
            }
        });
        
        try {
            observer.observe({ entryTypes: ['navigation'] });
            this.observers.push(observer);
        } catch (error) {
            console.warn('Web Vitals tracking setup failed:', error);
        }
    }
    
    setupNavigationTracking() {
        // Track page visibility changes
        document.addEventListener('visibilitychange', () => {
            const state = document.visibilityState;
            this.recordMetric(`Page.Visibility.${state}`, 1, 'count');
            this.logEvent('VISIBILITY_CHANGE', state);
        });
        
        // Track page unload
        window.addEventListener('beforeunload', () => {
            this.generateFinalReport();
        });
        
        // Track page focus/blur
        window.addEventListener('focus', () => {
            this.recordMetric('Page.Focus', 1, 'count');
            this.mark('page-focused');
        });
        
        window.addEventListener('blur', () => {
            this.recordMetric('Page.Blur', 1, 'count');
            this.mark('page-blurred');
        });
    }
    
    setupErrorTracking() {
        // Track JavaScript errors
        window.addEventListener('error', (event) => {
            this.recordMetric('Error.JavaScript', 1, 'count');
            this.logEvent('JS_ERROR', event.filename, {
                message: event.message,
                line: event.lineno,
                column: event.colno
            });
        });
        
        // Track unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            this.recordMetric('Error.UnhandledPromise', 1, 'count');
            this.logEvent('PROMISE_REJECTION', 'unhandled', {
                reason: event.reason?.toString()
            });
        });
    }
    
    startPeriodicReporting() {
        setInterval(() => {
            this.generateReport();
        }, this.config.reportingInterval);
    }
    
    getMetricSummary(name) {
        const measurements = this.metrics.get(name);
        if (!measurements || measurements.length === 0) {
            return null;
        }
        
        const values = measurements.map(m => m.value);
        const sorted = [...values].sort((a, b) => a - b);
        
        return {
            count: values.length,
            min: Math.min(...values),
            max: Math.max(...values),
            avg: values.reduce((a, b) => a + b, 0) / values.length,
            median: sorted[Math.floor(sorted.length / 2)],
            p90: sorted[Math.floor(sorted.length * 0.9)],
            p95: sorted[Math.floor(sorted.length * 0.95)],
            latest: values[values.length - 1],
            unit: measurements[0].unit
        };
    }
    
    getAllMetrics() {
        const summary = {};
        for (const [name] of this.metrics) {
            summary[name] = this.getMetricSummary(name);
        }
        return summary;
    }
    
    getWebVitals() {
        return {
            ...this.webVitals,
            timestamp: Date.now()
        };
    }
    
    generateReport() {
        const report = {
            timestamp: new Date().toISOString(),
            session: this.getSessionInfo(),
            navigation: this.navigationMetrics,
            webVitals: this.getWebVitals(),
            metrics: this.getAllMetrics(),
            marks: Object.fromEntries(this.marks),
            measures: Object.fromEntries(this.measures),
            resources: this.getResourceSummary(),
            performance: this.getPerformanceSummary()
        };
        
        if (this.config.enableDetailedLogging) {
            console.group('VectorBid Performance Report');
            console.table(this.getTopMetrics());
            console.log('Full Report:', report);
            console.groupEnd();
        }
        
        return report;
    }
    
    generateFinalReport() {
        const finalReport = this.generateReport();
        
        // Send to analytics if available
        if (window.gtag) {
            this.sendToGoogleAnalytics(finalReport);
        }
        
        // Store in session storage for debugging
        try {
            sessionStorage.setItem('vectorbid_performance_final', JSON.stringify(finalReport));
        } catch (error) {
            console.warn('Failed to store final performance report:', error);
        }
        
        return finalReport;
    }
    
    getSessionInfo() {
        return {
            userAgent: navigator.userAgent,
            url: window.location.href,
            referrer: document.referrer,
            timestamp: Date.now(),
            sessionDuration: performance.now(),
            deviceMemory: navigator.deviceMemory || 'unknown',
            hardwareConcurrency: navigator.hardwareConcurrency || 'unknown',
            connection: navigator.connection ? {
                effectiveType: navigator.connection.effectiveType,
                downlink: navigator.connection.downlink,
                rtt: navigator.connection.rtt
            } : 'unknown'
        };
    }
    
    getResourceSummary() {
        const summary = {
            totalResources: this.resourceCache.size,
            byType: {},
            totalSize: 0,
            totalLoadTime: 0
        };
        
        for (const [url, resource] of this.resourceCache) {
            if (!summary.byType[resource.type]) {
                summary.byType[resource.type] = { count: 0, size: 0, loadTime: 0 };
            }
            
            summary.byType[resource.type].count++;
            summary.byType[resource.type].size += resource.size;
            summary.byType[resource.type].loadTime += resource.loadTime;
            summary.totalSize += resource.size;
            summary.totalLoadTime += resource.loadTime;
        }
        
        return summary;
    }
    
    getPerformanceSummary() {
        const criticalMetrics = [
            'Navigation.Total_Load_Time',
            'Navigation.DOM_Interactive',
            'WebVitals.LCP',
            'WebVitals.FID',
            'WebVitals.CLS',
            'Memory.UsagePercent'
        ];
        
        const summary = {};
        criticalMetrics.forEach(metric => {
            const data = this.getMetricSummary(metric);
            if (data) {
                summary[metric] = data.latest || data.avg;
            }
        });
        
        return summary;
    }
    
    getTopMetrics() {
        const important = [
            'Navigation.Total_Load_Time',
            'WebVitals.LCP',
            'WebVitals.FID',
            'WebVitals.CLS',
            'Memory.UsagePercent',
            'Resource.TotalSize'
        ];
        
        const table = {};
        important.forEach(name => {
            const summary = this.getMetricSummary(name);
            if (summary) {
                table[name] = `${summary.latest?.toFixed(2) || 'N/A'} ${summary.unit}`;
            }
        });
        
        return table;
    }
    
    sendToGoogleAnalytics(report) {
        try {
            // Send core web vitals
            if (report.webVitals.LCP) {
                gtag('event', 'LCP', { value: Math.round(report.webVitals.LCP) });
            }
            if (report.webVitals.FID) {
                gtag('event', 'FID', { value: Math.round(report.webVitals.FID) });
            }
            if (report.webVitals.CLS) {
                gtag('event', 'CLS', { value: Math.round(report.webVitals.CLS * 1000) });
            }
            
            // Send custom metrics
            gtag('event', 'performance_report', {
                custom_parameter_1: report.navigation?.Total_Load_Time || 0,
                custom_parameter_2: report.resources?.totalSize || 0
            });
        } catch (error) {
            console.warn('Failed to send performance data to analytics:', error);
        }
    }
    
    logEvent(type, name, data = {}) {
        if (this.config.enableDetailedLogging) {
            console.debug(`[PERF] ${type}: ${name}`, data);
        }
        
        // Could be extended to send to external logging service
    }
    
    // Public API for manual performance tracking
    startTiming(name) {
        this.mark(`${name}-start`);
        return {
            end: () => this.measure(name, `${name}-start`)
        };
    }
    
    trackUserInteraction(action, element = null) {
        this.recordMetric(`Interaction.${action}`, 1, 'count');
        this.mark(`interaction-${action}`);
        
        if (element) {
            this.logEvent('USER_INTERACTION', action, {
                element: element.tagName,
                id: element.id,
                className: element.className
            });
        }
    }
    
    trackAPICall(url, duration, success = true) {
        this.recordMetric('API.CallDuration', duration, 'ms');
        this.recordMetric(`API.${success ? 'Success' : 'Failure'}`, 1, 'count');
        
        this.logEvent('API_CALL', url, { duration, success });
    }
    
    // Cleanup method
    destroy() {
        this.observers.forEach(observer => {
            try {
                observer.disconnect();
            } catch (error) {
                console.warn('Failed to disconnect performance observer:', error);
            }
        });
        
        this.observers = [];
        this.metrics.clear();
        this.marks.clear();
        this.measures.clear();
    }
}

// Initialize global performance monitor
window.PerformanceMonitor = new PerformanceMonitor();

// Auto-generate final report on page unload
window.addEventListener('beforeunload', () => {
    if (window.PerformanceMonitor) {
        window.PerformanceMonitor.generateFinalReport();
    }
});

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PerformanceMonitor;
}
