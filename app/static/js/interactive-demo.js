// VectorBid Interactive Demo - Real API Integration
// Connects demo widget to actual backend APIs

class InteractiveDemo {
    constructor() {
        this.apiBase = '/api';
        this.isProcessing = false;
        this.demoState = 'idle'; // idle, parsing, optimizing, complete
        
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.setupDemoFlow();
    }
    
    bindEvents() {
        // Interactive demo button
        const demoBtn = document.querySelector('.demo-widget button');
        if (demoBtn) {
            demoBtn.addEventListener('click', () => this.startDemo());
        }
        
        // Try interactive demo button
        const interactiveBtn = document.querySelector('button[onclick*="Interactive Demo"]') || 
                              document.querySelector('button:contains("Try Interactive Demo")') ||
                              document.querySelector('.demo-preview button');
        if (interactiveBtn) {
            interactiveBtn.addEventListener('click', () => this.startDemo());
        }
    }
    
    setupDemoFlow() {
        // Create demo status indicator
        this.createStatusIndicator();
    }
    
    createStatusIndicator() {
        const demoSection = document.querySelector('.demo-preview') || 
                           document.querySelector('#demo-input')?.closest('.bg-white');
        
        if (!demoSection) return;
        
        const statusDiv = document.createElement('div');
        statusDiv.id = 'demo-status';
        statusDiv.className = 'mt-4 p-3 rounded-lg border text-sm font-mono hidden';
        statusDiv.innerHTML = `
            <div class="flex items-center">
                <div class="spinner hidden mr-2">⚡</div>
                <span class="status-text">Ready for demo</span>
            </div>
        `;
        
        demoSection.appendChild(statusDiv);
    }
    
    async startDemo() {
        if (this.isProcessing) return;
        
        this.isProcessing = true;
        this.updateStatus('🔄 Starting AI analysis...', 'processing');
        
        try {
            // Get demo input text
            const inputText = this.getDemoInputText();
            
            // Step 1: Parse preferences
            await this.parsePreferences(inputText);
            
            // Step 2: Optimize schedule
            await this.optimizeSchedule();
            
            // Step 3: Show results
            this.showResults();
            
        } catch (error) {
            this.handleError(error);
        } finally {
            this.isProcessing = false;
        }
    }
    
    getDemoInputText() {
        const demoInput = document.getElementById('demo-input');
        return demoInput ? demoInput.textContent.replace(/"/g, '') : 
               "I want weekends off for family time, prefer morning departures, avoid red-eyes completely";
    }
    
    async parsePreferences(text) {
        this.updateStatus('🧠 Parsing natural language preferences...', 'processing');
        
        const payload = {
            preferences_text: text,
            persona: "family_first"
        };
        
        const response = await this.apiCall('/parse', payload);
        this.parseResult = response;
        
        await this.delay(1500); // Show process
        this.updateStatus('✅ Preferences parsed successfully', 'success');
    }
    
    async optimizeSchedule() {
        this.updateStatus('⚡ AI optimizing schedule candidates...', 'processing');
        
        // Create mock feature bundle for demo
        const featureBundle = {
            context: {
                ctx_id: "demo_ctx_001",
                pilot_id: "demo_pilot",
                airline: "UAL",
                base: "SFO",
                seat: "FO",
                equip: ["73G"],
                seniority_percentile: 0.75,
                commuting_profile: {},
                default_weights: {}
            },
            preference_schema: {
                pilot_id: "demo_pilot",
                airline: "UAL", 
                base: "SFO",
                seat: "FO",
                equip: ["73G"],
                hard_constraints: {
                    days_off: [],
                    no_red_eyes: this.parseResult?.parsed_preferences?.hard_constraints?.no_redeyes || false,
                    max_duty_hours_per_day: null,
                    legalities: ["FAR117"]
                },
                soft_prefs: {
                    weekend_priority: this.parseResult?.parsed_preferences?.soft_preferences?.weekend_priority ? 
                        {weight: this.parseResult.parsed_preferences.soft_preferences.weekend_priority} : null,
                    report_time: this.parseResult?.parsed_preferences?.soft_preferences?.morning_departures ?
                        {weight: this.parseResult.parsed_preferences.soft_preferences.morning_departures} : null
                },
                weights_version: "2025-08-16",
                confidence: this.parseResult?.parsed_preferences?.confidence || 0.85,
                source: {demo: true}
            },
            analytics_features: {},
            compliance_flags: {},
            pairing_features: {
                pairings: [
                    {id: "SFO123", route: "SFO-LAX-SFO", duty_time: 8.5, weekends: false},
                    {id: "SFO456", route: "SFO-DEN-SFO", duty_time: 9.2, weekends: true}
                ]
            }
        };
        
        const payload = {
            feature_bundle: featureBundle,
            K: 10
        };
        
        const response = await this.apiCall('/optimize', payload);
        this.optimizeResult = response;
        
        await this.delay(2000); // Show AI working
        this.updateStatus('✅ Schedule optimization complete', 'success');
    }
    
    async apiCall(endpoint, payload) {
        const response = await fetch(`${this.apiBase}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            throw new Error(`API call failed: ${response.status} ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    showResults() {
        this.updateStatus('🎯 Results ready!', 'success');
        
        // Update the demo preview with real results
        this.updateDemoPreview();
    }
    
    updateDemoPreview() {
        const demoPreview = document.querySelector('.demo-preview');
        if (!demoPreview) return;
        
        const candidates = this.optimizeResult?.candidates || [];
        const topCandidate = candidates[0];
        
        if (topCandidate) {
            // Update with real API data
            const scoreElement = demoPreview.querySelector('.text-blue-400');
            if (scoreElement) {
                scoreElement.textContent = `${Math.round(topCandidate.score * 100)}% Confidence`;
            }
            
            // Update metrics with real data
            const weekendProtection = Math.round((topCandidate.soft_breakdown?.weekend_priority || 0.87) * 100);
            const familyTime = Math.round((topCandidate.soft_breakdown?.family_time || 0.90) * 100);
            
            const metrics = demoPreview.querySelectorAll('.flex.justify-between');
            if (metrics.length >= 3) {
                metrics[0].children[1].textContent = `${weekendProtection}%`;
                metrics[0].children[1].className = weekendProtection > 80 ? 'text-green-400' : 'text-yellow-400';
                
                metrics[2].children[1].textContent = `${familyTime}%`;
                metrics[2].children[1].className = familyTime > 85 ? 'text-green-400' : 'text-yellow-400';
            }
            
            // Show AI reasoning if available
            const reasoning = topCandidate.rationale?.explanation || 
                            "AI optimized for weekend protection while maximizing family time and early departures.";
            
            const reasoningElement = demoPreview.querySelector('.text-gray-300');
            if (reasoningElement) {
                reasoningElement.textContent = reasoning;
            }
        }
        
        // Update button to show success
        const demoBtn = demoPreview.querySelector('button');
        if (demoBtn) {
            demoBtn.innerHTML = '<i class="fas fa-check mr-2"></i>Demo Complete!';
            demoBtn.className = demoBtn.className.replace('bg-blue-600 hover:bg-blue-700', 'bg-green-600 hover:bg-green-700');
            
            setTimeout(() => {
                demoBtn.innerHTML = '<i class="fas fa-magic mr-2"></i>Try Interactive Demo';
                demoBtn.className = demoBtn.className.replace('bg-green-600 hover:bg-green-700', 'bg-blue-600 hover:bg-blue-700');
            }, 3000);
        }
    }
    
    updateStatus(message, type = 'info') {
        const statusEl = document.getElementById('demo-status');
        if (!statusEl) return;
        
        statusEl.className = `mt-4 p-3 rounded-lg border text-sm font-mono ${this.getStatusClasses(type)}`;
        statusEl.querySelector('.status-text').textContent = message;
        statusEl.classList.remove('hidden');
        
        // Auto-hide success messages
        if (type === 'success') {
            setTimeout(() => {
                statusEl.classList.add('hidden');
            }, 3000);
        }
    }
    
    getStatusClasses(type) {
        switch (type) {
            case 'processing':
                return 'border-blue-400 bg-blue-50 text-blue-800';
            case 'success':
                return 'border-green-400 bg-green-50 text-green-800';
            case 'error':
                return 'border-red-400 bg-red-50 text-red-800';
            default:
                return 'border-gray-400 bg-gray-50 text-gray-800';
        }
    }
    
    handleError(error) {
        console.error('Demo error:', error);
        this.updateStatus(`❌ Demo error: ${error.message}`, 'error');
        
        // Fallback to simulation mode
        setTimeout(() => {
            this.updateStatus('🔄 Falling back to simulation mode...', 'info');
            setTimeout(() => {
                this.showResults();
            }, 1000);
        }, 2000);
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.vectorBidDemo = new InteractiveDemo();
});

// Export for manual testing
window.InteractiveDemo = InteractiveDemo;