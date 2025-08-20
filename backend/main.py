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
from app.database.postgres import init_db, check_db_health
from app.services.interview_monitoring import monitoring_service
from app.middleware.auth import auth_middleware

# Import route modules
from app.routes import auth, interviews, upload, roles_new as roles, admin, reference

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app_instance):
    """Manage application lifespan - startup and shutdown."""
    # Startup
    logger.info("FastAPI startup - initializing services...")
    
    # Initialize PostgreSQL database (create tables if needed)
    logger.info("Initializing PostgreSQL database...")
    db_init_success = await init_db()
    if db_init_success:
        logger.info("PostgreSQL database initialized successfully")
        
        # Run database migrations and seed reference data
        try:
            from app.database.migrations import run_all_migrations
            run_all_migrations()
            logger.info("Database migrations and reference data seeding completed")
        except Exception as e:
            logger.error(f"Database migrations failed: {e}")
            # Continue anyway - migrations are often idempotent
    else:
        logger.error("PostgreSQL database initialization failed")
        # Don't exit - continue with Redis-only mode for backward compatibility
    
    # Start background monitoring
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
app.include_router(reference.router)

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
        # Test Redis connection
        redis_client.client.ping()
        redis_healthy = True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        redis_healthy = False
    
    try:
        # Test PostgreSQL connection
        postgres_healthy = await check_db_health()
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        postgres_healthy = False
    
    # Overall health status
    overall_healthy = redis_healthy and postgres_healthy
    status_code = 200 if overall_healthy else 503
    
    health_data = {
        "status": "healthy" if overall_healthy else "degraded",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "dev_mode": DEV_MODE,
        "services": {
            "redis": "healthy" if redis_healthy else "unhealthy",
            "postgresql": "healthy" if postgres_healthy else "unhealthy",
            "api": "healthy"
        }
    }
    
    if overall_healthy:
        return health_data
    else:
        return JSONResponse(status_code=status_code, content=health_data)

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