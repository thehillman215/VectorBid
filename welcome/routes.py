"""Welcome wizard routes with HTMX-powered multi-step profile setup."""

from flask import (
    Blueprint,
    render_template,
    request,
    session,
    redirect,
    url_for,
    make_response,
)
from services.db import get_profile, save_profile

welcome_bp = Blueprint("welcome", __name__, url_prefix="/welcome")


@welcome_bp.route("/", methods=["GET"])
def wizard_start():
    """Step 1: Display airline selection wizard."""
    user_id = request.headers.get("X-Replit-User-Id")
    if not user_id:
        return redirect(url_for('replit_auth.login'))
    
    # Check if profile is already completed
    profile = get_profile(user_id)
    if profile.get('profile_completed', False):
        return redirect(url_for('main.index'))
    
    # Initialize session wizard data
    session['wizard_data'] = {
        'airline': profile.get('airline'),
        'fleet': profile.get('fleet', []),
        'seat': profile.get('seat'),
        'base': profile.get('base'),
        'seniority': profile.get('seniority')
    }
    
    return render_template("welcome/base_wizard.html", profile=profile)


@welcome_bp.route("/step/<int:step>", methods=["POST"])
def wizard_step(step):
    """Handle wizard step progression."""
    user_id = request.headers.get("X-Replit-User-Id")
    if not user_id:
        return redirect(url_for('replit_auth.login'))
    
    # Initialize wizard data if not present
    if 'wizard_data' not in session:
        session['wizard_data'] = {}
    
    if step == 1:
        # Process airline selection
        airline = request.form.get('airline', '').strip()
        if not airline:
            return render_template("welcome/step1.html", error="Please select an airline")
        
        session['wizard_data']['airline'] = airline
        session.modified = True
        
        return render_template("welcome/step2.html", 
                             wizard_data=session['wizard_data'])
    
    elif step == 2:
        # Process fleet selection and seat position
        fleet = request.form.getlist('fleet')
        seat = request.form.get('seat', '').strip()
        
        if not fleet:
            return render_template("welcome/step2.html", 
                                 wizard_data=session['wizard_data'],
                                 error="Please select at least one fleet type")
        
        if not seat or seat not in ['CA', 'FO']:
            return render_template("welcome/step2.html",
                                 wizard_data=session['wizard_data'],
                                 error="Please select your position (Captain or First Officer)")
        
        session['wizard_data']['fleet'] = fleet
        session['wizard_data']['seat'] = seat
        session.modified = True
        
        return render_template("welcome/step3.html",
                             wizard_data=session['wizard_data'])
    
    elif step == 3:
        # Process final step and save profile
        base = request.form.get('base', '').strip().upper()
        seniority_str = request.form.get('seniority', '').strip()
        
        if not base:
            return render_template("welcome/step3.html",
                                 wizard_data=session['wizard_data'],
                                 error="Please enter your home base")
        
        seniority = None
        if seniority_str and seniority_str.isdigit():
            seniority = int(seniority_str)
        
        # Update wizard data with final inputs
        session['wizard_data']['base'] = base
        session['wizard_data']['seniority'] = seniority
        session['wizard_data']['profile_completed'] = True
        
        # Save complete profile to database
        if save_profile(user_id, session['wizard_data']):
            # Clear wizard data from session
            session.pop('wizard_data', None)
            session.modified = True
            
            # Return HTMX redirect response
            response = make_response("")
            response.headers['HX-Redirect'] = url_for('main.index')
            return response
        else:
            return render_template("welcome/step3.html",
                                 wizard_data=session['wizard_data'],
                                 error="Error saving profile. Please try again.")
    
    # Invalid step
    return redirect(url_for('welcome.wizard_start'))