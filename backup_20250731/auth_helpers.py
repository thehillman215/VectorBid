"""Authentication and onboarding helpers."""
# Adding missing function definition and updating decorator docstring.
from functools import wraps
from flask import request, redirect, url_for
from services.db import get_profile


def get_current_user_id():
    """Get current user ID from Replit headers."""
    from flask import request
    return request.headers.get("X-Replit-User-Id")

def requires_onboarding(f):
    """Decorator to check if user has completed onboarding."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_current_user_id()
        if user_id:
            profile = get_profile(user_id)
            if not profile.get('onboard_complete', False):
                return redirect(url_for('main.onboarding'))
        return f(*args, **kwargs)
    return decorated_function