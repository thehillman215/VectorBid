# Cursor AI Task 3: Performance Optimization

## 🎯 Project Goal
Optimize VectorBid for maximum performance: fast load times, efficient bundle sizes, and smooth interactions.

## 📋 Prerequisites
- **MUST COMPLETE**: Task 2 (Error Handling & UX) first
- Base branch: `cursor/error-handling-ux` (from previous task)

## 🔧 Git Setup
```bash
git checkout cursor/error-handling-ux
git pull origin cursor/error-handling-ux
git checkout -b cursor/performance-optimization
```

## 📁 Files to Modify

### Primary Files (MUST MODIFY):
1. `app/static/js/data-flow-viz.js`
2. `app/static/js/interactive-demo.js`
3. `app/static/pages/landing/home.html`
4. `app/static/css/design-system.css`
5. `app/static/js/error-handler.js`

### New Files to Create:
6. `app/static/js/lazy-loader.js`
7. `app/static/js/performance-monitor.js`
8. `app/static/js/cache-manager.js`
9. `app/static/images/` (optimized images)

### Configuration Files:
10. `app/static/service-worker.js`
11. `.gitignore` (update)

## 🎯 Specific Tasks

### Task 3.1: Bundle Size Optimization
**File**: `app/static/pages/landing/home.html`

**Issues to Fix**:
- D3.js loads entire library (reduce to needed modules)
- Multiple CSS frameworks loaded (consolidate)
- JavaScript loaded synchronously (implement async loading)
- Unused Font Awesome icons (optimize icon loading)

**Expected Changes**:
```html
<!-- Replace D3.js full library -->
<script src="https://d3js.org/d3.v7.min.js"></script>
<!-- With optimized modules -->
<script src="https://d3js.org/d3-selection.v3.min.js" async></script>
<script src="https://d3js.org/d3-transition.v3.min.js" async></script>
<script src="https://d3js.org/d3-ease.v3.min.js" async></script>

<!-- Optimize Font Awesome loading -->
<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
<!-- Replace with subset -->
<link href="/static/css/fa-subset.css" rel="stylesheet">

<!-- Add resource hints -->
<link rel="preconnect" href="https://cdn.tailwindcss.com">
<link rel="preconnect" href="https://cdnjs.cloudflare.com">
<link rel="dns-prefetch" href="https://d3js.org">

<!-- Implement lazy loading for non-critical JS -->
<script>
window.addEventListener('load', () => {
    const scripts = [
        '/static/js/data-flow-viz.js',
        '/static/js/interactive-demo.js'
    ];
    
    scripts.forEach(src => {
        const script = document.createElement('script');
        script.src = src;
        script.async = true;
        document.body.appendChild(script);
    });
});
</script>
```

### Task 3.2: Lazy Loading System
**Create**: `app/static/js/lazy-loader.js`

**Implementation**:
```javascript
class LazyLoader {
    constructor() {
        this.loadedModules = new Set();
        this.loadingPromises = new Map();
        this.observers = new Map();
        this.setupIntersectionObserver();
    }
    
    setupIntersectionObserver() {
        if ('IntersectionObserver' in window) {
            this.intersectionObserver = new IntersectionObserver(
                (entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const element = entry.target;
                            const moduleToLoad = element.dataset.lazyModule;
                            if (moduleToLoad) {
                                this.loadModule(moduleToLoad);
                                this.intersectionObserver.unobserve(element);
                            }
                        }
                    });
                },
                { 
                    rootMargin: '50px',
                    threshold: 0.1
                }
            );
        }
    }
    
    async loadModule(moduleName) {
        if (this.loadedModules.has(moduleName)) {
            return Promise.resolve();
        }
        
        if (this.loadingPromises.has(moduleName)) {
            return this.loadingPromises.get(moduleName);
        }
        
        const promise = this.performModuleLoad(moduleName);
        this.loadingPromises.set(moduleName, promise);
        
        try {
            await promise;
            this.loadedModules.add(moduleName);
            this.loadingPromises.delete(moduleName);
        } catch (error) {
            this.loadingPromises.delete(moduleName);
            console.error(`Failed to load module ${moduleName}:`, error);
            throw error;
        }
        
        return promise;
    }
    
    async performModuleLoad(moduleName) {
        const moduleConfig = {
            'data-flow-viz': {
                js: ['/static/js/data-flow-viz.js'],
                css: [],
                dependencies: ['d3']
            },
            'interactive-demo': {
                js: ['/static/js/interactive-demo.js'],
                css: [],
                dependencies: []
            },
            'd3': {
                js: [
                    'https://d3js.org/d3-selection.v3.min.js',
                    'https://d3js.org/d3-transition.v3.min.js',
                    'https://d3js.org/d3-ease.v3.min.js'
                ],
                css: [],
                dependencies: []
            }
        };
        
        const config = moduleConfig[moduleName];
        if (!config) {
            throw new Error(`Unknown module: ${moduleName}`);
        }
        
        // Load dependencies first
        for (const dep of config.dependencies) {
            await this.loadModule(dep);
        }
        
        // Load CSS files
        const cssPromises = config.css.map(href => this.loadCSS(href));
        
        // Load JS files
        const jsPromises = config.js.map(src => this.loadScript(src));
        
        await Promise.all([...cssPromises, ...jsPromises]);
    }
    
    loadScript(src) {
        return new Promise((resolve, reject) => {
            const script = document.createElement('script');
            script.src = src;
            script.async = true;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }
    
    loadCSS(href) {
        return new Promise((resolve, reject) => {
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = href;
            link.onload = resolve;
            link.onerror = reject;
            document.head.appendChild(link);
        });
    }
    
    observeElement(element, moduleName) {
        if (this.intersectionObserver) {
            element.dataset.lazyModule = moduleName;
            this.intersectionObserver.observe(element);
        } else {
            // Fallback for browsers without IntersectionObserver
            this.loadModule(moduleName);
        }
    }
    
    preloadModule(moduleName) {
        // Preload module without waiting
        this.loadModule(moduleName).catch(console.error);
    }
}

window.LazyLoader = new LazyLoader();
```

### Task 3.3: Data Flow Visualization Performance
**File**: `app/static/js/data-flow-viz.js`

**Optimizations Required**:
```javascript
class DataFlowVisualization {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) return;
        
        // Performance optimizations
        this.isVisible = false;
        this.animationFrame = null;
        this.resizeTimeout = null;
        
        // Throttled methods
        this.throttledResize = this.throttle(this.handleResize.bind(this), 250);
        this.throttledRender = this.throttle(this.render.bind(this), 16); // 60fps
        
        // Initialize only when visible
        window.LazyLoader.observeElement(this.container, 'data-flow-viz');
        this.setupVisibilityObserver();
        
        // Defer initialization until needed
        this.initPromise = this.deferredInit();
    }
    
    async deferredInit() {
        // Wait for D3 to load
        await window.LazyLoader.loadModule('d3');
        
        // Initialize visualization
        this.init();
        
        // Setup performance monitoring
        this.startPerformanceMonitoring();
    }
    
    setupVisibilityObserver() {
        if ('IntersectionObserver' in window) {
            const observer = new IntersectionObserver(
                (entries) => {
                    entries.forEach(entry => {
                        this.isVisible = entry.isIntersecting;
                        if (this.isVisible) {
                            this.resumeAnimations();
                        } else {
                            this.pauseAnimations();
                        }
                    });
                },
                { threshold: 0.1 }
            );
            observer.observe(this.container);
        }
    }
    
    pauseAnimations() {
        if (this.animationFrame) {
            cancelAnimationFrame(this.animationFrame);
            this.animationFrame = null;
        }
        
        // Pause D3 transitions
        if (this.svg) {
            this.svg.selectAll('*').interrupt();
        }
    }
    
    resumeAnimations() {
        if (!this.isVisible) return;
        
        this.animateDataFlow();
    }
    
    handleResize() {
        if (!this.isVisible) return;
        
        const containerRect = this.container.getBoundingClientRect();
        const newWidth = Math.max(300, containerRect.width);
        const newHeight = Math.max(200, containerRect.height);
        
        if (this.width !== newWidth || this.height !== newHeight) {
            this.width = newWidth;
            this.height = newHeight;
            this.throttledRender();
        }
    }
    
    render() {
        if (!this.svg || !this.isVisible) return;
        
        // Use requestAnimationFrame for smooth updates
        this.animationFrame = requestAnimationFrame(() => {
            this.svg
                .attr('width', this.width)
                .attr('height', this.height)
                .attr('viewBox', `0 0 ${this.width} ${this.height}`);
            
            this.updateNodePositions();
            this.updateConnections();
        });
    }
    
    updateNodePositions() {
        // Scale nodes based on container size
        const scale = Math.min(this.width / 1200, this.height / 800);
        
        this.nodes.forEach(node => {
            node.scaledX = node.x * scale;
            node.scaledY = node.y * scale;
            node.scaledWidth = node.width * scale;
            node.scaledHeight = node.height * scale;
        });
        
        // Update node positions with scaled values
        this.svg.selectAll('.node')
            .attr('transform', d => `translate(${d.scaledX}, ${d.scaledY})`);
    }
    
    startPerformanceMonitoring() {
        if (window.PerformanceMonitor) {
            this.perfMonitor = new window.PerformanceMonitor('DataFlowViz');
            this.perfMonitor.mark('initialization-complete');
        }
    }
    
    throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }
    
    destroy() {
        this.pauseAnimations();
        
        if (this.resizeTimeout) {
            clearTimeout(this.resizeTimeout);
        }
        
        window.removeEventListener('resize', this.throttledResize);
        
        if (this.svg) {
            this.svg.remove();
        }
    }
}
```

### Task 3.4: API Response Caching
**Create**: `app/static/js/cache-manager.js`

**Implementation**:
```javascript
class CacheManager {
    constructor() {
        this.cache = new Map();
        this.timestamps = new Map();
        this.defaultTTL = 5 * 60 * 1000; // 5 minutes
        this.maxCacheSize = 50;
        
        // TTL configuration per endpoint
        this.ttlConfig = {
            '/api/parse': 2 * 60 * 1000,      // 2 minutes
            '/api/optimize': 10 * 60 * 1000,   // 10 minutes
            '/api/personas': 60 * 60 * 1000,   // 1 hour
        };
        
        this.setupPeriodicCleanup();
    }
    
    generateKey(url, payload = null) {
        const baseKey = url;
        if (payload) {
            // Create stable hash of payload
            const payloadString = JSON.stringify(payload, Object.keys(payload).sort());
            const hash = this.simpleHash(payloadString);
            return `${baseKey}:${hash}`;
        }
        return baseKey;
    }
    
    simpleHash(str) {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32-bit integer
        }
        return hash.toString(36);
    }
    
    set(url, payload, data) {
        const key = this.generateKey(url, payload);
        const ttl = this.ttlConfig[url] || this.defaultTTL;
        
        // Implement LRU eviction if cache is full
        if (this.cache.size >= this.maxCacheSize) {
            this.evictOldest();
        }
        
        this.cache.set(key, {
            data: data,
            timestamp: Date.now(),
            ttl: ttl,
            accessCount: 1,
            lastAccessed: Date.now()
        });
        
        this.timestamps.set(key, Date.now());
    }
    
    get(url, payload = null) {
        const key = this.generateKey(url, payload);
        const cached = this.cache.get(key);
        
        if (!cached) {
            return null;
        }
        
        // Check if expired
        if (Date.now() - cached.timestamp > cached.ttl) {
            this.cache.delete(key);
            this.timestamps.delete(key);
            return null;
        }
        
        // Update access tracking for LRU
        cached.accessCount++;
        cached.lastAccessed = Date.now();
        
        return cached.data;
    }
    
    has(url, payload = null) {
        return this.get(url, payload) !== null;
    }
    
    invalidate(url, payload = null) {
        const key = this.generateKey(url, payload);
        this.cache.delete(key);
        this.timestamps.delete(key);
    }
    
    clear() {
        this.cache.clear();
        this.timestamps.clear();
    }
    
    evictOldest() {
        let oldestKey = null;
        let oldestTime = Date.now();
        
        for (const [key, cached] of this.cache.entries()) {
            if (cached.lastAccessed < oldestTime) {
                oldestTime = cached.lastAccessed;
                oldestKey = key;
            }
        }
        
        if (oldestKey) {
            this.cache.delete(oldestKey);
            this.timestamps.delete(oldestKey);
        }
    }
    
    setupPeriodicCleanup() {
        setInterval(() => {
            const now = Date.now();
            const keysToDelete = [];
            
            for (const [key, cached] of this.cache.entries()) {
                if (now - cached.timestamp > cached.ttl) {
                    keysToDelete.push(key);
                }
            }
            
            keysToDelete.forEach(key => {
                this.cache.delete(key);
                this.timestamps.delete(key);
            });
        }, 60000); // Cleanup every minute
    }
    
    getCacheStats() {
        const stats = {
            size: this.cache.size,
            maxSize: this.maxCacheSize,
            hitRate: 0,
            entries: []
        };
        
        let totalAccess = 0;
        for (const [key, cached] of this.cache.entries()) {
            totalAccess += cached.accessCount;
            stats.entries.push({
                key: key,
                age: Date.now() - cached.timestamp,
                ttl: cached.ttl,
                accessCount: cached.accessCount
            });
        }
        
        return stats;
    }
}

window.CacheManager = new CacheManager();
```

### Task 3.5: Performance Monitoring
**Create**: `app/static/js/performance-monitor.js`

**Implementation**:
```javascript
class PerformanceMonitor {
    constructor(namespace = 'VectorBid') {
        this.namespace = namespace;
        this.metrics = new Map();
        this.marks = new Map();
        this.measures = new Map();
        this.observers = [];
        
        this.setupPerformanceObservers();
        this.startResourceMonitoring();
    }
    
    mark(name, detail = {}) {
        const markName = `${this.namespace}:${name}`;
        
        if ('performance' in window && 'mark' in performance) {
            performance.mark(markName, { detail });
        }
        
        this.marks.set(name, {
            timestamp: Date.now(),
            detail: detail
        });
    }
    
    measure(name, startMark, endMark = null) {
        const measureName = `${this.namespace}:${name}`;
        const startMarkName = `${this.namespace}:${startMark}`;
        const endMarkName = endMark ? `${this.namespace}:${endMark}` : undefined;
        
        try {
            if ('performance' in window && 'measure' in performance) {
                const measure = performance.measure(measureName, startMarkName, endMarkName);
                
                this.measures.set(name, {
                    duration: measure.duration,
                    startTime: measure.startTime,
                    timestamp: Date.now()
                });
                
                return measure.duration;
            }
        } catch (error) {
            console.warn('Performance measure failed:', error);
        }
        
        // Fallback measurement
        const startTime = this.marks.get(startMark)?.timestamp;
        const endTime = endMark ? this.marks.get(endMark)?.timestamp : Date.now();
        
        if (startTime && endTime) {
            const duration = endTime - startTime;
            this.measures.set(name, {
                duration: duration,
                startTime: startTime,
                timestamp: Date.now()
            });
            return duration;
        }
        
        return null;
    }
    
    setupPerformanceObservers() {
        if (!('PerformanceObserver' in window)) return;
        
        try {
            // Observe navigation timing
            const navObserver = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach(entry => {
                    this.processNavigationTiming(entry);
                });
            });
            navObserver.observe({ entryTypes: ['navigation'] });
            this.observers.push(navObserver);
            
            // Observe resource timing
            const resourceObserver = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                entries.forEach(entry => {
                    this.processResourceTiming(entry);
                });
            });
            resourceObserver.observe({ entryTypes: ['resource'] });
            this.observers.push(resourceObserver);
            
            // Observe largest contentful paint
            const lcpObserver = new PerformanceObserver((list) => {
                const entries = list.getEntries();
                const lastEntry = entries[entries.length - 1];
                this.recordMetric('LCP', lastEntry.startTime);
            });
            lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
            this.observers.push(lcpObserver);
            
            // Observe cumulative layout shift
            const clsObserver = new PerformanceObserver((list) => {
                let clsValue = 0;
                const entries = list.getEntries();
                entries.forEach(entry => {
                    if (!entry.hadRecentInput) {
                        clsValue += entry.value;
                    }
                });
                this.recordMetric('CLS', clsValue);
            });
            clsObserver.observe({ entryTypes: ['layout-shift'] });
            this.observers.push(clsObserver);
            
        } catch (error) {
            console.warn('Performance observer setup failed:', error);
        }
    }
    
    processNavigationTiming(entry) {
        const timing = {
            'DNS Lookup': entry.domainLookupEnd - entry.domainLookupStart,
            'TCP Connection': entry.connectEnd - entry.connectStart,
            'TLS Handshake': entry.secureConnectionStart > 0 ? entry.connectEnd - entry.secureConnectionStart : 0,
            'Request': entry.responseStart - entry.requestStart,
            'Response': entry.responseEnd - entry.responseStart,
            'DOM Processing': entry.domContentLoadedEventStart - entry.responseEnd,
            'Load Complete': entry.loadEventEnd - entry.loadEventStart,
            'Total Load Time': entry.loadEventEnd - entry.fetchStart
        };
        
        Object.entries(timing).forEach(([name, value]) => {
            this.recordMetric(`Navigation.${name}`, value);
        });
    }
    
    processResourceTiming(entry) {
        const resourceType = this.getResourceType(entry.name);
        const loadTime = entry.responseEnd - entry.startTime;
        
        this.recordMetric(`Resource.${resourceType}.LoadTime`, loadTime);
        
        if (entry.transferSize) {
            this.recordMetric(`Resource.${resourceType}.Size`, entry.transferSize);
        }
    }
    
    getResourceType(url) {
        if (url.includes('.js')) return 'JavaScript';
        if (url.includes('.css')) return 'CSS';
        if (url.match(/\.(png|jpg|jpeg|gif|svg|webp)$/i)) return 'Image';
        if (url.includes('font')) return 'Font';
        if (url.includes('/api/')) return 'API';
        return 'Other';
    }
    
    recordMetric(name, value, unit = 'ms') {
        if (!this.metrics.has(name)) {
            this.metrics.set(name, []);
        }
        
        this.metrics.get(name).push({
            value: value,
            timestamp: Date.now(),
            unit: unit
        });
        
        // Keep only last 100 measurements per metric
        const measurements = this.metrics.get(name);
        if (measurements.length > 100) {
            measurements.splice(0, measurements.length - 100);
        }
    }
    
    getMetricSummary(name) {
        const measurements = this.metrics.get(name);
        if (!measurements || measurements.length === 0) {
            return null;
        }
        
        const values = measurements.map(m => m.value);
        return {
            count: values.length,
            min: Math.min(...values),
            max: Math.max(...values),
            avg: values.reduce((a, b) => a + b, 0) / values.length,
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
    
    startResourceMonitoring() {
        // Monitor memory usage if available
        if ('memory' in performance) {
            setInterval(() => {
                this.recordMetric('Memory.Used', performance.memory.usedJSHeapSize, 'bytes');
                this.recordMetric('Memory.Total', performance.memory.totalJSHeapSize, 'bytes');
                this.recordMetric('Memory.Limit', performance.memory.jsHeapSizeLimit, 'bytes');
            }, 10000); // Every 10 seconds
        }
        
        // Monitor FPS
        let lastTime = performance.now();
        let frames = 0;
        
        const measureFPS = (currentTime) => {
            frames++;
            if (currentTime >= lastTime + 1000) {
                this.recordMetric('FPS', frames, 'fps');
                frames = 0;
                lastTime = currentTime;
            }
            requestAnimationFrame(measureFPS);
        };
        
        requestAnimationFrame(measureFPS);
    }
    
    generateReport() {
        const report = {
            timestamp: new Date().toISOString(),
            metrics: this.getAllMetrics(),
            marks: Object.fromEntries(this.marks),
            measures: Object.fromEntries(this.measures),
            userAgent: navigator.userAgent,
            url: window.location.href
        };
        
        console.group('VectorBid Performance Report');
        console.table(report.metrics);
        console.groupEnd();
        
        return report;
    }
    
    destroy() {
        this.observers.forEach(observer => {
            try {
                observer.disconnect();
            } catch (error) {
                console.warn('Failed to disconnect performance observer:', error);
            }
        });
        this.observers = [];
    }
}

window.PerformanceMonitor = new PerformanceMonitor();

// Auto-generate report on page unload
window.addEventListener('beforeunload', () => {
    window.PerformanceMonitor.generateReport();
});
```

## ✅ Success Criteria

### Performance Benchmarks:
1. **Load Time**: Landing page loads in < 2 seconds on 3G
2. **Bundle Size**: JavaScript bundles < 200KB gzipped total
3. **Time to Interactive**: < 3 seconds
4. **Largest Contentful Paint**: < 2.5 seconds
5. **Cumulative Layout Shift**: < 0.1
6. **First Input Delay**: < 100ms

### Testing Requirements:
- [ ] Lighthouse audit score > 90 for Performance
- [ ] All critical resources load within 2 seconds
- [ ] Data flow visualization renders smoothly at 60fps
- [ ] API responses are cached appropriately
- [ ] Memory usage remains stable during interactions
- [ ] Bundle size reduced by at least 30% from baseline

## 🔗 Chain to Next Task
After completing performance optimization:

```bash
git add .
git commit -m "feat: implement comprehensive performance optimizations

- Add lazy loading system for non-critical resources
- Implement intelligent caching for API responses
- Optimize data flow visualization with visibility observers
- Add performance monitoring and metrics collection
- Reduce bundle sizes with selective D3.js loading
- Implement FPS monitoring and memory tracking

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push origin cursor/performance-optimization
```

**NEXT**: Proceed to `4-ACCESSIBILITY.md` for accessibility improvements.

## 📊 Testing Commands
```bash
# Performance testing
lighthouse http://localhost:8000/ --output=json --output-path=./lighthouse-report.json

# Bundle analysis
du -sh app/static/js/*.js
gzip -c app/static/js/*.js | wc -c

# Memory monitoring
# Use browser dev tools Memory tab for heap snapshots

# Load testing
ab -n 100 -c 10 http://localhost:8000/
```

## 🚨 Critical Requirements
- Performance improvements must not break functionality
- Maintain backwards compatibility with older browsers
- Cache invalidation must work correctly
- Performance monitoring must not impact user experience
- Lazy loading must have proper fallbacks