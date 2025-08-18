// VectorBid SPA JavaScript
class VectorBidApp {
    constructor() {
        this.currentStep = 1;
        this.selectedPersona = null;
        this.preferences = {};
        this.results = {};
        this.init();
    }

    init() {
        this.loadPersonas();
        this.bindEvents();
        this.updateSliderValues();
    }

    async loadPersonas() {
        try {
            const response = await fetch('/api/personas');
            const data = await response.json();
            this.renderPersonas(data.personas);
        } catch (error) {
            console.error('Failed to load personas:', error);
        }
    }

    renderPersonas(personas) {
        const grid = document.getElementById('persona-grid');
        grid.innerHTML = '';

        // Add custom option
        const customCard = this.createPersonaCard('custom', {
            name: 'Custom',
            description: 'Create your own preferences',
            icon: 'fas fa-cog'
        });
        grid.appendChild(customCard);

        // Add persona options
        Object.entries(personas).forEach(([key, persona]) => {
            const card = this.createPersonaCard(key, persona);
            grid.appendChild(card);
        });
    }

    createPersonaCard(key, persona) {
        const card = document.createElement('div');
        card.className = 'persona-card bg-gray-50 border-2 border-gray-200 rounded-lg p-4 cursor-pointer';
        card.dataset.persona = key;
        
        card.innerHTML = `
            <div class="text-center">
                <i class="${persona.icon} text-3xl text-blue-600 mb-3"></i>
                <h3 class="text-lg font-semibold text-gray-900 mb-2">${persona.name}</h3>
                <p class="text-sm text-gray-600">${persona.description}</p>
            </div>
        `;

        card.addEventListener('click', () => this.selectPersona(key, card));
        return card;
    }

    selectPersona(persona, cardElement) {
        // Remove previous selection
        document.querySelectorAll('.persona-card').forEach(card => {
            card.classList.remove('selected');
        });

        // Add selection to clicked card
        cardElement.classList.add('selected');
        this.selectedPersona = persona;

        // Enable next button
        document.getElementById('next-to-preferences').disabled = false;

        // Pre-fill preferences if not custom
        if (persona !== 'custom') {
            this.loadPersonaPreferences(persona);
        }
    }

    async loadPersonaPreferences(persona) {
        // Load default preferences for selected persona
        const response = await fetch('/api/personas');
        const data = await response.json();
        const personaData = data.personas[persona];
        
        if (personaData && personaData.preferences) {
            document.getElementById('preferences-text').value = personaData.preferences;
        }

        // Set default weights
        if (personaData && personaData.weights) {
            Object.entries(personaData.weights).forEach(([key, value]) => {
                const slider = document.getElementById(`${key.replace('_', '-')}-weight`);
                if (slider) {
                    slider.value = value;
                    this.updateSliderValue(slider);
                }
            });
        }
    }

    bindEvents() {
        // Navigation
        document.getElementById('next-to-preferences').addEventListener('click', () => this.goToStep(2));
        document.getElementById('back-to-persona').addEventListener('click', () => this.goToStep(1));
        document.getElementById('back-to-preferences').addEventListener('click', () => this.goToStep(2));
        document.getElementById('compile-bid').addEventListener('click', () => this.compileBid());
        document.getElementById('start-over').addEventListener('click', () => this.goToStep(1));

        // Preferences
        document.getElementById('preferences-text').addEventListener('input', this.debounce(() => this.parsePreferences(), 500));

        // Sliders
        document.querySelectorAll('input[type="range"]').forEach(slider => {
            slider.addEventListener('input', () => this.updateSliderValue(slider));
        });

        // Results view switching
        document.getElementById('view-schedule').addEventListener('click', () => this.showScheduleView());
        document.getElementById('view-layers').addEventListener('click', () => this.showLayersView());

        // Export
        document.getElementById('export-bid').addEventListener('click', () => this.exportBid());
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    updateSliderValue(slider) {
        const valueDisplay = document.getElementById(slider.id.replace('-weight', '-value'));
        if (valueDisplay) {
            valueDisplay.textContent = slider.value;
        }
    }

    updateSliderValues() {
        document.querySelectorAll('input[type="range"]').forEach(slider => {
            this.updateSliderValue(slider);
        });
    }

    async parsePreferences() {
        const text = document.getElementById('preferences-text').value;
        if (!text.trim()) {
            document.getElementById('parsed-preview').classList.add('hidden');
            return;
        }

        try {
            const response = await fetch('/api/parse_preferences', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    preferences: text,
                    persona: this.selectedPersona 
                })
            });

            const data = await response.json();
            this.displayParsedPreferences(data);
        } catch (error) {
            console.error('Failed to parse preferences:', error);
        }
    }

    displayParsedPreferences(data) {
        const preview = document.getElementById('parsed-preview');
        const content = document.getElementById('parsed-content');
        
        let html = '<div class="space-y-2">';
        data.parsed_preferences.parsed_items.forEach(item => {
            const badge = item.category === 'hard_constraint' ? 'bg-red-100 text-red-800' : 'bg-blue-100 text-blue-800';
            html += `
                <div class="flex items-center justify-between">
                    <span class="text-sm">${item.text}</span>
                    <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${badge}">
                        ${(item.confidence * 100).toFixed(0)}%
                    </span>
                </div>
            `;
        });
        html += '</div>';
        
        content.innerHTML = html;
        preview.classList.remove('hidden');
    }

    goToStep(step) {
        // Hide all steps
        document.getElementById('persona-step').classList.add('hidden');
        document.getElementById('preferences-step').classList.add('hidden');
        document.getElementById('results-step').classList.add('hidden');

        // Update step indicators
        this.updateStepIndicators(step);

        // Show target step
        switch (step) {
            case 1:
                document.getElementById('persona-step').classList.remove('hidden');
                break;
            case 2:
                document.getElementById('preferences-step').classList.remove('hidden');
                break;
            case 3:
                document.getElementById('results-step').classList.remove('hidden');
                break;
        }

        this.currentStep = step;
    }

    updateStepIndicators(activeStep) {
        [1, 2, 3].forEach(step => {
            const stepElement = step === 1 ? document.querySelector('.flex.items-center.text-blue-600') :
                              document.getElementById(`step${step}`);
            const circle = stepElement.querySelector('div');
            const text = stepElement.querySelector('span');

            if (step <= activeStep) {
                circle.className = 'flex items-center justify-center w-8 h-8 bg-blue-600 text-white rounded-full text-sm font-medium';
                text.className = 'ml-2 text-sm font-medium text-blue-600';
            } else {
                circle.className = 'flex items-center justify-center w-8 h-8 bg-gray-300 text-gray-600 rounded-full text-sm font-medium';
                text.className = 'ml-2 text-sm font-medium text-gray-400';
            }
        });
    }

    async compileBid() {
        this.showLoading(true);

        try {
            // Collect all preferences
            const preferences = this.collectPreferences();

            // First validate constraints
            const validationResponse = await fetch('/api/validate_constraints', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(preferences)
            });

            const validation = await validationResponse.json();

            // Then optimize schedule
            const optimizeResponse = await fetch('/api/optimize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(preferences)
            });

            const optimization = await optimizeResponse.json();

            // Generate layers
            const layersResponse = await fetch('/api/generate_layers', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(preferences)
            });

            const layers = await layersResponse.json();

            this.results = {
                validation,
                optimization,
                layers
            };

            this.renderResults();
            this.goToStep(3);

        } catch (error) {
            console.error('Failed to compile bid:', error);
            alert('Failed to compile bid. Please try again.');
        } finally {
            this.showLoading(false);
        }
    }

    collectPreferences() {
        return {
            pilot_id: "demo_pilot",
            airline: "UAL",
            base: "SFO",
            seat: "FO",
            equip: ["B737", "B757"],
            hard_constraints: {
                no_weekends: document.getElementById('no-weekends').checked,
                no_redeyes: document.getElementById('no-redeyes').checked,
                domestic_only: document.getElementById('domestic-only').checked,
                max_duty_days: 4
            },
            soft_prefs: {
                weekend_weight: parseFloat(document.getElementById('weekend-weight').value),
                credit_weight: parseFloat(document.getElementById('credit-weight').value),
                trip_weight: parseFloat(document.getElementById('trip-weight').value)
            },
            preferences_text: document.getElementById('preferences-text').value,
            persona: this.selectedPersona
        };
    }

    renderResults() {
        this.renderCandidates();
        this.renderViolations();
        this.renderLayers();
    }

    renderCandidates() {
        const container = document.getElementById('candidates-list');
        const candidates = this.results.optimization.candidates;

        container.innerHTML = candidates.map((candidate, index) => `
            <div class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div class="flex items-center justify-between mb-3">
                    <div class="flex items-center">
                        <div class="flex items-center justify-center w-8 h-8 bg-blue-100 text-blue-800 rounded-full text-sm font-medium mr-3">
                            ${index + 1}
                        </div>
                        <div>
                            <h4 class="text-lg font-medium text-gray-900">Schedule ${candidate.candidate_id}</h4>
                            <p class="text-sm text-gray-500">Score: ${(candidate.score * 100).toFixed(1)}%</p>
                        </div>
                    </div>
                    <div class="text-right">
                        <div class="text-2xl font-bold text-green-600">${(candidate.score * 100).toFixed(0)}%</div>
                        <div class="text-xs text-gray-500">Match</div>
                    </div>
                </div>
                
                <div class="grid grid-cols-3 gap-2 mb-3">
                    ${Object.entries(candidate.soft_breakdown).map(([key, value]) => `
                        <div class="text-center">
                            <div class="text-sm font-medium text-gray-900">${(value * 100).toFixed(0)}%</div>
                            <div class="text-xs text-gray-500">${key.replace('_', ' ')}</div>
                        </div>
                    `).join('')}
                </div>

                <div class="mb-3">
                    <h5 class="text-sm font-medium text-gray-700 mb-1">Pairings:</h5>
                    <div class="text-sm text-gray-600">${candidate.pairings.join(', ')}</div>
                </div>

                <div class="mb-3">
                    <h5 class="text-sm font-medium text-gray-700 mb-1">Why this works:</h5>
                    <ul class="text-sm text-gray-600 list-disc list-inside">
                        ${candidate.rationale.map(reason => `<li>${reason}</li>`).join('')}
                    </ul>
                </div>

                <button onclick="app.explainCandidate('${candidate.candidate_id}')" 
                        class="text-blue-600 hover:text-blue-800 text-sm font-medium">
                    <i class="fas fa-info-circle mr-1"></i>
                    Explain ranking
                </button>
            </div>
        `).join('');
    }

    renderViolations() {
        const container = document.getElementById('violations-panel');
        const validation = this.results.validation;

        let html = `
            <div class="mb-4">
                <h4 class="text-sm font-medium text-gray-700 mb-2">Validation Score</h4>
                <div class="text-2xl font-bold text-green-600">${(validation.score * 100).toFixed(0)}%</div>
            </div>
        `;

        if (validation.violations.length > 0) {
            html += `
                <div class="mb-4">
                    <h4 class="text-sm font-medium text-red-700 mb-2">Violations</h4>
                    <ul class="text-sm text-red-600 space-y-1">
                        ${validation.violations.map(v => `<li>• ${v}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        if (validation.warnings.length > 0) {
            html += `
                <div>
                    <h4 class="text-sm font-medium text-yellow-700 mb-2">Warnings</h4>
                    <ul class="text-sm text-yellow-600 space-y-1">
                        ${validation.warnings.map(w => `<li>• ${w}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        container.innerHTML = html;
    }

    renderLayers() {
        const container = document.getElementById('layers-list');
        const layers = this.results.layers.display ? this.results.layers.display.layers : this.results.layers.layers;

        container.innerHTML = layers.map(layer => `
            <div class="bg-white border border-gray-200 rounded-lg p-4">
                <div class="flex items-center justify-between mb-3">
                    <h4 class="text-lg font-medium text-gray-900">Layer ${layer.layer_number}</h4>
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                        ${(layer.probability * 100).toFixed(0)}% chance
                    </span>
                </div>
                
                <p class="text-gray-600 mb-3">${layer.description}</p>
                
                <div class="mb-3">
                    <h5 class="text-sm font-medium text-gray-700 mb-2">PBS Commands:</h5>
                    <div class="bg-gray-50 rounded-md p-3">
                        <code class="text-sm text-gray-800">
                            ${layer.pbs_commands.join('<br>')}
                        </code>
                    </div>
                </div>
                
                <p class="text-sm text-gray-500">Expected: ${layer.expected_outcome}</p>
            </div>
        `).join('');
    }

    showScheduleView() {
        document.getElementById('schedule-results').classList.remove('hidden');
        document.getElementById('layers-results').classList.add('hidden');
        
        document.getElementById('view-schedule').className = 'bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors';
        document.getElementById('view-layers').className = 'bg-gray-200 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-300 transition-colors';
    }

    showLayersView() {
        document.getElementById('schedule-results').classList.add('hidden');
        document.getElementById('layers-results').classList.remove('hidden');
        
        document.getElementById('view-schedule').className = 'bg-gray-200 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-300 transition-colors';
        document.getElementById('view-layers').className = 'bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors';
    }

    async explainCandidate(candidateId) {
        try {
            const response = await fetch(`/api/explain/${candidateId}`);
            const explanation = await response.json();
            
            alert(`Score Breakdown for ${candidateId}:\n\n` +
                  `Base Score: ${explanation.explanation.score_breakdown.base_score}\n` +
                  `Bonuses: ${explanation.explanation.score_breakdown.weekend_bonus + explanation.explanation.score_breakdown.credit_bonus}\n` +
                  `Penalties: ${explanation.explanation.score_breakdown.penalties}\n\n` +
                  `Key Factors:\n${explanation.explanation.key_factors.join('\n• ')}`
            );
        } catch (error) {
            console.error('Failed to get explanation:', error);
        }
    }

    async exportBid() {
        try {
            const response = await fetch(`/api/exports/${this.results.layers.export_hash}`);
            const exportData = await response.json();
            
            // Create download
            const blob = new Blob([exportData.content], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            const month = this.results.layers.display ? this.results.layers.display.month : this.results.layers.month;
            a.download = `vectorbid_${month}.pbs`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Failed to export bid:', error);
        }
    }

    showLoading(show) {
        const overlay = document.getElementById('loading-overlay');
        if (show) {
            overlay.classList.remove('hidden');
        } else {
            overlay.classList.add('hidden');
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new VectorBidApp();
});