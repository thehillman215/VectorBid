// VectorBid Cache Manager
// Intelligent API response caching with TTL, LRU eviction, and storage management

class CacheManager {
    constructor() {
        this.cache = new Map();
        this.timestamps = new Map();
        this.accessCounts = new Map();
        this.defaultTTL = 5 * 60 * 1000; // 5 minutes
        this.maxCacheSize = 100;
        this.maxMemorySize = 10 * 1024 * 1024; // 10MB
        this.currentMemorySize = 0;
        
        // TTL configuration per endpoint pattern
        this.ttlConfig = {
            '/api/parse': 2 * 60 * 1000,      // 2 minutes - user input changes frequently
            '/api/optimize': 10 * 60 * 1000,   // 10 minutes - optimization is expensive
            '/api/validate': 5 * 60 * 1000,    // 5 minutes - validation rules don't change often
            '/api/personas': 60 * 60 * 1000,   // 1 hour - personas are relatively static
            '/api/airlines': 24 * 60 * 60 * 1000, // 24 hours - airline data rarely changes
            '/api/bases': 24 * 60 * 60 * 1000,    // 24 hours - base data rarely changes
            '/static/': 24 * 60 * 60 * 1000,      // 24 hours - static resources
        };
        
        // Cache priority levels
        this.priorityLevels = {
            critical: 4,   // Never evict unless expired
            high: 3,       // Evict only when necessary
            medium: 2,     // Standard caching
            low: 1         // Evict first when space needed
        };
        
        this.setupPeriodicCleanup();
        this.setupStorageMonitoring();
        this.initializeFromStorage();
    }
    
    generateKey(url, payload = null, options = {}) {
        let baseKey = this.normalizeUrl(url);
        
        if (payload) {
            // Create stable hash of payload, excluding timestamp fields
            const cleanPayload = this.cleanPayloadForCaching(payload);
            const payloadString = JSON.stringify(cleanPayload, Object.keys(cleanPayload).sort());
            const hash = this.fastHash(payloadString);
            baseKey = `${baseKey}:${hash}`;
        }
        
        // Add user context if available
        const userContext = this.getUserContext();
        if (userContext) {
            baseKey = `${userContext}:${baseKey}`;
        }
        
        return baseKey;
    }
    
    normalizeUrl(url) {
        // Remove query parameters and normalize URL
        try {
            const urlObj = new URL(url, window.location.origin);
            return urlObj.pathname;
        } catch (error) {
            return url.split('?')[0];
        }
    }
    
    cleanPayloadForCaching(payload) {
        const cleaned = { ...payload };
        
        // Remove timestamp fields that shouldn't affect caching
        delete cleaned.timestamp;
        delete cleaned.requestId;
        delete cleaned.sessionId;
        delete cleaned._cache_timestamp;
        
        // Sort arrays for consistent hashing
        Object.keys(cleaned).forEach(key => {
            if (Array.isArray(cleaned[key])) {
                cleaned[key] = [...cleaned[key]].sort();
            }
        });
        
        return cleaned;
    }
    
    fastHash(str) {
        let hash = 0;
        if (str.length === 0) return hash;
        
        for (let i = 0; i < str.length; i++) {
            const char = str.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32-bit integer
        }
        
        return Math.abs(hash).toString(36);
    }
    
    getUserContext() {
        // Get user context for cache isolation
        try {
            const user = localStorage.getItem('vectorbid_user');
            if (user) {
                const userData = JSON.parse(user);
                return `${userData.airline || 'unknown'}:${userData.base || 'unknown'}`;
            }
        } catch (error) {
            console.warn('Failed to get user context for caching:', error);
        }
        return null;
    }
    
    getTTL(url) {
        // Find matching TTL configuration
        for (const [pattern, ttl] of Object.entries(this.ttlConfig)) {
            if (url.includes(pattern)) {
                return ttl;
            }
        }
        return this.defaultTTL;
    }
    
    estimateSize(data) {
        // Rough estimation of data size in bytes
        try {
            return new Blob([JSON.stringify(data)]).size;
        } catch (error) {
            // Fallback estimation
            return JSON.stringify(data).length * 2; // Approximate Unicode overhead
        }
    }
    
    set(url, payload, data, options = {}) {
        const key = this.generateKey(url, payload, options);
        const ttl = options.ttl || this.getTTL(url);
        const priority = options.priority || 'medium';
        const size = this.estimateSize(data);
        
        // Check if we need to make space
        if (this.cache.size >= this.maxCacheSize || this.currentMemorySize + size > this.maxMemorySize) {
            this.evictLeastUseful(size);
        }
        
        const cacheEntry = {
            data: data,
            timestamp: Date.now(),
            ttl: ttl,
            priority: this.priorityLevels[priority] || this.priorityLevels.medium,
            accessCount: 1,
            lastAccessed: Date.now(),
            size: size,
            url: url,
            compressed: false
        };
        
        // Compress large entries
        if (size > 50 * 1024) { // 50KB threshold
            try {
                cacheEntry.data = this.compressData(data);
                cacheEntry.compressed = true;
                cacheEntry.size = this.estimateSize(cacheEntry.data);
            } catch (error) {
                console.warn('Failed to compress cache entry:', error);
            }
        }
        
        this.cache.set(key, cacheEntry);
        this.timestamps.set(key, Date.now());
        this.accessCounts.set(key, 1);
        this.currentMemorySize += cacheEntry.size;
        
        // Persist critical entries to storage
        if (priority === 'critical' || priority === 'high') {
            this.persistToStorage(key, cacheEntry);
        }
        
        this.logCacheOperation('SET', key, size);
    }
    
    get(url, payload = null, options = {}) {
        const key = this.generateKey(url, payload, options);
        const cached = this.cache.get(key);
        
        if (!cached) {
            this.logCacheOperation('MISS', key);
            return null;
        }
        
        // Check if expired
        if (Date.now() - cached.timestamp > cached.ttl) {
            this.delete(key);
            this.logCacheOperation('EXPIRED', key);
            return null;
        }
        
        // Update access tracking for LRU
        cached.accessCount++;
        cached.lastAccessed = Date.now();
        this.accessCounts.set(key, cached.accessCount);
        
        this.logCacheOperation('HIT', key);
        
        // Decompress if needed
        if (cached.compressed) {
            try {
                return this.decompressData(cached.data);
            } catch (error) {
                console.error('Failed to decompress cache entry:', error);
                this.delete(key);
                return null;
            }
        }
        
        return cached.data;
    }
    
    has(url, payload = null, options = {}) {
        return this.get(url, payload, options) !== null;
    }
    
    delete(key) {
        const cached = this.cache.get(key);
        if (cached) {
            this.currentMemorySize -= cached.size;
            this.cache.delete(key);
            this.timestamps.delete(key);
            this.accessCounts.delete(key);
            this.removeFromStorage(key);
        }
    }
    
    invalidate(url, payload = null, options = {}) {
        const key = this.generateKey(url, payload, options);
        this.delete(key);
    }
    
    invalidatePattern(pattern) {
        const keysToDelete = [];
        
        for (const [key, cached] of this.cache.entries()) {
            if (cached.url.includes(pattern)) {
                keysToDelete.push(key);
            }
        }
        
        keysToDelete.forEach(key => this.delete(key));
        
        return keysToDelete.length;
    }
    
    clear() {
        this.cache.clear();
        this.timestamps.clear();
        this.accessCounts.clear();
        this.currentMemorySize = 0;
        this.clearStorage();
    }
    
    evictLeastUseful(sizeNeeded = 0) {
        const entries = Array.from(this.cache.entries());
        
        // Sort by usefulness score (lower is less useful)
        entries.sort(([keyA, cacheA], [keyB, cacheB]) => {
            const scoreA = this.calculateUsefulnessScore(cacheA);
            const scoreB = this.calculateUsefulnessScore(cacheB);
            return scoreA - scoreB;
        });
        
        let freedSpace = 0;
        let evictedCount = 0;
        
        for (const [key, cached] of entries) {
            // Don't evict critical entries unless expired
            if (cached.priority >= this.priorityLevels.critical) {
                const isExpired = Date.now() - cached.timestamp > cached.ttl;
                if (!isExpired) continue;
            }
            
            this.delete(key);
            freedSpace += cached.size;
            evictedCount++;
            
            // Stop if we've freed enough space or reached reasonable eviction limit
            if (freedSpace >= sizeNeeded && evictedCount >= 5) {
                break;
            }
            
            // Don't evict more than half the cache at once
            if (evictedCount >= this.cache.size / 2) {
                break;
            }
        }
        
        this.logCacheOperation('EVICT', null, null, { count: evictedCount, freed: freedSpace });
    }
    
    calculateUsefulnessScore(cached) {
        const now = Date.now();
        const age = now - cached.timestamp;
        const timeSinceAccess = now - cached.lastAccessed;
        const ageRatio = age / cached.ttl;
        
        // Lower score = less useful = evict first
        let score = cached.priority * 1000; // Base score from priority
        score += cached.accessCount * 10; // Frequently accessed items get higher score
        score -= ageRatio * 500; // Older items get lower score
        score -= (timeSinceAccess / 60000) * 50; // Recently accessed items get higher score
        score -= cached.size / 1024; // Larger items get slightly lower score
        
        return score;
    }
    
    compressData(data) {
        // Simple compression using JSON string manipulation
        // In a real implementation, you might use a compression library
        const jsonString = JSON.stringify(data);
        
        // Remove unnecessary whitespace and normalize formatting
        return jsonString
            .replace(/\s+/g, ' ')
            .replace(/\s*([{}[\],:])\s*/g, '$1');
    }
    
    decompressData(compressedData) {
        // Simple decompression - just parse the JSON
        return JSON.parse(compressedData);
    }
    
    setupPeriodicCleanup() {
        // Cleanup expired entries every 2 minutes
        setInterval(() => {
            this.cleanupExpired();
        }, 2 * 60 * 1000);
        
        // Memory pressure check every 30 seconds
        setInterval(() => {
            this.checkMemoryPressure();
        }, 30 * 1000);
    }
    
    cleanupExpired() {
        const now = Date.now();
        const keysToDelete = [];
        
        for (const [key, cached] of this.cache.entries()) {
            if (now - cached.timestamp > cached.ttl) {
                keysToDelete.push(key);
            }
        }
        
        keysToDelete.forEach(key => this.delete(key));
        
        if (keysToDelete.length > 0) {
            this.logCacheOperation('CLEANUP', null, null, { expired: keysToDelete.length });
        }
    }
    
    checkMemoryPressure() {
        // Check if we're using too much memory
        if (this.currentMemorySize > this.maxMemorySize * 0.8) {
            const targetSize = this.maxMemorySize * 0.6;
            const sizeToFree = this.currentMemorySize - targetSize;
            this.evictLeastUseful(sizeToFree);
        }
    }
    
    setupStorageMonitoring() {
        // Monitor storage quota if available
        if ('storage' in navigator && 'estimate' in navigator.storage) {
            navigator.storage.estimate().then(estimate => {
                this.storageQuota = estimate.quota;
                this.storageUsage = estimate.usage;
            }).catch(error => {
                console.warn('Failed to estimate storage:', error);
            });
        }
    }
    
    persistToStorage(key, cacheEntry) {
        try {
            // Only persist smaller, important entries
            if (cacheEntry.size < 100 * 1024) { // 100KB limit
                const storageKey = `vectorbid_cache_${key}`;
                const storageData = {
                    data: cacheEntry.data,
                    timestamp: cacheEntry.timestamp,
                    ttl: cacheEntry.ttl,
                    compressed: cacheEntry.compressed
                };
                
                localStorage.setItem(storageKey, JSON.stringify(storageData));
            }
        } catch (error) {
            // Storage quota exceeded or other error
            console.warn('Failed to persist cache entry to storage:', error);
        }
    }
    
    initializeFromStorage() {
        try {
            const keys = Object.keys(localStorage).filter(key => key.startsWith('vectorbid_cache_'));
            
            keys.forEach(storageKey => {
                try {
                    const data = JSON.parse(localStorage.getItem(storageKey));
                    const cacheKey = storageKey.replace('vectorbid_cache_', '');
                    
                    // Check if still valid
                    if (Date.now() - data.timestamp < data.ttl) {
                        const cacheEntry = {
                            ...data,
                            priority: this.priorityLevels.medium,
                            accessCount: 1,
                            lastAccessed: Date.now(),
                            size: this.estimateSize(data.data),
                            url: 'storage'
                        };
                        
                        this.cache.set(cacheKey, cacheEntry);
                        this.currentMemorySize += cacheEntry.size;
                    } else {
                        // Remove expired entry from storage
                        localStorage.removeItem(storageKey);
                    }
                } catch (error) {
                    console.warn('Failed to restore cache entry from storage:', error);
                    localStorage.removeItem(storageKey);
                }
            });
        } catch (error) {
            console.warn('Failed to initialize cache from storage:', error);
        }
    }
    
    removeFromStorage(key) {
        try {
            const storageKey = `vectorbid_cache_${key}`;
            localStorage.removeItem(storageKey);
        } catch (error) {
            console.warn('Failed to remove cache entry from storage:', error);
        }
    }
    
    clearStorage() {
        try {
            const keys = Object.keys(localStorage).filter(key => key.startsWith('vectorbid_cache_'));
            keys.forEach(key => localStorage.removeItem(key));
        } catch (error) {
            console.warn('Failed to clear cache storage:', error);
        }
    }
    
    getCacheStats() {
        const stats = {
            size: this.cache.size,
            maxSize: this.maxCacheSize,
            memoryUsage: this.currentMemorySize,
            maxMemorySize: this.maxMemorySize,
            memoryUsagePercent: (this.currentMemorySize / this.maxMemorySize * 100).toFixed(1),
            hitRate: this.calculateHitRate(),
            entries: []
        };
        
        for (const [key, cached] of this.cache.entries()) {
            stats.entries.push({
                key: key.substring(0, 50) + (key.length > 50 ? '...' : ''),
                age: Date.now() - cached.timestamp,
                ttl: cached.ttl,
                accessCount: cached.accessCount,
                size: cached.size,
                priority: Object.keys(this.priorityLevels).find(k => this.priorityLevels[k] === cached.priority),
                compressed: cached.compressed
            });
        }
        
        // Sort by access count descending
        stats.entries.sort((a, b) => b.accessCount - a.accessCount);
        
        return stats;
    }
    
    calculateHitRate() {
        // Simple hit rate calculation based on recent access patterns
        if (this.cache.size === 0) return 0;
        
        let totalAccess = 0;
        for (const count of this.accessCounts.values()) {
            totalAccess += count;
        }
        
        return totalAccess > 0 ? ((totalAccess - this.cache.size) / totalAccess * 100).toFixed(1) : 0;
    }
    
    logCacheOperation(operation, key, size, extra = {}) {
        if (window.PerformanceMonitor) {
            window.PerformanceMonitor.recordMetric(`Cache.${operation}`, 1, 'count');
            
            if (size) {
                window.PerformanceMonitor.recordMetric(`Cache.${operation}.Size`, size, 'bytes');
            }
        }
        
        // Debug logging (can be removed in production)
        if (window.location.hostname === 'localhost' || window.location.search.includes('debug=cache')) {
            console.debug(`Cache ${operation}:`, { key, size, ...extra });
        }
    }
    
    // Public API for enhanced cache integration
    wrap(url, apiFunction, payload = null, options = {}) {
        const cached = this.get(url, payload, options);
        if (cached !== null) {
            return Promise.resolve(cached);
        }
        
        return apiFunction().then(result => {
            this.set(url, payload, result, options);
            return result;
        });
    }
    
    preload(url, apiFunction, payload = null, options = {}) {
        // Preload data into cache without waiting
        if (!this.has(url, payload, options)) {
            apiFunction().then(result => {
                this.set(url, payload, result, { ...options, priority: 'low' });
            }).catch(error => {
                console.warn('Cache preload failed:', error);
            });
        }
    }
    
    // Memory cleanup method
    destroy() {
        this.clear();
        
        // Clean up intervals
        if (this.cleanupInterval) {
            clearInterval(this.cleanupInterval);
        }
        if (this.memoryCheckInterval) {
            clearInterval(this.memoryCheckInterval);
        }
    }
}

// Initialize global cache manager
window.CacheManager = new CacheManager();

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CacheManager;
}
