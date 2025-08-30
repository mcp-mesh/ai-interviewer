"""
SQLAlchemy Base Configuration

Provides the declarative base class for all interview agent models.
Centralizes SQLAlchemy configuration and base functionality.
"""

from sqlalchemy.orm import declarative_base

# SQLAlchemy declarative base for all models
Base = declarative_base()