# Create a base template with navigation
base_template = """<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}VectorBid{% endblock %}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    {% block head %}{% endblock %}
</head>
<body class="bg-gray-50">
    <!-- Navigation Bar -->
    <nav class="bg-blue-900 text-white shadow-lg">
        <div class="container mx-auto px-4 py-3">
            <div class="flex justify-between items-center">
                <div class="flex items-center space-x-6">
                    <a href="/" class="text-xl font-bold flex items-center space-x-2">
                        <span>✈️</span>
                        <span>VectorBid</span>
                    </a>
                    <div class="flex space-x-4 text-sm">
                        <a href="/" class="hover:text-blue-300">Home</a>
                        <a href="/test-panel" class="hover:text-blue-300 bg-yellow-600 px-2 py-1 rounded">🧪 Test Mode</a>
                        <a href="/onboarding" class="hover:text-blue-300">Setup</a>
                        <a href="/profile" class="hover:text-blue-300">Profile</a>
                    </div>
                </div>
                <div class="text-sm">
                    {% block user_info %}
                    <span>Not logged in</span>
                    {% endblock %}
                </div>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <main>
        {% block content %}{% endblock %}
    </main>

    {% block scripts %}{% endblock %}
</body>
</html>"""

# Save the base template
with open("app/templates/base_nav.html", "w") as f:
    f.write(base_template)

print("✅ Created base template with navigation")

# Update index.html to use the base
index_with_nav = """{% extends "base_nav.html" %}

{% block title %}VectorBid - Home{% endblock %}

{% block user_info %}
{% if profile %}
    {{ profile.name }} | {{ profile.airline }}-{{ profile.base }}
{% else %}
    <a href="/onboarding" class="bg-blue-700 px-3 py-1 rounded hover:bg-blue-600">Get Started</a>
{% endif %}
{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-8">
    <div class="bg-white rounded-xl shadow-lg p-8 max-w-2xl mx-auto">
        <h1 class="text-3xl font-bold mb-4">Welcome to VectorBid</h1>

        <div class="space-y-4">
            <a href="/test-panel" class="block w-full bg-yellow-500 text-white py-3 px-6 rounded-lg text-center hover:bg-yellow-600">
                🧪 Open Test Control Panel
            </a>

            <a href="/onboarding" class="block w-full bg-blue-600 text-white py-3 px-6 rounded-lg text-center hover:bg-blue-700">
                👤 Setup Profile (First Time)
            </a>

            {% if profile %}
            <div class="border-t pt-4 mt-4">
                <p class="text-gray-600 mb-3">Logged in as: <strong>{{ profile.name }}</strong></p>
                <a href="/" class="block w-full bg-green-600 text-white py-3 px-6 rounded-lg text-center hover:bg-green-700">
                    ✈️ Generate Monthly Bid
                </a>
            </div>
            {% else %}
            <p class="text-gray-500 text-center">Set up your profile first to start bidding</p>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}"""

with open("app/templates/index_nav.html", "w") as f:
    f.write(index_with_nav)

print("✅ Created index with navigation menu")
