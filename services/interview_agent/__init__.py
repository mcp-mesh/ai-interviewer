#!/usr/bin/env python3
"""
Interview Agent Package

AI-powered technical interviewer agent for the AI Interviewer MCP Mesh system.
Conducts dynamic interviews based on role requirements and candidate profiles.
"""

__version__ = "1.0.0"
__author__ = "AI Interviewer Team"
__description__ = "Technical interview conductor with session management"

from .main import InterviewAgent

__all__ = ["InterviewAgent"]