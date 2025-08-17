#!/bin/bash

cat > app/templates/smart_bid.html << 'EOHTML'
<!DOCTYPE html>
<html>
<head>
    <title>VectorBid - January 2025 Bid</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .persona-card {
            transition: all 0.3s ease;
            cursor: pointer;
        }
        .persona-card.selected {
            border-color: #3B82F6;
            background: #EFF6FF;
            transform: scale(1.02);
        }
        .fade-in {
            animation: fadeIn 0.5s ease-in;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        input[type="range"] {
            background: #E5E7EB;
        }
        .slider-fill {
            transition: width 0.3s ease;
        }
    </style>
</head>
<body class="bg-gray-50">
    <!-- Header -->
    <nav class="bg-blue-900 text-white p-4 shadow-lg">
        <div class="container mx-auto flex justify-between items-center">
            <div class="flex items-center space-x-3">
                <span class="text-2xl">✈️</span>
                <h1 class="text-xl font-bold">VectorBid</h1>
            </div>
            <div class="flex items-center space-x-4 text-sm">
                <span>{{ profile.name }}</span>
                <span class="text-blue-300">{{ profile.airline }}-{{ profile.base }} {{ profile.equipment }} {{ profile.seat }}</span>
                <a href="/profile" class="bg-blue-800 px-3 py-1 rounded hover:bg-blue-700">Profile</a>
            </div>
        </div>
    </nav>

    <div class="container mx-auto px-4 py-6 max-w-6xl">
        <!-- History Bar -->
        {% if history.last_month %}
        <div class="bg-blue-50 border-l-4 border-blue-500 p-4 mb-6 rounded">
            <p class="text-sm">
                <span class="font-medium">Last month:</span> You used <strong>{{ personas[history.last_month.persona].name }}</strong> 
                with {{ history.last_month.success_rate }} success rate
                <span class="text-gray-600 ml-2">• Common requests: {{ history.common_requests|join(", ") }}</span>
            </p>
        </div>
        {% endif %}

        <form method="post" action="/generate-pbs" id="bidForm">
            <div class="bg-white rounded-xl shadow-lg p-8">
                <div class="mb-8">
                    <h2 class="text-3xl font-bold">{{ current_month }} Bid Preferences</h2>
                    <p class="text-gray-600 mt-2">Choose your bidding strategy and customize for this month</p>
                </div>

                <!-- Persona Selection with Comparison -->
                <div class="mb-8">
                    <h3 class="text-lg font-semibold mb-4">Choose Your Bidding Strategy</h3>
                    <div class="grid grid-cols-3 gap-4">
                        {% for key, persona in personas.items() %}
                        <div class="persona-card border-2 rounded-lg p-4 hover:shadow-lg" 
                             onclick="selectPersona('{{ key }}')" id="persona-{{ key }}">
                            <input type="radio" name="persona" value="{{ key }}" class="hidden">
                            <div class="flex items-center justify-between mb-2">
                                <span class="text-2xl">{{ persona.icon }}</span>
                                {% if history.last_month.persona == key %}
                                <span class="text-xs bg-green-100 text-green-700 px-2 py-1 rounded">Used last month</span>
                                {% endif %}
                            </div>
                            <h4 class="font-semibold">{{ persona.name }}</h4>
                            <div class="flex flex-wrap gap-1 mt-2">
                                {% for badge in persona.badges %}
                                <span class="text-xs bg-gray-100 px-2 py-1 rounded">{{ badge }}</span>
                                {% endfor %}
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>

                <!-- Custom Preferences with Auto-fill -->
                <div class="mb-8">
                    <div class="flex justify-between items-center mb-3">
                        <h3 class="text-lg font-semibold">Customize Your Preferences</h3>
                        <div class="text-sm space-x-2">
                            <button type="button" onclick="showSaved()" class="text-blue-600 hover:underline">
                                📁 Load Saved
                            </button>
                            <button type="button" onclick="clearText()" class="text-gray-600 hover:underline">
                                Clear
                            </button>
                        </div>
                    </div>
                    <textarea name="preferences" id="prefText" rows="5" 
                        class="w-full p-4 border rounded-lg fade-in"
                        placeholder="Select a persona above to auto-fill, then customize..."></textarea>
                    <div class="flex items-center mt-2">
                        <input type="checkbox" name="save_preference" id="savePref" class="mr-2">
                        <label for="savePref" class="text-sm text-gray-600">Save these preferences for future use</label>
                    </div>
                </div>

                <!-- Priority Sliders -->
                <div class="mb-8">
                    <h3 class="text-lg font-semibold mb-4">Fine-tune Priorities</h3>
                    <div class="grid grid-cols-2 gap-6">
                        <div>
                            <div class="flex justify-between mb-2">
                                <label class="text-sm font-medium">⏰ Time at Home</label>
                                <span id="home-val" class="text-sm font-bold">5</span>
                            </div>
                            <input type="range" name="priority_time_home" id="home-slider" 
                                   min="1" max="10" value="5" oninput="updateSlider('home')">
                        </div>
                        <div>
                            <div class="flex justify-between mb-2">
                                <label class="text-sm font-medium">💰 Pay/Credit</label>
                                <span id="pay-val" class="text-sm font-bold">5</span>
                            </div>
                            <input type="range" name="priority_pay" id="pay-slider"
                                   min="1" max="10" value="5" oninput="updateSlider('pay')">
                        </div>
                        <div>
                            <div class="flex justify-between mb-2">
                                <label class="text-sm font-medium">📅 Weekends Off</label>
                                <span id="weekend-val" class="text-sm font-bold">5</span>
                            </div>
                            <input type="range" name="priority_weekends" id="weekend-slider"
                                   min="1" max="10" value="5" oninput="updateSlider('weekend')">
                        </div>
                        <div>
                            <div class="flex justify-between mb-2">
                                <label class="text-sm font-medium">😴 Rest/Comfort</label>
                                <span id="comfort-val" class="text-sm font-bold">5</span>
                            </div>
                            <input type="range" name="priority_comfort" id="comfort-slider"
                                   min="1" max="10" value="5" oninput="updateSlider('comfort')">
                        </div>
                    </div>
                </div>

                <button type="submit" class="w-full bg-blue-600 text-white py-4 rounded-lg font-semibold hover:bg-blue-700 transition text-lg">
                    Generate PBS Commands →
                </button>
            </div>
        </form>
    </div>

    <!-- Saved Preferences Modal -->
    <div id="savedModal" class="hidden fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
        <div class="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 class="text-lg font-semibold mb-4">Saved Preferences</h3>
            {% for pref in saved_preferences %}
            <div class="border p-3 rounded mb-2 cursor-pointer hover:bg-gray-50" 
                 onclick="loadSaved('{{ pref.text }}')">
                <div class="font-medium">{{ pref.name }}</div>
                <div class="text-sm text-gray-600">{{ pref.text }}</div>
            </div>
            {% endfor %}
            <button onclick="closeSaved()" class="mt-4 w-full bg-gray-500 text-white py-2 rounded">
                Close
            </button>
        </div>
    </div>

    <script>
    const personaData = {{ personas|tojson }};
    let currentPersona = null;
    let customText = "";

    function selectPersona(key) {
        // Visual feedback
        document.querySelectorAll('.persona-card').forEach(card => {
            card.classList.remove('selected');
        });
        document.getElementById('persona-' + key).classList.add('selected');
        document.querySelector(`input[value="${key}"]`).checked = true;
        
        // Store current custom text if exists
        const textArea = document.getElementById('prefText');
        const currentText = textArea.value;
        if (currentPersona && !currentText.startsWith(personaData[currentPersona].default_text)) {
            if (confirm('Keep your custom additions?')) {
                customText = currentText.replace(personaData[currentPersona].default_text, '').trim();
            } else {
                customText = "";
            }
        }
        
        // Update text and sliders
        currentPersona = key;
        const persona = personaData[key];
        textArea.value = persona.default_text + (customText ? "\\n\\n" + customText : "");
        textArea.classList.add('fade-in');
        
        // Update sliders
        updateSliderValue('home', persona.priorities.time_home);
        updateSliderValue('pay', persona.priorities.pay);
        updateSliderValue('weekend', persona.priorities.weekends);
        updateSliderValue('comfort', persona.priorities.comfort);
    }

    function updateSlider(name) {
        const slider = document.getElementById(name + '-slider');
        const val = document.getElementById(name + '-val');
        val.innerText = slider.value;
        const percent = (slider.value - 1) * 11.11;
        slider.style.background = `linear-gradient(to right, #3B82F6 0%, #3B82F6 ${percent}%, #E5E7EB ${percent}%, #E5E7EB 100%)`;
    }

    function updateSliderValue(name, value) {
        document.getElementById(name + '-slider').value = value;
        updateSlider(name);
    }

    function showSaved() {
        document.getElementById('savedModal').classList.remove('hidden');
    }

    function closeSaved() {
        document.getElementById('savedModal').classList.add('hidden');
    }

    function loadSaved(text) {
        document.getElementById('prefText').value = 
            (currentPersona ? personaData[currentPersona].default_text + "\\n\\n" : "") + text;
        closeSaved();
    }

    function clearText() {
        document.getElementById('prefText').value = "";
        customText = "";
    }

    // Initialize sliders
    window.onload = () => {
        ['home', 'pay', 'weekend', 'comfort'].forEach(updateSlider);
    };
    </script>
</body>
</html>
EOHTML

echo "✅ Smart template created!"
