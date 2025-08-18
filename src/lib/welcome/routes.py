"""Welcome module routes for VectorBid application."""

from flask import Blueprint

# Create blueprint for welcome routes
bp = Blueprint("welcome", __name__, url_prefix="/welcome")

# This module can be extended in the future for welcome/landing page functionality
