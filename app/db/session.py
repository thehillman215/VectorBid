"""
Database session management for VectorBid
Provides async session dependency injection
"""

from .database import get_session

__all__ = ["get_session"]