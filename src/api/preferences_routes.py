"""
Preference handling routes
Add this to your routes.py or create as separate blueprint
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from src.lib.personas import PILOT_PERSONAS, get_persona_preferences, get_persona_pbs_filters
from src.lib.services.db import save_profile, get_profile
import json

preferences_bp = Blueprint('preferences', __name__)

@preferences_bp.route('/preferences', methods=['GET', 'POST'])
def preferences():
    """Handle preference selection and saving"""
    user_id = session.get('user_id', '44040350')  # Default test user

    if request.method == 'POST':
        # Get form data
        persona = request.form.get('persona')
        custom_preferences = request.form.get('custom_preferences', '')

        # Get existing profile
        profile = get_profile(user_id) or {}

        # Update profile with preferences
        profile['persona'] = persona
        profile['custom_preferences'] = custom_preferences

        # If persona selected, get its preferences
        if persona and persona != 'custom':
            profile['preferences_text'] = get_persona_preferences(persona)
            profile['pbs_filters'] = get_persona_pbs_filters(persona)
        else:
            profile['preferences_text'] = custom_preferences
            # Generate PBS filters from custom text
            from src.api.pbs_fix import natural_language_to_pbs_filters
            profile['pbs_filters'] = natural_language_to_pbs_filters(custom_preferences)

        # Save profile
        save_profile(user_id, profile)

        flash('Preferences saved successfully!', 'success')
        return redirect(url_for('main.index'))

    # GET request - show form
    profile = get_profile(user_id) or {}
    return render_template('preferences.html', 
                         personas=PILOT_PERSONAS,
                         profile=profile)

@preferences_bp.route('/api/persona/<persona_key>')
def get_persona(persona_key):
    """API endpoint to get persona details"""
    if persona_key in PILOT_PERSONAS:
        return jsonify(PILOT_PERSONAS[persona_key])
    return jsonify({'error': 'Persona not found'}), 404
