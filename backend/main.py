"""
AI Interviewer FastAPI Backend - MCP Mesh Integration
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

import mesh
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import DEV_MODE
from app.database.redis_client import redis_client
from app.services.interview_monitoring import monitoring_service
from app.middleware.auth import auth_middleware

# Import route modules
from app.routes import auth, interviews, upload, roles, admin

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app_instance):
    """Manage application lifespan - startup and shutdown."""
    # Startup
    logger.info("FastAPI startup - initializing background tasks")
    await monitoring_service.start_monitor()
    logger.info("Background interview timer monitor started successfully")
    
    yield  # Application runs here
    
    # Shutdown 
    await monitoring_service.stop_monitor()

app = FastAPI(
    title="AI Interviewer Backend", 
    version="1.0.0",
    description="Modularized FastAPI backend for AI Interviewer system",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware
app.middleware("http")(auth_middleware)

# Include routers
app.include_router(auth.router)
app.include_router(interviews.router)
app.include_router(upload.router)
app.include_router(roles.router)
app.include_router(admin.router)

@app.get("/debug/routes")
async def debug_routes():
    """Debug endpoint to list all registered routes."""
    routes = []
    for route in app.routes:
        if hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "methods": getattr(route, 'methods', [])
            })
    return {"routes": routes}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test Redis connection by calling ping through our client
        redis_client.client.ping()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "dev_mode": DEV_MODE,
            "services": {
                "redis": "healthy",
                "api": "healthy"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

@app.get("/api/users/interviews")
async def get_user_interviews(request: Request):
    """Get user's interview history."""
    user_data = request.state.user
    logger.info(f"Interview history requested by user: {user_data.get('email')}")
    
    # TODO: Query storage service for user's interviews via MCP Mesh
    # For now, return mock data
    mock_interviews = [
        {
            "interview_id": f"interview_{user_data.get('user_id')}_20241201_140000",
            "job_title": "Senior Python Developer",
            "date": "2024-12-01T14:00:00Z",
            "status": "completed",
            "score": 85,
            "recommendation": "Strong hire"
        },
        {
            "interview_id": f"interview_{user_data.get('user_id')}_20241128_100000",
            "job_title": "Full Stack Engineer",
            "date": "2024-11-28T10:00:00Z", 
            "status": "completed",
            "score": 72,
            "recommendation": "Proceed with caution"
        }
    ]
    
    return {"interviews": mock_interviews}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)