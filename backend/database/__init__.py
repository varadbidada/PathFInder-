"""
Database package for MongoDB integration.
"""
from .connection import get_database, close_database_connection

__all__ = ["get_database", "close_database_connection"]
