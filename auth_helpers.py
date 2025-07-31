"""Authentication and onboarding helpers."""
# Adding missing function definition and updating decorator docstring.
from functools import wraps
from flask import request, redirect, url_for
from services.db import get_profile


def get_current_user_id():
    """Get current user ID from Replit headers or use test user for open testing."""
    from flask import request
    # For open testing, always return a test user ID
    return request.headers.get("X-Replit-User-Id") or '44040350'

def requires_onboarding(f):
    """Decorator to check if user has completed onboarding - disabled for open testing."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Skip onboarding check for open testing
        return f(*args, **kwargs)
    return decorated_function