
# Add this to your existing src/api/routes.py file

# Import the fixed PBS generation
from src.api.pbs_fix import natural_language_to_pbs_filters

# Import personas
from src.lib.personas import PILOT_PERSONAS, get_persona_preferences

# Add calendar route
@bp.route('/calendar')
def calendar():
    """Display trip calendar view"""
    user_id = session.get('user_id', '44040350')
    profile = get_profile(user_id) or {}

    # Get trips from database or session
    trips = session.get('ranked_trips', [])

    return render_template('calendar.html', 
                         profile=profile,
                         trips=trips)

# Update the process route to use fixed PBS generation
@bp.route('/process', methods=['POST'])
def process():
    """Process preferences and generate PBS commands"""
    try:
        # Get preferences from form
        preferences = request.form.get('preferences', '')
        persona = request.form.get('persona', '')

        # If persona selected, use its preferences
        if persona and persona != 'custom':
            preferences = get_persona_preferences(persona)

        # Generate PBS filters using fixed function
        pbs_filters = natural_language_to_pbs_filters(preferences)

        # Store in session for results page
        session['pbs_filters'] = pbs_filters
        session['preferences'] = preferences

        # Log for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Generated {len(pbs_filters)} PBS filters from: {preferences}")

        return render_template('pbs_results.html',
                             pbs_filters=pbs_filters,
                             preferences=preferences)

    except Exception as e:
        flash(f"Error processing preferences: {str(e)}", 'error')
        return redirect(url_for('main.index'))
