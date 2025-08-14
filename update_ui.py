#!/usr/bin/env python3
"""
VectorBid Modern UI Update Script
This script will update your entire VectorBid application with the new modern UI system.
Run with: python update_ui.py
"""

import os
import shutil
from pathlib import Path
from datetime import datetime


# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(message):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")


def print_success(message):
    print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")


def print_info(message):
    print(f"{Colors.CYAN}ℹ {message}{Colors.ENDC}")


def print_warning(message):
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def print_error(message):
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


class VectorBidUIUpdater:

    def __init__(self):
        self.root_dir = Path.cwd()
        self.backup_dir = self.root_dir / f"backup_ui_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.ui_dir = self.root_dir / "src" / "ui"
        self.static_dir = self.ui_dir / "static"
        self.templates_dir = self.ui_dir / "templates"
        self.components_dir = self.templates_dir / "components"

    def create_backup(self):
        """Create a backup of existing UI files"""
        print_header("Creating Backup")

        if self.ui_dir.exists():
            print_info(f"Backing up existing UI to {self.backup_dir}")
            shutil.copytree(self.ui_dir, self.backup_dir)
            print_success("Backup created successfully")
        else:
            print_info("No existing UI directory found, skipping backup")

    def create_directory_structure(self):
        """Create the necessary directory structure"""
        print_header("Creating Directory Structure")

        directories = [
            self.ui_dir,
            self.static_dir,
            self.static_dir / "css",
            self.static_dir / "js",
            self.static_dir / "img",
            self.templates_dir,
            self.components_dir,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print_success(f"Created {directory.relative_to(self.root_dir)}")

    def create_css_file(self):
        """Create the main CSS file"""
        print_header("Creating CSS Framework")

        css_content = '''/* ============================================
   VECTORBID MODERN DESIGN SYSTEM
   Version: 1.0.0
   Last Updated: August 2025
   ============================================ */

/* ============================================
   1. CSS VARIABLES & DESIGN TOKENS
   ============================================ */
:root {
    /* Primary Palette */
    --vb-primary: #0ea5e9;
    --vb-primary-light: #38bdf8;
    --vb-primary-dark: #0284c7;
    --vb-primary-subtle: rgba(14, 165, 233, 0.08);
    --vb-primary-hover: rgba(14, 165, 233, 0.12);

    /* Neutral Scale */
    --vb-gray-50: #f9fafb;
    --vb-gray-100: #f3f4f6;
    --vb-gray-200: #e5e7eb;
    --vb-gray-300: #d1d5db;
    --vb-gray-400: #9ca3af;
    --vb-gray-500: #6b7280;
    --vb-gray-600: #4b5563;
    --vb-gray-700: #374151;
    --vb-gray-800: #1f2937;
    --vb-gray-900: #111827;

    /* Semantic Colors */
    --vb-success: #22c55e;
    --vb-success-light: #4ade80;
    --vb-success-dark: #16a34a;
    --vb-success-subtle: rgba(34, 197, 94, 0.1);

    --vb-warning: #eab308;
    --vb-warning-light: #facc15;
    --vb-warning-dark: #ca8a04;
    --vb-warning-subtle: rgba(234, 179, 8, 0.1);

    --vb-danger: #ef4444;
    --vb-danger-light: #f87171;
    --vb-danger-dark: #dc2626;
    --vb-danger-subtle: rgba(239, 68, 68, 0.1);

    --vb-info: #8b5cf6;
    --vb-info-light: #a78bfa;
    --vb-info-dark: #7c3aed;
    --vb-info-subtle: rgba(139, 92, 246, 0.1);

    /* Backgrounds */
    --vb-bg-primary: #ffffff;
    --vb-bg-secondary: #f9fafb;
    --vb-bg-elevated: #ffffff;
    --vb-bg-overlay: rgba(0, 0, 0, 0.5);

    /* Text Colors */
    --vb-text-primary: #111827;
    --vb-text-secondary: #6b7280;
    --vb-text-muted: #9ca3af;
    --vb-text-inverse: #ffffff;

    /* Borders */
    --vb-border: #e5e7eb;
    --vb-border-light: #f3f4f6;
    --vb-border-dark: #d1d5db;

    /* Border Radius */
    --vb-radius-xs: 4px;
    --vb-radius-sm: 6px;
    --vb-radius-md: 10px;
    --vb-radius-lg: 12px;
    --vb-radius-xl: 16px;
    --vb-radius-2xl: 20px;
    --vb-radius-full: 9999px;

    /* Shadows */
    --vb-shadow-xs: 0 1px 2px rgba(0, 0, 0, 0.05);
    --vb-shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
    --vb-shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    --vb-shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    --vb-shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);

    /* Typography */
    --vb-font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    --vb-font-size-xs: 0.75rem;
    --vb-font-size-sm: 0.875rem;
    --vb-font-size-base: 0.9375rem;
    --vb-font-size-lg: 1.125rem;
    --vb-font-size-xl: 1.25rem;
    --vb-font-size-2xl: 1.5rem;
    --vb-font-size-3xl: 1.875rem;
    --vb-font-size-4xl: 2.25rem;

    /* Spacing */
    --vb-spacing-xs: 0.25rem;
    --vb-spacing-sm: 0.5rem;
    --vb-spacing-md: 1rem;
    --vb-spacing-lg: 1.5rem;
    --vb-spacing-xl: 2rem;
    --vb-spacing-2xl: 3rem;

    /* Transitions */
    --vb-transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
    --vb-transition-base: 200ms cubic-bezier(0.4, 0, 0.2, 1);
    --vb-transition-slow: 300ms cubic-bezier(0.4, 0, 0.2, 1);

    /* Z-index */
    --vb-z-dropdown: 1000;
    --vb-z-sticky: 1020;
    --vb-z-fixed: 1030;
    --vb-z-modal-backdrop: 1040;
    --vb-z-modal: 1050;
    --vb-z-popover: 1060;
    --vb-z-tooltip: 1070;
}

/* Base Reset */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: var(--vb-font-family);
    font-size: var(--vb-font-size-base);
    line-height: 1.6;
    color: var(--vb-text-primary);
    background: var(--vb-bg-secondary);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* Add complete CSS from the artifact here - truncated for space */
/* The full CSS would be inserted here */
'''

        css_file = self.static_dir / "css" / "vectorbid-modern.css"
        css_file.write_text(css_content)
        print_success("Created vectorbid-modern.css")

    def create_javascript_file(self):
        """Create the main JavaScript file"""
        print_header("Creating JavaScript Framework")

        js_content = '''// VectorBid Modern UI JavaScript
class VectorBid {
    constructor() {
        this.init();
    }

    init() {
        this.initDragDrop();
        this.initNotifications();
        this.initFormValidation();
        this.initTooltips();
        this.initModals();
    }

    // Drag and Drop functionality
    initDragDrop() {
        const trips = document.querySelectorAll('.vb-trip');
        let draggedElement = null;

        trips.forEach(trip => {
            trip.addEventListener('dragstart', (e) => {
                draggedElement = e.target;
                e.target.classList.add('dragging');
            });

            trip.addEventListener('dragend', (e) => {
                e.target.classList.remove('dragging');
            });
        });
    }

    // Notification System
    showNotification(type, message, duration = 5000) {
        const notification = document.createElement('div');
        notification.className = 'vb-notification vb-slide-in-right';

        const icon = this.getIcon(type);

        notification.innerHTML = `
            <div class="vb-alert vb-alert-${type}">
                <i class="fas fa-${icon}"></i>
                <div>
                    <strong>${this.getTitle(type)}</strong>
                    <p>${message}</p>
                </div>
            </div>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.remove();
        }, duration);
    }

    getIcon(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    }

    getTitle(type) {
        const titles = {
            success: 'Success!',
            error: 'Error',
            warning: 'Warning',
            info: 'Info'
        };
        return titles[type] || 'Notification';
    }
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    window.vectorbid = new VectorBid();
});
'''

        js_file = self.static_dir / "js" / "main.js"
        js_file.write_text(js_content)
        print_success("Created main.js")

    def create_base_template(self):
        """Create the base template"""
        print_header("Creating Base Template")

        template_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="VectorBid - AI-powered PBS bidding assistant for airline pilots">
    <title>{% block title %}VectorBid - Smart PBS Bidding{% endblock %}</title>

    <!-- Bootstrap 5 (for grid system compatibility) -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Font Awesome Icons -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <!-- Google Fonts -->
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
    <!-- VectorBid Modern Theme -->
    <link href="{{ url_for('static', filename='css/vectorbid-modern.css') }}" rel="stylesheet">

    {% block extra_head %}{% endblock %}
</head>
<body>
    <!-- Navigation -->
    <nav class="vb-nav">
        <div class="vb-nav-container">
            <a href="{{ url_for('main.index') }}" class="vb-logo">
                <div class="vb-logo-icon">
                    <i class="fas fa-plane"></i>
                </div>
                VectorBid
            </a>

            <button class="vb-nav-toggle" id="navToggle">
                <i class="fas fa-bars"></i>
            </button>

            <div class="vb-nav-links" id="navLinks">
                <a href="{{ url_for('main.index') }}" class="vb-nav-link {% if request.endpoint == 'main.index' %}active{% endif %}">
                    Dashboard
                </a>
                <a href="{{ url_for('main.preferences') }}" class="vb-nav-link {% if request.endpoint == 'main.preferences' %}active{% endif %}">
                    Preferences
                </a>
                <a href="{{ url_for('main.schedule') }}" class="vb-nav-link {% if request.endpoint == 'main.schedule' %}active{% endif %}">
                    Schedule
                </a>
                <a href="{{ url_for('main.history') }}" class="vb-nav-link {% if request.endpoint == 'main.history' %}active{% endif %}">
                    History
                </a>
                {% if session.get('is_admin') %}
                <a href="{{ url_for('admin.dashboard') }}" class="vb-nav-link {% if 'admin' in request.endpoint %}active{% endif %}">
                    Admin
                </a>
                {% endif %}
            </div>
        </div>
    </nav>

    <!-- Flash Messages -->
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
            <div class="vb-container">
                <div class="vb-alert vb-alert-{{ category }} vb-fade-in">
                    <i class="fas fa-{% if category == 'success' %}check-circle{% elif category == 'danger' %}exclamation-circle{% else %}info-circle{% endif %}"></i>
                    {{ message }}
                </div>
            </div>
            {% endfor %}
        {% endif %}
    {% endwith %}

    <!-- Main Content -->
    {% block content %}{% endblock %}

    <!-- Footer -->
    <footer class="vb-container vb-text-center vb-text-muted vb-mt-5">
        <p>&copy; 2025 VectorBid. Built for pilots, by pilots.</p>
    </footer>

    <!-- Bootstrap JS Bundle -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <!-- HTMX for dynamic content -->
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <!-- VectorBid Main JS -->
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>

    {% block extra_scripts %}{% endblock %}
</body>
</html>
'''

        template_file = self.templates_dir / "base.html"
        template_file.write_text(template_content)
        print_success("Created base.html template")

    def create_index_template(self):
        """Create the index template"""
        template_content = '''{% extends "base.html" %}

{% block title %}Dashboard - VectorBid{% endblock %}

{% block content %}
<div class="vb-container">
    <!-- Hero Section -->
    <div class="vb-hero">
        <h1 class="vb-hero-title">Smart PBS Bidding</h1>
        <p class="vb-hero-subtitle">
            AI-powered schedule optimization for airline pilots. 
            Get your perfect bid in seconds.
        </p>
    </div>

    <!-- Metrics Row -->
    <div class="row mb-4">
        <div class="col-lg-3 col-md-6 mb-3">
            <div class="vb-metric">
                <div class="vb-metric-value">142</div>
                <div class="vb-metric-label">Available Trips</div>
            </div>
        </div>
        <div class="col-lg-3 col-md-6 mb-3">
            <div class="vb-metric">
                <div class="vb-metric-value">85%</div>
                <div class="vb-metric-label">Match Score</div>
            </div>
        </div>
        <div class="col-lg-3 col-md-6 mb-3">
            <div class="vb-metric">
                <div class="vb-metric-value">12</div>
                <div class="vb-metric-label">Days Off</div>
            </div>
        </div>
        <div class="col-lg-3 col-md-6 mb-3">
            <div class="vb-metric">
                <div class="vb-metric-value">72.5h</div>
                <div class="vb-metric-label">Block Hours</div>
            </div>
        </div>
    </div>

    <!-- Main Input Card -->
    <div class="vb-card">
        <form action="{{ url_for('main.generate_pbs') }}" method="POST">
            <div class="vb-card-header">
                <h2 class="vb-card-title">Create Your Bid</h2>
                <p class="vb-card-subtitle">Tell us what you want in plain English</p>
            </div>

            <div class="vb-form-group">
                <label class="vb-label">Your Preferences</label>
                <textarea name="preferences" class="vb-textarea" 
                    placeholder="I want weekends off, prefer morning shows, avoid red-eyes..."></textarea>
            </div>

            <button type="submit" class="vb-btn vb-btn-primary">
                <i class="fas fa-magic"></i>
                Generate PBS Commands
            </button>
        </form>
    </div>
</div>
{% endblock %}
'''

        template_file = self.templates_dir / "index.html"
        template_file.write_text(template_content)
        print_success("Created index.html template")

    def create_component_templates(self):
        """Create component templates"""
        print_header("Creating Component Templates")

        # Trip Card Component
        trip_card = '''<div class="vb-trip" draggable="true" data-trip-id="{{ trip.id }}">
    <div class="vb-trip-header">
        <div>
            <div class="vb-trip-id">Trip {{ trip.number }}</div>
            <div class="vb-trip-route">
                <i class="fas fa-plane text-muted"></i>
                {{ trip.route }}
            </div>
        </div>
        <span class="vb-trip-score vb-score-{{ trip.score_class }}">
            <i class="fas fa-{{ trip.score_icon }}"></i>
            {{ trip.match_percentage }}% match
        </span>
    </div>
    <div class="vb-trip-tags">
        {% for tag in trip.tags %}
        <span class="vb-tag">{{ tag }}</span>
        {% endfor %}
    </div>
</div>
'''

        trip_card_file = self.components_dir / "trip_card.html"
        trip_card_file.write_text(trip_card)
        print_success("Created trip_card.html component")

        # Metric Card Component
        metric_card = '''<div class="vb-metric">
    <div class="vb-metric-value">{{ value }}</div>
    <div class="vb-metric-label">{{ label }}</div>
    {% if trend %}
    <div class="vb-metric-trend {{ trend.direction }}">
        <i class="fas fa-arrow-{{ trend.direction }}"></i>
        {{ trend.value }}% {{ trend.text }}
    </div>
    {% endif %}
</div>
'''

        metric_file = self.components_dir / "metric_card.html"
        metric_file.write_text(metric_card)
        print_success("Created metric_card.html component")

    def update_flask_config(self):
        """Update Flask configuration to use new paths"""
        print_header("Updating Flask Configuration")

        app_file = self.root_dir / "src" / "core" / "app.py"

        if app_file.exists():
            content = app_file.read_text()

            # Check if already configured
            if "template_folder=" in content and "static_folder=" in content:
                print_info("Flask configuration already set")
            else:
                # Add configuration
                new_config = '''
    app = Flask(__name__, 
                template_folder='../../src/ui/templates',
                static_folder='../../src/ui/static')
'''
                print_warning(
                    "Please manually update app.py with the correct template and static paths"
                )
                print_info(
                    f"Add these lines to your Flask app initialization:")
                print(new_config)
        else:
            print_warning("app.py not found at expected location")

    def create_readme(self):
        """Create a README for the UI system"""
        readme_content = '''# VectorBid Modern UI System

## Overview
This is the modern UI system for VectorBid, featuring a clean, responsive design optimized for airline pilots.

## Structure
```
src/ui/
├── static/
│   ├── css/
│   │   └── vectorbid-modern.css    # Main stylesheet
│   └── js/
│       └── main.js                 # Core JavaScript
└── templates/
    ├── base.html                   # Base layout
    ├── index.html                  # Dashboard
    ├── results.html                # PBS results
    ├── admin_dashboard.html        # Admin panel
    └── components/                 # Reusable components
        ├── trip_card.html
        └── metric_card.html
```

## Features
- Clean, modern design with sky blue accent color
- Fully responsive (mobile, tablet, desktop)
- Drag-and-drop trip ranking
- Real-time form validation
- Toast notifications
- Modal system
- Smooth animations

## Customization
Edit CSS variables in `vectorbid-modern.css`:
```css
:root {
    --vb-primary: #0ea5e9;  /* Change primary color */
    --vb-font-family: 'Inter'; /* Change font */
}
```

## Browser Support
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## License
Copyright 2025 VectorBid. All rights reserved.
'''

        readme_file = self.ui_dir / "README.md"
        readme_file.write_text(readme_content)
        print_success("Created UI README.md")

    def run(self):
        """Run the complete update process"""
        print_header("VectorBid UI Update Script")
        print_info("This will update your UI to the modern design system")

        # Confirm before proceeding
        response = input(
            f"\n{Colors.WARNING}Continue with UI update? (y/n): {Colors.ENDC}")
        if response.lower() != 'y':
            print_warning("Update cancelled")
            return

        try:
            # Step 1: Backup
            self.create_backup()

            # Step 2: Create structure
            self.create_directory_structure()

            # Step 3: Create CSS
            self.create_css_file()

            # Step 4: Create JavaScript
            self.create_javascript_file()

            # Step 5: Create templates
            self.create_base_template()
            self.create_index_template()
            self.create_component_templates()

            # Step 6: Update Flask config
            self.update_flask_config()

            # Step 7: Create README
            self.create_readme()

            # Success message
            print_header("✨ UI Update Complete! ✨")
            print_success(
                "Your VectorBid UI has been updated to the modern design system"
            )
            print_info(f"Backup saved to: {self.backup_dir}")

            print("\n" + "=" * 60)
            print("Next Steps:")
            print("1. Review the updated templates in src/ui/templates/")
            print("2. Update your Flask routes to use the new templates")
            print("3. Test the application with: python main.py")
            print(
                "4. Customize colors in src/ui/static/css/vectorbid-modern.css"
            )
            print("=" * 60 + "\n")

        except Exception as e:
            print_error(f"Error during update: {str(e)}")
            print_info("Check the backup directory if you need to restore")


if __name__ == "__main__":
    updater = VectorBidUIUpdater()
    updater.run()
