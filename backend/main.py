#!/usr/bin/env python3
"""
Phase 2 FastAPI Backend - Clean API Gateway with MCP Mesh Integration

A minimal backend that delegates all business logic to MCP Mesh agents.
No authentication checks for initial testing phase.
"""

import logging
import os
from contextlib import asynccontextmanager

import mesh
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import route modules
from app.routes import jobs, applications, users, files, interviews


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown."""
    logger.info("🚀 Phase 2 Backend starting up...")
    logger.info("🔗 MCP Mesh enabled - agents will be auto-injected")
    yield
    logger.info("⏹️  Phase 2 Backend shutting down...")


# Create FastAPI application
app = FastAPI(
    title="AI Interviewer - Phase 2 Backend",
    description="Clean API Gateway with MCP Mesh Agent Integration",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Frontend ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint (no MCP dependency)
@app.get("/health")
async def health_check():
    """Health check endpoint for container orchestration."""
    return {
        "status": "healthy",
        "service": "ai-interviewer-phase2-backend",
        "version": "2.0.0"
    }

# Register route modules
app.include_router(jobs.router, prefix="/api")
app.include_router(applications.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(interviews.router, prefix="/api")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "AI Interviewer Phase 2 Backend",
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "jobs": "/api/jobs",
            "applications": "/api/applications",
            "users": "/api/users",
            "files": "/api/files",
            "interviews": "/api/interviews",
            "docs": "/docs"
        },
        "mcp_mesh": True
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0", 
        port=8080,
        reload=True,
        log_level="info"
    )