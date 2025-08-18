"""
Authentication middleware and utilities.
"""

import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

async def auth_middleware(request: Request, call_next):
    """Intercept all calls to validate bearer token and manage user state."""
    
    logger.error(f"AUTH MIDDLEWARE ENTRY: {request.method} {request.url.path}")
    
    # Skip auth for health check endpoint and internal batch finalization
    logger.error(f"DEBUG: Checking path '{request.url.path}' against skip list")
    if request.url.path in ["/health", "/api/interviews/finalize/batch"]:
        logger.info(f"SKIPPING AUTH FOR INTERNAL ENDPOINT: {request.url.path}")
        return await call_next(request)
    else:
        logger.error(f"DEBUG: Path '{request.url.path}' NOT in skip list, continuing with auth")
    
    # Extract bearer token from Authorization header
    bearer_token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        bearer_token = auth_header[7:]
    
    # Debug: Log what token we received
    logger.info(f"DIRECT-CALL Auth middleware - Authorization header: {auth_header}")
    logger.info(f"DIRECT-CALL Auth middleware - Bearer token (first 50 chars): {bearer_token[:50] if bearer_token else 'None'}")
    
    # If no bearer token, return 401
    if not bearer_token:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required", "message": "Bearer token missing"}
        )
    
    try:
        # Get or create user from Redis
        user_data = await AuthService.get_or_create_user(bearer_token)
        logger.info(f"DEBUG: Auth middleware - user_data result: {user_data is not None}")
        logger.info(f"DEBUG: Auth middleware - user_data type: {type(user_data)}")
        if user_data:
            logger.info(f"DEBUG: Auth middleware - user_data email: {user_data.get('email', 'no-email')}")
        
        if not user_data:
            logger.error("DEBUG: Auth middleware - user_data is None/False, returning 401")
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid token", "message": "Bearer token invalid"}
            )
        
        # Add user data to request state
        request.state.user = user_data
        request.state.bearer_token = bearer_token
        
        logger.info("DEBUG: Auth middleware - about to call next()")
        # Continue with request
        try:
            response = await call_next(request)
            logger.info("DEBUG: Auth middleware - call_next() completed successfully")
            return response
        except Exception as call_next_error:
            logger.error(f"DEBUG: Exception in call_next(): {call_next_error}")
            import traceback
            logger.error(f"DEBUG: call_next() Traceback: {traceback.format_exc()}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "message": str(call_next_error)}
            )
        
    except Exception as e:
        logger.error(f"Auth middleware error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Authentication failed", "message": str(e)}
        )

def check_admin_access(request: Request) -> None:
    """Check if the authenticated user has admin privileges."""
    user_data = request.state.user
    if not user_data.get("admin", False):
        raise HTTPException(
            status_code=403, 
            detail="Admin access required"
        )