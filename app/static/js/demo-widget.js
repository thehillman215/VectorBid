// VectorBid Interactive Demo Widget
// Provides 60-second transformation experience

class VectorBidDemo {
    constructor() {
        this.currentStep = 0;
        this.selectedPersona = null;
        this.processingTimer = null;
        this.processingTime = 0;
        
        this.personas = {
            family_first: {
                name: "Family First",
                description: "Weekends off, family time priority",
                icon: "fas fa-home",
                input: "I want weekends off for family time, prefer morning departures, avoid red-eyes completely",
                preferences: {
                    weekend_priority: 0.9,
                    departure_time: "morning",
                    family_focus: true
                },
                recommendation: {
                    title: "Schedule A - Family Optimized",
                    weekend_protection: "87%",
                    avg_departure: "6:15 AM",
                    family_dinners: "90%",
                    trip_length: "2.3 days avg",
                    credit_hours: "78 hours"
                },
                reasoning: [
                    "Perfect family-friendly schedule with excellent weekend protection",
                    "Morning departures ensure you're home for family dinners",
                    "Short trip lengths maximize time at home",
                    "Realistic expectations for your seniority level"
                ]
            },
            money_maker: {
                name: "Money Maker", 
                description: "Maximum credit hours and earnings",
                icon: "fas fa-dollar-sign",
                input: "I want maximum credit hours and premium international routes for best earnings",
                preferences: {
                    credit_priority: 0.9,
                    international: 0.8,
                    earnings_focus: true
                },
                recommendation: {
                    title: "Schedule B - Earnings Maximized",
                    credit_hours: "96 hours",
                    international_routes: "75%",
                    premium_layovers: "London, Tokyo",
                    annual_earnings: "+$18,000",
                    efficiency: "98.2%"
                },
                reasoning: [
                    "Optimal high-credit schedule with premium international flying",
                    "London and Tokyo layovers provide excellent per diem",
                    "Efficient trip construction maximizes earnings potential",
                    "Career progression through international experience"
                ]
            },
            commuter_friendly: {
                name: "Commuter Friendly",
                description: "Optimized for commuting logistics", 
                icon: "fas fa-plane-departure",
                input: "I commute from Seattle to Denver base, need late starts and early finishes for airline connections",
                preferences: {
                    departure_time: "late_start",
                    commute_optimization: true,
                    connection_reliability: 0.9
                },
                recommendation: {
                    title: "Schedule C - Commute Optimized",
                    connection_success: "95%",
                    departure_time: "11:30 AM avg",
                    finish_time: "5:45 PM avg", 
                    commute_cost: "$800/month",
                    reliability: "Excellent"
                },
                reasoning: [
                    "Late starts allow 7 AM SEA-DEN commute connection",
                    "Early finishes catch 8 PM return flights reliably",
                    "Weather backup options identified for winter",
                    "Minimizes commute stress and unexpected costs"
                ]
            }
        };
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.loadPersonas();
    }
    
    setupEventListeners() {
        // Demo start buttons
        document.getElementById('start-demo')?.addEventListener('click', () => this.startDemo());
        document.getElementById('watch-video')?.addEventListener('click', () => this.showVideoDemo());
        
        // Step navigation
        document.getElementById('next-step-1')?.addEventListener('click', () => this.goToStep(1));
        document.getElementById('start-processing')?.addEventListener('click', () => this.startProcessing());
        document.getElementById('try-again')?.addEventListener('click', () => this.resetDemo());
        document.getElementById('start-trial')?.addEventListener('click', () => window.location.href = '/auth/signup');
    }
    
    loadPersonas() {
        const personaSelector = document.getElementById('persona-selector');
        if (!personaSelector) return;
        
        Object.entries(this.personas).forEach(([key, persona]) => {
            const personaCard = document.createElement('div');
            personaCard.className = 'persona-card cursor-pointer p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 transition-all';
            personaCard.dataset.persona = key;
            
            personaCard.innerHTML = `
                <div class="text-center">
                    <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                        <i class="${persona.icon} text-blue-600 text-xl"></i>
                    </div>
                    <h4 class="font-semibold text-gray-900 mb-1">${persona.name}</h4>
                    <p class="text-sm text-gray-600">${persona.description}</p>
                </div>
            `;
            
            personaCard.addEventListener('click', () => this.selectPersona(key));
            personaSelector.appendChild(personaCard);
        });
    }
    
    selectPersona(personaKey) {
        this.selectedPersona = personaKey;
        const persona = this.personas[personaKey];
        
        // Update UI
        document.querySelectorAll('.persona-card').forEach(card => {
            card.classList.remove('border-blue-500', 'bg-blue-50');
            card.classList.add('border-gray-200');
        });
        
        const selectedCard = document.querySelector(`[data-persona="${personaKey}"]`);
        selectedCard.classList.remove('border-gray-200');
        selectedCard.classList.add('border-blue-500', 'bg-blue-50');
        
        // Start typing animation
        this.typeText(persona.input);
        
        // Enable processing button
        document.getElementById('start-processing').disabled = false;
        document.getElementById('start-processing').classList.remove('opacity-50', 'cursor-not-allowed');
    }
    
    typeText(text) {
        const userInput = document.getElementById('user-input');
        if (!userInput) return;
        
        userInput.textContent = '';
        userInput.classList.add('typing-cursor');
        
        let index = 0;
        const typeInterval = setInterval(() => {
            if (index < text.length) {
                userInput.textContent += text[index];
                index++;
            } else {
                clearInterval(typeInterval);
                userInput.classList.remove('typing-cursor');
            }
        }, 50);
    }
    
    startDemo() {
        document.getElementById('demo-section').scrollIntoView({ behavior: 'smooth' });
        this.goToStep(0);
    }
    
    showVideoDemo() {
        document.getElementById('video-demo-section').classList.remove('hidden');
        document.getElementById('video-demo-section').scrollIntoView({ behavior: 'smooth' });
    }
    
    goToStep(stepNumber) {
        // Hide all steps
        document.querySelectorAll('.demo-step').forEach(step => {
            step.classList.remove('active');
            step.classList.add('hidden');
        });
        
        // Show current step
        const steps = ['step-comparison', 'step-input', 'step-processing', 'step-results'];
        const currentStepElement = document.getElementById(steps[stepNumber]);
        if (currentStepElement) {
            currentStepElement.classList.remove('hidden');
            currentStepElement.classList.add('active');
        }
        
        // Update progress
        this.updateProgress(stepNumber);
        this.currentStep = stepNumber;
    }
    
    updateProgress(stepNumber) {
        const progress = (stepNumber + 1) / 4 * 100;
        const progressBar = document.getElementById('demo-progress');
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
        }
    }
    
    startProcessing() {
        this.goToStep(2);
        this.processingTime = 0;
        
        const processingSteps = [
            { text: "🔍 Parsing natural language preferences...", delay: 500 },
            { text: "🧠 Analyzing pilot context and seniority...", delay: 1000 },
            { text: "⚖️ Balancing multiple preference weights...", delay: 1500 },
            { text: "📊 Evaluating 847 schedule candidates...", delay: 2000 },
            { text: "🎯 Applying AI context analysis...", delay: 2500 },
            { text: "✅ Generating optimized recommendations...", delay: 3000 }
        ];
        
        const processingContainer = document.getElementById('processing-steps');
        processingContainer.innerHTML = '';
        
        // Start timer
        this.processingTimer = setInterval(() => {
            this.processingTime += 0.1;
            document.getElementById('processing-time').textContent = this.processingTime.toFixed(1) + 's';
        }, 100);
        
        // Add processing steps with delays
        processingSteps.forEach((step, index) => {
            setTimeout(() => {
                const stepElement = document.createElement('div');
                stepElement.className = 'flex items-center space-x-3 text-white animate-fadeIn';
                stepElement.innerHTML = `
                    <div class="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                        <i class="fas fa-check text-xs"></i>
                    </div>
                    <span>${step.text}</span>
                `;
                processingContainer.appendChild(stepElement);
                
                // Show results after last step
                if (index === processingSteps.length - 1) {
                    setTimeout(() => {
                        clearInterval(this.processingTimer);
                        this.showResults();
                    }, 500);
                }
            }, step.delay);
        });
    }
    
    showResults() {
        this.goToStep(3);
        
        if (!this.selectedPersona) return;
        
        const persona = this.personas[this.selectedPersona];
        const recommendation = persona.recommendation;
        const reasoning = persona.reasoning;
        
        // Populate recommendation
        const recommendationContainer = document.getElementById('schedule-recommendation');
        recommendationContainer.innerHTML = `
            <h4 class="text-xl font-semibold text-gray-900 mb-4">${recommendation.title}</h4>
            <div class="space-y-3">
                ${Object.entries(recommendation).filter(([key]) => key !== 'title').map(([key, value]) => `
                    <div class="flex justify-between items-center">
                        <span class="text-gray-600 capitalize">${key.replace(/_/g, ' ')}:</span>
                        <span class="font-semibold text-gray-900">${value}</span>
                    </div>
                `).join('')}
            </div>
            <div class="mt-4 p-3 bg-green-50 rounded-lg">
                <div class="flex items-center">
                    <i class="fas fa-check-circle text-green-600 mr-2"></i>
                    <span class="text-sm font-medium text-green-800">Optimized for your priorities</span>
                </div>
            </div>
        `;
        
        // Populate reasoning
        const reasoningContainer = document.getElementById('ai-reasoning');
        reasoningContainer.innerHTML = reasoning.map(reason => `
            <div class="flex items-start space-x-3">
                <div class="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center mt-0.5">
                    <i class="fas fa-lightbulb text-blue-600 text-xs"></i>
                </div>
                <p class="text-gray-700">${reason}</p>
            </div>
        `).join('');
    }
    
    resetDemo() {
        this.selectedPersona = null;
        this.processingTime = 0;
        if (this.processingTimer) {
            clearInterval(this.processingTimer);
        }
        
        // Reset persona selection
        document.querySelectorAll('.persona-card').forEach(card => {
            card.classList.remove('border-blue-500', 'bg-blue-50');
            card.classList.add('border-gray-200');
        });
        
        // Reset user input
        const userInput = document.getElementById('user-input');
        if (userInput) {
            userInput.textContent = '';
        }
        
        // Disable processing button
        const processButton = document.getElementById('start-processing');
        if (processButton) {
            processButton.disabled = true;
            processButton.classList.add('opacity-50', 'cursor-not-allowed');
        }
        
        // Go back to input step
        this.goToStep(1);
    }
}

// Initialize demo when page loads
document.addEventListener('DOMContentLoaded', () => {
    new VectorBidDemo();
});

// Add CSS animation for fade in
const style = document.createElement('style');
style.textContent = `
    .animate-fadeIn {
        animation: fadeIn 0.5s ease-in-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
`;
document.head.appendChild(style);