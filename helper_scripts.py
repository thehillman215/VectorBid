#!/usr/bin/env python3
"""
VectorBid Helper Scripts Suite
Collection of utility scripts for managing and enhancing VectorBid
Save this as: helper_scripts.py
"""

import os
import re
import json
import shutil
from pathlib import Path
from datetime import datetime
import sys


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


# ==============================================================================
# 1. MIGRATION SCRIPT - Updates existing routes automatically
# ==============================================================================


class RouteMigrator:
    """Automatically updates Flask routes to use new templates"""

    def __init__(self):
        self.root_dir = Path.cwd()
        self.routes_file = self.root_dir / "src" / "api" / "routes.py"
        self.admin_file = self.root_dir / "src" / "api" / "admin.py"
        self.backup_dir = self.root_dir / f"backup_routes_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def backup_routes(self):
        """Backup existing route files"""
        print_info("Backing up route files...")
        self.backup_dir.mkdir(exist_ok=True)

        if self.routes_file.exists():
            shutil.copy(self.routes_file, self.backup_dir / "routes.py")
            print_success(f"Backed up routes.py")
        if self.admin_file.exists():
            shutil.copy(self.admin_file, self.backup_dir / "admin.py")
            print_success(f"Backed up admin.py")

        print_success(f"Routes backed up to {self.backup_dir}")

    def update_template_references(self, content):
        """Update template references to new naming convention"""
        replacements = {
            r"render_template\(['\"]index\.html":
            "render_template('index.html",
            r"render_template\(['\"]dashboard\.html":
            "render_template('index.html",
            r"render_template\(['\"]admin\.html":
            "render_template('admin_dashboard.html",
            r"render_template\(['\"]results\.html":
            "render_template('results.html",
            r"render_template\(['\"]preferences\.html":
            "render_template('preferences.html",
            r"render_template\(['\"]login\.html":
            "render_template('auth/login.html",
            r"render_template\(['\"]signup\.html":
            "render_template('auth/signup.html",
        }

        for pattern, replacement in replacements.items():
            content = re.sub(pattern, replacement, content)

        return content

    def add_context_data(self, content):
        """Add necessary context data to routes"""
        # Add stats calculation for dashboard
        dashboard_context = '''
def get_dashboard_stats():
    """Get statistics for dashboard display"""
    return {
        'trips_count': 142,  # TODO: Get from database
        'match_score': 85,
        'days_off': 12,
        'block_hours': 72.5,
        'trips_trend': {'direction': 'up', 'value': 12}
    }
'''

        if "get_dashboard_stats" not in content:
            content = dashboard_context + "\n" + content

        # Update index route to include stats
        content = re.sub(
            r"return render_template\('index\.html'",
            "return render_template('index.html', stats=get_dashboard_stats()",
            content)

        return content

    def migrate(self):
        """Run the migration"""
        print_header("Route Migration Tool")

        self.backup_routes()

        # Update routes.py
        if self.routes_file.exists():
            print_info("Updating routes.py...")
            content = self.routes_file.read_text()
            content = self.update_template_references(content)
            content = self.add_context_data(content)
            self.routes_file.write_text(content)
            print_success("Updated routes.py")
        else:
            print_warning("routes.py not found - skipping")

        # Update admin.py
        if self.admin_file.exists():
            print_info("Updating admin.py...")
            content = self.admin_file.read_text()
            content = self.update_template_references(content)
            self.admin_file.write_text(content)
            print_success("Updated admin.py")
        else:
            print_warning("admin.py not found - skipping")

        print_success("Route migration complete!")


# ==============================================================================
# 2. THEME CUSTOMIZER - Interactive color picker for the UI
# ==============================================================================


class ThemeCustomizer:
    """Interactive theme customization tool"""

    def __init__(self):
        self.root_dir = Path.cwd()
        self.css_file = self.root_dir / "src" / "ui" / "static" / "css" / "vectorbid-modern.css"
        self.themes_dir = self.root_dir / "src" / "ui" / "static" / "css" / "themes"

    def create_theme_directory(self):
        """Create themes directory"""
        self.themes_dir.mkdir(parents=True, exist_ok=True)

    def show_current_theme(self):
        """Display current theme colors"""
        print_header("Current Theme Colors")

        if self.css_file.exists():
            content = self.css_file.read_text()

            # Extract primary color
            primary_match = re.search(r'--vb-primary:\s*(#[0-9a-fA-F]{6})',
                                      content)
            if primary_match:
                print(
                    f"Primary Color: {Colors.CYAN}{primary_match.group(1)}{Colors.ENDC}"
                )

            # Extract other key colors
            success_match = re.search(r'--vb-success:\s*(#[0-9a-fA-F]{6})',
                                      content)
            if success_match:
                print(
                    f"Success Color: {Colors.GREEN}{success_match.group(1)}{Colors.ENDC}"
                )

            warning_match = re.search(r'--vb-warning:\s*(#[0-9a-fA-F]{6})',
                                      content)
            if warning_match:
                print(
                    f"Warning Color: {Colors.WARNING}{warning_match.group(1)}{Colors.ENDC}"
                )
        else:
            print_error("CSS file not found")

    def create_preset_themes(self):
        """Create preset theme files"""
        themes = {
            "ocean": {
                "name": "Ocean Blue",
                "primary": "#0ea5e9",
                "primary-light": "#38bdf8",
                "primary-dark": "#0284c7",
                "success": "#22c55e",
                "warning": "#eab308",
                "danger": "#ef4444",
                "info": "#8b5cf6"
            },
            "sunset": {
                "name": "Sunset Orange",
                "primary": "#fb923c",
                "primary-light": "#fdba74",
                "primary-dark": "#ea580c",
                "success": "#22c55e",
                "warning": "#eab308",
                "danger": "#ef4444",
                "info": "#e11d48"
            },
            "forest": {
                "name": "Forest Green",
                "primary": "#16a34a",
                "primary-light": "#22c55e",
                "primary-dark": "#15803d",
                "success": "#22c55e",
                "warning": "#eab308",
                "danger": "#ef4444",
                "info": "#0ea5e9"
            },
            "midnight": {
                "name": "Midnight Purple",
                "primary": "#8b5cf6",
                "primary-light": "#a78bfa",
                "primary-dark": "#7c3aed",
                "success": "#22c55e",
                "warning": "#eab308",
                "danger": "#ef4444",
                "info": "#ec4899"
            },
            "aviation": {
                "name": "Aviation Classic",
                "primary": "#1e40af",
                "primary-light": "#3b82f6",
                "primary-dark": "#1e3a8a",
                "success": "#059669",
                "warning": "#d97706",
                "danger": "#dc2626",
                "info": "#7c3aed"
            }
        }

        for theme_id, colors in themes.items():
            theme_css = f'''/* VectorBid Theme: {colors['name']} */
:root {{
    --vb-primary: {colors['primary']};
    --vb-primary-light: {colors['primary-light']};
    --vb-primary-dark: {colors['primary-dark']};
    --vb-success: {colors['success']};
    --vb-warning: {colors['warning']};
    --vb-danger: {colors['danger']};
    --vb-info: {colors['info']};
}}
'''
            theme_file = self.themes_dir / f"theme-{theme_id}.css"
            theme_file.write_text(theme_css)
            print_success(f"Created theme: {colors['name']}")

    def apply_theme(self, theme_name):
        """Apply a preset theme"""
        theme_file = self.themes_dir / f"theme-{theme_name}.css"

        if not theme_file.exists():
            print_error(f"Theme '{theme_name}' not found")
            return

        # Read theme colors
        theme_content = theme_file.read_text()

        # Update main CSS file
        if self.css_file.exists():
            main_css = self.css_file.read_text()

            # Extract colors from theme
            color_pattern = r'--vb-(\w+(?:-\w+)?)\s*:\s*(#[0-9a-fA-F]{6})'
            theme_colors = re.findall(color_pattern, theme_content)

            # Replace colors in main CSS
            for var_name, color in theme_colors:
                pattern = f'--vb-{var_name}\\s*:\\s*#[0-9a-fA-F]{{6}}'
                replacement = f'--vb-{var_name}: {color}'
                main_css = re.sub(pattern, replacement, main_css)

            self.css_file.write_text(main_css)
            print_success(f"Applied theme: {theme_name}")

    def create_custom_theme(self):
        """Interactive custom theme creator"""
        print_header("Custom Theme Creator")

        print("Enter your custom colors (hex format, e.g., #0ea5e9):")
        print("Press Enter to use default value")

        custom = {}
        custom['primary'] = input("Primary Color [#0ea5e9]: ") or "#0ea5e9"
        custom['success'] = input("Success Color [#22c55e]: ") or "#22c55e"
        custom['warning'] = input("Warning Color [#eab308]: ") or "#eab308"
        custom['danger'] = input("Danger Color [#ef4444]: ") or "#ef4444"
        custom['info'] = input("Info Color [#8b5cf6]: ") or "#8b5cf6"

        theme_name = input("Theme name: ").lower().replace(" ", "-")

        # Generate light and dark variants
        def lighten(hex_color, percent=20):
            """Lighten a hex color"""
            hex_color = hex_color.lstrip('#')
            rgb = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
            new_rgb = tuple(
                min(255, int(c + (255 - c) * percent / 100)) for c in rgb)
            return '#{:02x}{:02x}{:02x}'.format(*new_rgb)

        def darken(hex_color, percent=20):
            """Darken a hex color"""
            hex_color = hex_color.lstrip('#')
            rgb = tuple(int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
            new_rgb = tuple(
                max(0, int(c * (100 - percent) / 100)) for c in rgb)
            return '#{:02x}{:02x}{:02x}'.format(*new_rgb)

        custom['primary-light'] = lighten(custom['primary'])
        custom['primary-dark'] = darken(custom['primary'])

        # Save custom theme
        theme_css = f'''/* VectorBid Custom Theme: {theme_name} */
:root {{
    --vb-primary: {custom['primary']};
    --vb-primary-light: {custom['primary-light']};
    --vb-primary-dark: {custom['primary-dark']};
    --vb-success: {custom['success']};
    --vb-warning: {custom['warning']};
    --vb-danger: {custom['danger']};
    --vb-info: {custom['info']};
}}
'''

        theme_file = self.themes_dir / f"theme-{theme_name}.css"
        theme_file.write_text(theme_css)
        print_success(f"Created custom theme: {theme_name}")

        apply = input("\nApply this theme now? (y/n): ")
        if apply.lower() == 'y':
            self.apply_theme(theme_name)

    def run(self):
        """Run the theme customizer"""
        print_header("VectorBid Theme Customizer")

        self.create_theme_directory()
        self.create_preset_themes()

        while True:
            print("\n" + "=" * 40)
            print("1. Show current theme")
            print("2. Apply preset theme")
            print("3. Create custom theme")
            print("4. Back to main menu")
            print("=" * 40)

            choice = input("\nSelect option: ")

            if choice == '1':
                self.show_current_theme()
            elif choice == '2':
                print("\nAvailable themes:")
                print("- ocean (Ocean Blue)")
                print("- sunset (Sunset Orange)")
                print("- forest (Forest Green)")
                print("- midnight (Midnight Purple)")
                print("- aviation (Aviation Classic)")
                theme = input("\nSelect theme: ")
                self.apply_theme(theme)
            elif choice == '3':
                self.create_custom_theme()
            elif choice == '4':
                break


# ==============================================================================
# 3. COMPONENT GENERATOR - Create new UI components easily
# ==============================================================================


class ComponentGenerator:
    """Generate new UI components from templates"""

    def __init__(self):
        self.root_dir = Path.cwd()
        self.components_dir = self.root_dir / "src" / "ui" / "templates" / "components"
        self.css_file = self.root_dir / "src" / "ui" / "static" / "css" / "components.css"

    def ensure_directory(self):
        """Ensure components directory exists"""
        self.components_dir.mkdir(parents=True, exist_ok=True)

    def create_component(self, component_type):
        """Create a new component based on type"""

        generators = {
            'card': self.generate_card,
            'modal': self.generate_modal,
            'form': self.generate_form,
            'table': self.generate_table,
            'alert': self.generate_alert,
            'badge': self.generate_badge
        }

        if component_type in generators:
            name = input(f"Enter {component_type} name: ").lower().replace(
                " ", "_")
            generators[component_type](name)
        else:
            print_error(f"Unknown component type: {component_type}")

    def generate_card(self, name):
        """Generate a card component"""
        template = f'''<!-- {name.replace('_', ' ').title()} Card Component -->
<div class="vb-card vb-card-{name}">
    <div class="vb-card-header">
        <h3 class="vb-card-title">{{{{ title }}}}</h3>
        {{% if subtitle %}}
        <p class="vb-card-subtitle">{{{{ subtitle }}}}</p>
        {{% endif %}}
    </div>
    <div class="vb-card-body">
        {{{{ content | safe }}}}
    </div>
    {{% if footer %}}
    <div class="vb-card-footer">
        {{{{ footer | safe }}}}
    </div>
    {{% endif %}}
</div>
'''

        component_file = self.components_dir / f"{name}_card.html"
        component_file.write_text(template)
        print_success(f"Created card component: {name}_card.html")

    def generate_modal(self, name):
        """Generate a modal component"""
        template = f'''<!-- {name.replace('_', ' ').title()} Modal Component -->
<div id="{name}Modal" class="vb-modal-wrapper" style="display: none;">
    <div class="vb-modal-backdrop" onclick="vectorbid.closeModal()"></div>
    <div class="vb-modal">
        <div class="vb-modal-header">
            <h3 class="vb-modal-title">{{{{ title }}}}</h3>
            <button class="vb-modal-close" onclick="vectorbid.closeModal()">
                <i class="fas fa-times"></i>
            </button>
        </div>
        <div class="vb-modal-body">
            {{{{ content | safe }}}}
        </div>
        <div class="vb-modal-footer">
            <button class="vb-btn vb-btn-secondary" onclick="vectorbid.closeModal()">
                Cancel
            </button>
            <button class="vb-btn vb-btn-primary" onclick="{{{{ action }}}}">
                {{{{ action_text | default('Confirm') }}}}
            </button>
        </div>
    </div>
</div>
'''

        component_file = self.components_dir / f"{name}_modal.html"
        component_file.write_text(template)
        print_success(f"Created modal component: {name}_modal.html")

    def generate_form(self, name):
        """Generate a form component"""
        template = f'''<!-- {name.replace('_', ' ').title()} Form Component -->
<form id="{name}Form" class="vb-form" method="POST" action="{{{{ action }}}}">
    {{% for field in fields %}}
    <div class="vb-form-group">
        <label class="vb-label" for="{{{{ field.id }}}}">
            {{{{ field.label }}}}
            {{% if field.required %}}
            <span class="vb-required">*</span>
            {{% endif %}}
        </label>

        {{% if field.type == 'textarea' %}}
        <textarea 
            name="{{{{ field.name }}}}" 
            id="{{{{ field.id }}}}"
            class="vb-textarea"
            placeholder="{{{{ field.placeholder }}}}">{{{{ field.value }}}}</textarea>
        {{% elif field.type == 'select' %}}
        <select 
            name="{{{{ field.name }}}}" 
            id="{{{{ field.id }}}}"
            class="vb-select">
            {{% for option in field.options %}}
            <option value="{{{{ option.value }}}}">{{{{ option.label }}}}</option>
            {{% endfor %}}
        </select>
        {{% else %}}
        <input 
            type="{{{{ field.type | default('text') }}}}"
            name="{{{{ field.name }}}}"
            id="{{{{ field.id }}}}"
            class="vb-input"
            value="{{{{ field.value }}}}"
            placeholder="{{{{ field.placeholder }}}}">
        {{% endif %}}
    </div>
    {{% endfor %}}

    <button type="submit" class="vb-btn vb-btn-primary">
        Submit
    </button>
</form>
'''

        component_file = self.components_dir / f"{name}_form.html"
        component_file.write_text(template)
        print_success(f"Created form component: {name}_form.html")

    def generate_table(self, name):
        """Generate a table component"""
        template = f'''<!-- {name.replace('_', ' ').title()} Table Component -->
<div class="vb-table-wrapper">
    <table class="vb-table vb-table-{name}">
        <thead>
            <tr>
                {{% for column in columns %}}
                <th>{{{{ column.label }}}}</th>
                {{% endfor %}}
            </tr>
        </thead>
        <tbody>
            {{% for row in rows %}}
            <tr>
                {{% for column in columns %}}
                <td>{{{{ row[column.key] }}}}</td>
                {{% endfor %}}
            </tr>
            {{% endfor %}}
        </tbody>
    </table>
</div>
'''

        component_file = self.components_dir / f"{name}_table.html"
        component_file.write_text(template)
        print_success(f"Created table component: {name}_table.html")

    def generate_alert(self, name):
        """Generate an alert component"""
        template = f'''<!-- {name.replace('_', ' ').title()} Alert Component -->
<div class="vb-alert vb-alert-{{{{ type | default('info') }}}}">
    <i class="fas fa-{{{{ icon | default('info-circle') }}}}"></i>
    {{{{ message }}}}
</div>
'''

        component_file = self.components_dir / f"{name}_alert.html"
        component_file.write_text(template)
        print_success(f"Created alert component: {name}_alert.html")

    def generate_badge(self, name):
        """Generate a badge component"""
        template = f'''<!-- {name.replace('_', ' ').title()} Badge Component -->
<span class="vb-badge vb-badge-{{{{ type | default('primary') }}}}">
    {{{{ text }}}}
</span>
'''

        component_file = self.components_dir / f"{name}_badge.html"
        component_file.write_text(template)
        print_success(f"Created badge component: {name}_badge.html")

    def run(self):
        """Run the component generator"""
        print_header("VectorBid Component Generator")

        self.ensure_directory()

        print("\nAvailable component types:")
        print("- card")
        print("- modal")
        print("- form")
        print("- table")
        print("- alert")
        print("- badge")

        component_type = input("\nSelect component type: ").lower()
        self.create_component(component_type)


# ==============================================================================
# 4. TEST SCRIPT - Validates all templates and routes
# ==============================================================================


class TemplateValidator:
    """Validate templates and routes"""

    def __init__(self):
        self.root_dir = Path.cwd()
        self.templates_dir = self.root_dir / "src" / "ui" / "templates"
        self.routes_dir = self.root_dir / "src" / "api"
        self.errors = []
        self.warnings = []

    def check_template_syntax(self, template_file):
        """Check Jinja2 template syntax"""
        content = template_file.read_text()

        # Check for balanced Jinja2 tags
        if content.count('{%') != content.count('%}'):
            self.errors.append(
                f"{template_file.name}: Unbalanced {{% %}} tags")

        if content.count('{{') != content.count('}}'):
            self.errors.append(
                f"{template_file.name}: Unbalanced {{{{ }}}} tags")

        # Check for required blocks in child templates
        if "{% extends" in content:
            if "{% block content %}" not in content:
                self.warnings.append(
                    f"{template_file.name}: Missing content block")

    def check_static_references(self, template_file):
        """Check that static file references exist"""
        content = template_file.read_text()

        # Find all url_for('static', ...) references
        static_refs = re.findall(r"url_for\('static',\s*filename='([^']+)'\)",
                                 content)

        for ref in static_refs:
            static_file = self.root_dir / "src" / "ui" / "static" / ref
            if not static_file.exists():
                self.warnings.append(
                    f"{template_file.name}: Missing static file: {ref}")

    def check_route_templates(self):
        """Check that all templates referenced in routes exist"""
        for route_file in self.routes_dir.glob("*.py"):
            if route_file.exists():
                content = route_file.read_text()

                # Find all render_template calls
                templates = re.findall(r"render_template\(['\"]([^'\"]+)['\"]",
                                       content)

                for template in templates:
                    template_file = self.templates_dir / template
                    if not template_file.exists():
                        self.errors.append(
                            f"{route_file.name}: Missing template: {template}")

    def check_components(self):
        """Check component usage"""
        components_dir = self.templates_dir / "components"

        if not components_dir.exists():
            self.warnings.append("Components directory not found")
            return

        # Check if components are used
        for component in components_dir.glob("*.html"):
            component_name = component.stem
            used = False

            for template in self.templates_dir.glob("*.html"):
                if template == component:
                    continue

                content = template.read_text()
                if f"include 'components/{component.name}'" in content:
                    used = True
                    break

            if not used:
                self.warnings.append(f"Component {component.name} is not used")

    def run_tests(self):
        """Run all validation tests"""
        print_header("Template Validation")

        if not self.templates_dir.exists():
            print_error("Templates directory not found!")
            return False

        # Check all templates
        for template in self.templates_dir.glob("**/*.html"):
            self.check_template_syntax(template)
            self.check_static_references(template)

        # Check routes
        self.check_route_templates()

        # Check components
        self.check_components()

        # Report results
        if self.errors:
            print_error(f"Found {len(self.errors)} errors:")
            for error in self.errors:
                print(f"  - {error}")
        else:
            print_success("No errors found!")

        if self.warnings:
            print_warning(f"Found {len(self.warnings)} warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")

        return len(self.errors) == 0


# ==============================================================================
# MAIN SCRIPT RUNNER
# ==============================================================================


def main():
    """Main script runner"""
    print_header("VectorBid Helper Scripts Suite")

    while True:
        print("\n" + "=" * 60)
        print("Available Tools:")
        print("1. Route Migration Tool - Update routes for new templates")
        print("2. Theme Customizer - Change UI colors and themes")
        print("3. Component Generator - Create new UI components")
        print("4. Template Validator - Test all templates and routes")
        print("5. Exit")
        print("=" * 60)

        choice = input("\nSelect tool (1-5): ")

        if choice == '1':
            migrator = RouteMigrator()
            migrator.migrate()
        elif choice == '2':
            customizer = ThemeCustomizer()
            customizer.run()
        elif choice == '3':
            generator = ComponentGenerator()
            generator.run()
        elif choice == '4':
            validator = TemplateValidator()
            validator.run_tests()
        elif choice == '5':
            print_success("Goodbye!")
            break
        else:
            print_error("Invalid choice")


if __name__ == "__main__":
    main()
