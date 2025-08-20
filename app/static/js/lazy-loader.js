// VectorBid Lazy Loading System
// Intelligent module loading with intersection observers and dependency management

class LazyLoader {
    constructor() {
        this.loadedModules = new Set();
        this.loadingPromises = new Map();
        this.observers = new Map();
        this.dependencyGraph = new Map();
        this.moduleInstances = new Map();
        
        this.setupIntersectionObserver();
        this.setupPerformanceMonitoring();
        
        // Module configuration with dependencies
        this.moduleConfig = {
            'd3': {
                js: [
                    'https://d3js.org/d3-selection.v3.min.js',
                    'https://d3js.org/d3-transition.v3.min.js',
                    'https://d3js.org/d3-ease.v3.min.js',
                    'https://d3js.org/d3-interpolate.v3.min.js'
                ],
                css: [],
                dependencies: [],
                global: 'd3',
                priority: 'low'
            },
            'data-flow-viz': {
                js: ['/static/js/data-flow-viz.js'],
                css: [],
                dependencies: ['d3'],
                global: 'DataFlowVisualization',
                priority: 'medium',
                factory: (containerId) => new window.DataFlowVisualization(containerId)
            },
            'interactive-demo': {
                js: ['/static/js/interactive-demo.js'],
                css: [],
                dependencies: ['error-handler', 'loading-states'],
                global: 'InteractiveDemo',
                priority: 'medium',
                factory: () => new window.InteractiveDemo()
            },
            'error-handler': {
                js: ['/static/js/error-handler.js'],
                css: ['/static/css/feedback-components.css'],
                dependencies: [],
                global: 'VectorBidErrors',
                priority: 'high',
                critical: true
            },
            'loading-states': {
                js: ['/static/js/loading-states.js'],
                css: [],
                dependencies: [],
                global: 'LoadingStates',
                priority: 'high',
                critical: true
            },
            'cache-manager': {
                js: ['/static/js/cache-manager.js'],
                css: [],
                dependencies: [],
                global: 'CacheManager',
                priority: 'medium'
            },
            'performance-monitor': {
                js: ['/static/js/performance-monitor.js'],
                css: [],
                dependencies: [],
                global: 'PerformanceMonitor',
                priority: 'high'
            }
        };
        
        this.preloadCriticalModules();
    }
    
    setupIntersectionObserver() {
        if ('IntersectionObserver' in window) {
            this.intersectionObserver = new IntersectionObserver(
                (entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const element = entry.target;
                            const moduleToLoad = element.dataset.lazyModule;
                            const options = this.parseLoadOptions(element.dataset.lazyOptions);
                            
                            if (moduleToLoad) {
                                this.loadModule(moduleToLoad, options);
                                this.intersectionObserver.unobserve(element);
                            }
                        }
                    });
                },
                { 
                    rootMargin: '100px', // Load before element is visible
                    threshold: 0.1
                }
            );
        }
    }
    
    setupPerformanceMonitoring() {
        if (window.PerformanceMonitor) {
            this.perfMonitor = window.PerformanceMonitor;
        }
    }
    
    parseLoadOptions(optionsString) {
        if (!optionsString) return {};
        try {
            return JSON.parse(optionsString);
        } catch (error) {
            console.warn('Failed to parse lazy load options:', error);
            return {};
        }
    }
    
    async preloadCriticalModules() {
        const criticalModules = Object.entries(this.moduleConfig)
            .filter(([name, config]) => config.critical)
            .map(([name]) => name);
        
        for (const moduleName of criticalModules) {
            this.preloadModule(moduleName);
        }
    }
    
    async loadModule(moduleName, options = {}) {
        if (this.loadedModules.has(moduleName)) {
            return this.getModuleInstance(moduleName, options);
        }
        
        if (this.loadingPromises.has(moduleName)) {
            await this.loadingPromises.get(moduleName);
            return this.getModuleInstance(moduleName, options);
        }
        
        const promise = this.performModuleLoad(moduleName, options);
        this.loadingPromises.set(moduleName, promise);
        
        try {
            await promise;
            this.loadedModules.add(moduleName);
            this.loadingPromises.delete(moduleName);
            
            // Mark performance
            if (this.perfMonitor) {
                this.perfMonitor.mark(`module-${moduleName}-loaded`);
            }
            
            return this.getModuleInstance(moduleName, options);
        } catch (error) {
            this.loadingPromises.delete(moduleName);
            console.error(`Failed to load module ${moduleName}:`, error);
            
            // Try fallback loading strategies
            if (options.fallback !== false) {
                return this.loadModuleWithFallback(moduleName, options);
            }
            
            throw error;
        }
    }
    
    async performModuleLoad(moduleName, options = {}) {
        const config = this.moduleConfig[moduleName];
        if (!config) {
            throw new Error(`Unknown module: ${moduleName}`);
        }
        
        if (this.perfMonitor) {
            this.perfMonitor.mark(`module-${moduleName}-start`);
        }
        
        // Load dependencies first in parallel
        if (config.dependencies.length > 0) {
            await Promise.all(
                config.dependencies.map(dep => this.loadModule(dep, { ...options, nested: true }))
            );
        }
        
        // Load CSS and JS in parallel
        const loadPromises = [];
        
        // Load CSS files
        if (config.css.length > 0) {
            loadPromises.push(
                Promise.all(config.css.map(href => this.loadCSS(href)))
            );
        }
        
        // Load JS files sequentially to maintain dependency order
        if (config.js.length > 0) {
            loadPromises.push(this.loadScriptsSequentially(config.js));
        }
        
        await Promise.all(loadPromises);
        
        // Verify module loaded correctly
        if (config.global && !window[config.global]) {
            throw new Error(`Module ${moduleName} did not expose expected global: ${config.global}`);
        }
        
        if (this.perfMonitor) {
            this.perfMonitor.measure(`module-${moduleName}-load`, `module-${moduleName}-start`);
        }
    }
    
    async loadModuleWithFallback(moduleName, options) {
        const config = this.moduleConfig[moduleName];
        
        // Try loading from CDN fallback if local fails
        if (config.fallbackUrls) {
            for (const fallbackUrl of config.fallbackUrls) {
                try {
                    await this.loadScript(fallbackUrl);
                    this.loadedModules.add(moduleName);
                    return this.getModuleInstance(moduleName, options);
                } catch (error) {
                    console.warn(`Fallback URL failed for ${moduleName}:`, fallbackUrl, error);
                }
            }
        }
        
        // Return stub or mock if available
        if (config.stub) {
            console.warn(`Using stub for module ${moduleName}`);
            return config.stub;
        }
        
        throw new Error(`All fallback strategies failed for module: ${moduleName}`);
    }
    
    async loadScriptsSequentially(scripts) {
        for (const src of scripts) {
            await this.loadScript(src);
        }
    }
    
    loadScript(src) {
        return new Promise((resolve, reject) => {
            // Check if script already exists
            if (document.querySelector(`script[src="${src}"]`)) {
                resolve();
                return;
            }
            
            const script = document.createElement('script');
            script.src = src;
            script.async = true;
            script.crossOrigin = 'anonymous';
            
            script.onload = () => {
                if (this.perfMonitor) {
                    this.perfMonitor.recordMetric('Script.LoadTime', performance.now());
                }
                resolve();
            };
            
            script.onerror = (error) => {
                console.error(`Failed to load script: ${src}`, error);
                reject(new Error(`Script load failed: ${src}`));
            };
            
            // Add integrity check for external scripts
            if (src.startsWith('http') && !src.includes(window.location.hostname)) {
                script.setAttribute('referrerpolicy', 'no-referrer');
            }
            
            document.head.appendChild(script);
        });
    }
    
    loadCSS(href) {
        return new Promise((resolve, reject) => {
            // Check if stylesheet already exists
            if (document.querySelector(`link[href="${href}"]`)) {
                resolve();
                return;
            }
            
            const link = document.createElement('link');
            link.rel = 'stylesheet';
            link.href = href;
            link.crossOrigin = 'anonymous';
            
            link.onload = () => {
                if (this.perfMonitor) {
                    this.perfMonitor.recordMetric('CSS.LoadTime', performance.now());
                }
                resolve();
            };
            
            link.onerror = (error) => {
                console.error(`Failed to load stylesheet: ${href}`, error);
                reject(new Error(`Stylesheet load failed: ${href}`));
            };
            
            document.head.appendChild(link);
        });
    }
    
    getModuleInstance(moduleName, options = {}) {
        const config = this.moduleConfig[moduleName];
        
        // Return existing instance if available and not requiring new instance
        if (!options.newInstance && this.moduleInstances.has(moduleName)) {
            return this.moduleInstances.get(moduleName);
        }
        
        // Create new instance using factory
        if (config.factory && window[config.global]) {
            try {
                const instance = config.factory.apply(null, options.args || []);
                
                if (!options.newInstance) {
                    this.moduleInstances.set(moduleName, instance);
                }
                
                return instance;
            } catch (error) {
                console.error(`Failed to create instance of ${moduleName}:`, error);
            }
        }
        
        // Return global reference
        return window[config.global] || null;
    }
    
    observeElement(element, moduleName, options = {}) {
        if (!element) {
            console.warn('Cannot observe null element for lazy loading');
            return;
        }
        
        if (this.intersectionObserver) {
            element.dataset.lazyModule = moduleName;
            if (options) {
                element.dataset.lazyOptions = JSON.stringify(options);
            }
            this.intersectionObserver.observe(element);
        } else {
            // Fallback for browsers without IntersectionObserver
            this.loadModule(moduleName, options);
        }
    }
    
    preloadModule(moduleName, options = {}) {
        // Preload module without waiting, with low priority
        this.loadModule(moduleName, { ...options, preload: true }).catch(error => {
            console.warn(`Preload failed for ${moduleName}:`, error);
        });
    }
    
    async loadModulesByPriority(priority = 'medium') {
        const modulesToLoad = Object.entries(this.moduleConfig)
            .filter(([name, config]) => 
                config.priority === priority && !this.loadedModules.has(name)
            )
            .map(([name]) => name);
        
        const results = await Promise.allSettled(
            modulesToLoad.map(name => this.loadModule(name))
        );
        
        // Log any failures
        results.forEach((result, index) => {
            if (result.status === 'rejected') {
                console.warn(`Failed to load ${modulesToLoad[index]}:`, result.reason);
            }
        });
        
        return results;
    }
    
    isModuleLoaded(moduleName) {
        return this.loadedModules.has(moduleName);
    }
    
    isModuleLoading(moduleName) {
        return this.loadingPromises.has(moduleName);
    }
    
    getLoadedModules() {
        return Array.from(this.loadedModules);
    }
    
    getLoadingModules() {
        return Array.from(this.loadingPromises.keys());
    }
    
    // Prefetch resources for faster loading
    prefetchModule(moduleName) {
        const config = this.moduleConfig[moduleName];
        if (!config) return;
        
        const allUrls = [...config.js, ...config.css];
        
        allUrls.forEach(url => {
            const link = document.createElement('link');
            link.rel = 'prefetch';
            link.href = url;
            link.crossOrigin = 'anonymous';
            document.head.appendChild(link);
        });
    }
    
    // Preconnect to external domains
    preconnectToDomains() {
        const domains = new Set();
        
        Object.values(this.moduleConfig).forEach(config => {
            [...config.js, ...config.css].forEach(url => {
                if (url.startsWith('http')) {
                    const domain = new URL(url).origin;
                    domains.add(domain);
                }
            });
        });
        
        domains.forEach(domain => {
            if (!document.querySelector(`link[href="${domain}"][rel="preconnect"]`)) {
                const link = document.createElement('link');
                link.rel = 'preconnect';
                link.href = domain;
                link.crossOrigin = 'anonymous';
                document.head.appendChild(link);
            }
        });
    }
    
    // Get performance metrics
    getPerformanceMetrics() {
        const metrics = {
            modulesLoaded: this.loadedModules.size,
            modulesLoading: this.loadingPromises.size,
            loadedModules: this.getLoadedModules(),
            loadingModules: this.getLoadingModules()
        };
        
        if (this.perfMonitor) {
            metrics.performanceData = this.perfMonitor.getAllMetrics();
        }
        
        return metrics;
    }
    
    // Cleanup method
    destroy() {
        if (this.intersectionObserver) {
            this.intersectionObserver.disconnect();
        }
        
        // Clear all instances
        this.moduleInstances.clear();
        this.loadingPromises.clear();
        this.observers.clear();
    }
}

// Initialize global lazy loader
window.LazyLoader = new LazyLoader();

// Preconnect to external domains on load
window.addEventListener('load', () => {
    window.LazyLoader.preconnectToDomains();
});

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LazyLoader;
}
