# main.py - AI Interviewer FastAPI Backend
import asyncio
import os
import json
import hashlib
import logging
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from io import BytesIO

import redis
import httpx
import jwt
from minio import Minio
from minio.error import S3Error
from fastapi import FastAPI, Header, HTTPException, WebSocket, UploadFile, File, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Background task control
_timer_task = None

@asynccontextmanager
async def lifespan(app_instance):
    """Manage application lifespan - startup and shutdown."""
    # Startup
    logger.info("FastAPI startup - initializing background tasks")
    await start_timer_monitor()
    logger.info("Background interview timer monitor started successfully")
    
    yield  # Application runs here
    
    # Shutdown 
    global _timer_task
    if _timer_task and not _timer_task.done():
        logger.info("Shutting down timer monitor")
        _timer_task.cancel()
        try:
            await _timer_task
        except asyncio.CancelledError:
            pass

app = FastAPI(
    title="AI Interviewer Backend", 
    version="1.0.0",
    description="Auth-free FastAPI backend for AI Interviewer system",
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

# Redis connection
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(redis_url, decode_responses=True)

# Timer monitoring constants
SESSION_PREFIX = "interview_session:"
INTERVIEW_TIMEOUT_SECONDS = 300  # 5 minutes
LOCK_PREFIX = "interview_expire_lock:"
LOCK_TTL = 300  # 5 minutes lock expiry

# MinIO S3 client configuration (optional for testing)
minio_client = None
bucket_name = "ai-interviewer-uploads"
try:
    minio_host = os.getenv("MINIO_HOST", "minio:9000")
    minio_client = Minio(
        minio_host,
        access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin123"),
        secure=False  # Use HTTP for internal communication
    )
    
    # Ensure bucket exists
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)
        logger.info(f"Created MinIO bucket: {bucket_name}")
except Exception as e:
    logger.warning(f"MinIO not available, file uploads will be disabled: {e}")
    minio_client = None

# Environment variables for MCP services
PDF_EXTRACTOR_URL = os.getenv("PDF_EXTRACTOR_URL", "http://pdf-extractor:8090")
INTERVIEW_AGENT_URL = os.getenv("INTERVIEW_AGENT_URL", "http://interview-agent:8090")

# Timer monitoring functions
def is_session_expired(session_data: dict) -> bool:
    """Check if a session has expired based on start_time + duration."""
    try:
        start_time_str = session_data.get("start_time")
        duration = session_data.get("duration", INTERVIEW_TIMEOUT_SECONDS)  # fallback to old logic
        
        if not start_time_str:
            # Fallback to old logic for backward compatibility
            created_at_str = session_data.get("created_at")
            if not created_at_str:
                return True
            start_time_str = created_at_str
            
        start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        elapsed_seconds = (now - start_time).total_seconds()
        
        return elapsed_seconds > duration
    except Exception as e:
        logger.error(f"Error checking session expiry: {e}")
        return True


async def acquire_expire_lock(session_id: str) -> bool:
    """Acquire distributed lock for session expiry processing."""
    try:
        lock_key = f"{LOCK_PREFIX}{session_id}"
        result = redis_client.set(lock_key, "locked", nx=True, ex=LOCK_TTL)
        return bool(result)
    except Exception as e:
        logger.error(f"Error acquiring expire lock for {session_id}: {e}")
        return False


async def release_expire_lock(session_id: str) -> bool:
    """Release distributed lock for session expiry."""
    try:
        lock_key = f"{LOCK_PREFIX}{session_id}"
        result = redis_client.delete(lock_key)
        return bool(result)
    except Exception as e:
        logger.error(f"Error releasing expire lock for {session_id}: {e}")
        return False


async def finalize_expired_session_via_mcp(session_id: str) -> bool:
    """Finalize expired session by calling interview agent MCP tool."""
    try:
        logger.info(f"Finalizing expired session via MCP: {session_id}")
        
        result = await call_interview_agent("finalize_interview", {"session_id": session_id})
        
        if result and result.get("success"):
            logger.info(f"Successfully finalized expired session {session_id}: score={result.get('score', 0)}")
            return True
        else:
            error_msg = result.get("error", "Unknown error") if result else "No response"
            logger.error(f"Failed to finalize session {session_id}: {error_msg}")
            return False
            
    except Exception as e:
        logger.error(f"Error finalizing expired session {session_id}: {e}")
        return False


async def monitor_expired_interviews():
    """Background task to monitor and finalize expired interview sessions."""
    logger.info("Starting interview expiry monitor in backend")
    
    while True:
        try:
            # Scan for all interview sessions
            pattern = f"{SESSION_PREFIX}*"
            session_keys = []
            
            cursor = 0
            while True:
                cursor, keys = redis_client.scan(cursor=cursor, match=pattern, count=100)
                session_keys.extend(keys)
                if cursor == 0:
                    break
            
            logger.debug(f"Found {len(session_keys)} interview sessions to check")
            
            # Check each session for expiry
            expired_count = 0
            for key in session_keys:
                try:
                    session_id = key.replace(SESSION_PREFIX, "")
                    
                    # Try to acquire lock for this session
                    if await acquire_expire_lock(session_id):
                        try:
                            # Get session data
                            session_data_json = redis_client.get(key)
                            if session_data_json:
                                session_data = json.loads(session_data_json)
                                
                                # Check if expired and not already completed
                                current_status = session_data.get("status", "active")
                                if current_status == "active" and is_session_expired(session_data):
                                    # Session is expired, finalize via MCP
                                    success = await finalize_expired_session_via_mcp(session_id)
                                    if success:
                                        expired_count += 1
                                        logger.info(f"Finalized expired session: {session_id}")
                        finally:
                            # Always release the lock
                            await release_expire_lock(session_id)
                    else:
                        # Lock couldn't be acquired, another instance is handling it
                        logger.debug(f"Session {session_id} is being processed by another instance")
                        
                except Exception as e:
                    logger.error(f"Error processing session {key}: {e}")
                    # Make sure to release lock in case of error
                    session_id = key.replace(SESSION_PREFIX, "")
                    await release_expire_lock(session_id)
            
            if expired_count > 0:
                logger.info(f"Processed {expired_count} expired interviews")
            
        except Exception as e:
            logger.error(f"Error in interview monitor: {e}")
        
        # Wait 30 seconds before next check
        await asyncio.sleep(30)


async def start_timer_monitor():
    """Start the background timer monitor task."""
    global _timer_task
    
    if _timer_task is None or _timer_task.done():
        logger.info("Starting background interview timer monitor")
        _timer_task = asyncio.create_task(monitor_expired_interviews())
    else:
        logger.info("Background timer monitor already running")




# Authentication middleware
@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    """Intercept all calls to validate bearer token and manage user state."""
    
    logger.error(f"🔥🔥🔥 AUTH MIDDLEWARE ENTRY: {request.method} {request.url.path} 🔥🔥🔥")
    
    # Skip auth for health check endpoint
    if request.url.path == "/health":
        logger.error(f"🔥🔥🔥 SKIPPING AUTH FOR HEALTH CHECK 🔥🔥🔥")
        return await call_next(request)
    
    # Extract bearer token from Authorization header
    bearer_token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        bearer_token = auth_header[7:]
    
    # Debug: Log what token we received
    logger.info(f"🚀 DIRECT-CALL Auth middleware - Authorization header: {auth_header}")
    logger.info(f"🚀 DIRECT-CALL Auth middleware - Bearer token (first 50 chars): {bearer_token[:50] if bearer_token else 'None'}")
    
    # If no bearer token, return 401
    if not bearer_token:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required", "message": "Bearer token missing"}
        )
    
    try:
        # Get or create user from Redis
        user_data = await get_or_create_user(bearer_token)
        logger.info(f"🔍 DEBUG: Auth middleware - user_data result: {user_data is not None}")
        logger.info(f"🔍 DEBUG: Auth middleware - user_data type: {type(user_data)}")
        if user_data:
            logger.info(f"🔍 DEBUG: Auth middleware - user_data email: {user_data.get('email', 'no-email')}")
        
        if not user_data:
            logger.error("🔍 DEBUG: Auth middleware - user_data is None/False, returning 401")
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid token", "message": "Bearer token invalid"}
            )
        
        # Add user data to request state
        request.state.user = user_data
        request.state.bearer_token = bearer_token
        
        logger.info("🔍 DEBUG: Auth middleware - about to call next()")
        # Continue with request
        try:
            response = await call_next(request)
            logger.info("🔍 DEBUG: Auth middleware - call_next() completed successfully")
            return response
        except Exception as call_next_error:
            logger.error(f"🔍 DEBUG: Exception in call_next(): {call_next_error}")
            import traceback
            logger.error(f"🔍 DEBUG: call_next() Traceback: {traceback.format_exc()}")
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

def parse_oauth_token(bearer_token: str) -> Optional[Dict[str, Any]]:
    """Parse OAuth JWT token to extract user info (without signature verification)."""
    try:
        # Handle both access tokens and ID tokens
        # Try to decode as JWT without verification (we trust nginx validated it)
        try:
            # For ID tokens (JWT format)
            payload = jwt.decode(bearer_token, options={"verify_signature": False})
            logger.info(f"Parsed ID token for user: {payload.get('email', 'unknown')}")
            return {
                "email": payload.get("email"),
                "name": payload.get("name"),
                "given_name": payload.get("given_name"),
                "family_name": payload.get("family_name"),
                "provider": "google",
                "token_type": "id_token",
                "sub": payload.get("sub")
            }
        except jwt.DecodeError:
            # For access tokens (opaque format), we need to call Google's userinfo endpoint
            logger.info("Token is not JWT format, treating as access token")
            return {
                "token_type": "access_token",
                "access_token": bearer_token
            }
            
    except Exception as e:
        logger.error(f"Error parsing OAuth token: {e}")
        return None

async def get_user_info_from_access_token(access_token: str) -> Optional[Dict[str, Any]]:
    """Get user info from Google using access token."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            if response.status_code == 200:
                user_info = response.json()
                logger.info(f"Retrieved user info for: {user_info.get('email', 'unknown')}")
                return {
                    "email": user_info.get("email"),
                    "name": user_info.get("name"),
                    "given_name": user_info.get("given_name"),  
                    "family_name": user_info.get("family_name"),
                    "provider": "google",
                    "token_type": "access_token"
                }
            else:
                logger.error(f"Failed to get user info: {response.status_code}")
                return None
    except Exception as e:
        logger.error(f"Error getting user info from access token: {e}")
        return None

async def get_or_create_user(bearer_token: str) -> Optional[Dict[str, Any]]:
    """Parse OAuth token and get/create user profile."""
    try:
        logger.info(f"🔍 DEBUG: Starting get_or_create_user with token length: {len(bearer_token)}")
        
        # Parse the OAuth token
        token_info = parse_oauth_token(bearer_token)
        logger.info(f"🔍 DEBUG: Token info received: {token_info is not None}")
        if not token_info:
            logger.error("🔍 DEBUG: Token info is None, returning None")
            return None
        
        user_email = None
        user_name = None
        
        logger.info(f"🔍 DEBUG: Token type: {token_info.get('token_type')}")
        
        if token_info.get("token_type") == "id_token":
            # JWT ID token - already has user info
            user_email = token_info.get("email")
            user_name = token_info.get("name")
            logger.info(f"🔍 DEBUG: ID token - email: {user_email}, name: {user_name}")
        elif token_info.get("token_type") == "access_token":
            # Access token - need to call Google API
            logger.info("🔍 DEBUG: Processing access token")
            user_info = await get_user_info_from_access_token(token_info.get("access_token"))
            if user_info:
                user_email = user_info.get("email")
                user_name = user_info.get("name")
                logger.info(f"🔍 DEBUG: Access token - email: {user_email}, name: {user_name}")
        
        if not user_email:
            logger.warning("🔍 DEBUG: No user email found in token, returning None")
            return None
        
        logger.info(f"🔍 DEBUG: About to lookup user in Redis with key: user:{user_email}")
        
        # Use email as the persistent key
        user_key = f"user:{user_email}"
        
        # Try to get existing user by email
        user_data_json = redis_client.get(user_key)
        logger.info(f"🔍 DEBUG: Redis lookup result: {user_data_json is not None}")
        
        if user_data_json:
            # User exists, update last_active and return
            user_data = json.loads(user_data_json)
            user_data["last_active"] = datetime.now().isoformat()
            
            # Store updated user data (no expiry for user profiles)
            redis_client.set(user_key, json.dumps(user_data))
            
            logger.info(f"Existing user found: {user_email}")
            logger.info(f"🔍 DEBUG: Returning existing user data: {user_data.get('user_id')}")
            return user_data
        
        # User doesn't exist, create new user
        # Check if user is admin
        is_admin = user_email == "dhyan.raj@gmail.com"
        
        # Create new user object
        user_data = {
            "user_id": f"user_{hashlib.sha256(user_email.encode()).hexdigest()[:8]}",
            "email": user_email,
            "name": user_name or user_email.split('@')[0],
            "admin": is_admin,
            "created_at": datetime.now().isoformat(),
            "last_active": datetime.now().isoformat(),
            "interview_count": 0,
            "current_setup": {
                "status": "initial"
            }
        }
        
        # Store user in Redis (no expiry for user profiles)
        redis_client.set(user_key, json.dumps(user_data))
        
        logger.info(f"New user created: {user_email} (admin: {is_admin})")
        return user_data
        
    except Exception as e:
        logger.error(f"🔍 DEBUG: Exception in get_or_create_user: {e}")
        import traceback
        logger.error(f"🔍 DEBUG: Traceback: {traceback.format_exc()}")
        return None

def update_user_data(email: str, updates: Dict[str, Any]) -> bool:
    """Update user data in Redis."""
    try:
        user_key = f"user:{email}"
        user_data_json = redis_client.get(user_key)
        
        if not user_data_json:
            logger.error(f"User not found for email: {email}")
            return False
        
        user_data = json.loads(user_data_json)
        user_data.update(updates)
        user_data["last_active"] = datetime.now().isoformat()
        
        redis_client.set(user_key, json.dumps(user_data))
        logger.info(f"Updated user data for: {email}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating user data: {e}")
        return False

def check_admin_access(request: Request) -> None:
    """Check if the authenticated user has admin privileges."""
    user_data = request.state.user
    if not user_data.get("admin", False):
        raise HTTPException(
            status_code=403, 
            detail="Admin access required"
        )

# Check if running in dev mode
DEV_MODE = os.getenv("DEV_MODE", "false").lower() == "true"

# Pydantic models
class InterviewStartRequest(BaseModel):
    role_id: str

class InterviewAnswerRequest(BaseModel):
    answer: str

class RoleCreateRequest(BaseModel):
    title: str
    description: str
    status: str = "open"  # open, closed, on_hold

class RoleResponse(BaseModel):
    role_id: str
    title: str
    description: str
    status: str
    created_at: str
    created_by: str

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check Redis connection
        redis_client.ping()
        
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

@app.get("/api/user/profile")
async def get_user_profile(request: Request):
    """Get user profile from authenticated user."""
    user_data = request.state.user
    bearer_token = request.state.bearer_token
    
    logger.info(f"🔥 USER PROFILE ENDPOINT CALLED - UPDATED LOG VERSION 2025-08-08 🔥 - User: {user_data.get('email')} - Token: {bearer_token[:20]}...")
    
    return {
        "message": "Authentication successful!",
        "user": user_data,
        "bearer_token": bearer_token,
        "dev_mode": DEV_MODE
    }

@app.get("/api/auth/test")
async def test_authentication(request: Request):
    """Test endpoint to show authentication details including bearer token."""
    user_data = request.state.user
    bearer_token = request.state.bearer_token
    
    logger.info(f"Auth test requested by user: {user_data.get('email')}")
    
    # Get session data from Redis if available
    session_data = None
    try:
        session_key = f"session:{bearer_token}"
        session_json = redis_client.get(session_key)
        if session_json:
            session_data = json.loads(session_json)
    except Exception as e:
        logger.error(f"Failed to get session data: {e}")
        session_data = {"error": str(e)}
    
    return {
        "message": "Authentication successful!",
        "user": user_data,
        "bearer_token": bearer_token,
        "session_data_from_redis": session_data,
        "dev_mode": DEV_MODE,
        "all_headers": dict(request.headers)
    }

@app.post("/api/interviews/start")
async def start_interview(
    request_data: InterviewStartRequest,
    request: Request
):
    """Initialize new interview session."""
    user_data = request.state.user
    user_id = user_data.get('user_id')
    user_email = user_data.get('email')
    
    logger.info(f"Starting interview for user: {user_email}, role: {request_data.role_id}")
    
    # 1. Check if user has uploaded resume
    if not user_data.get("resume"):
        raise HTTPException(
            status_code=400,
            detail="Please upload your resume before starting an interview"
        )
    
    # 2. Get role details from Redis
    role_data_json = redis_client.get(f"roles:{request_data.role_id}")
    if not role_data_json:
        raise HTTPException(
            status_code=404,
            detail="Role not found"
        )
    
    role_data = json.loads(role_data_json)
    
    # 3. Check for existing active interview session for this user
    user_session_key = f"user_interview:{user_id}"
    existing_session = redis_client.get(user_session_key)
    
    # Clean up any existing interview agent session to start fresh
    old_agent_session_key = f"interview_session:{user_id}"
    redis_client.delete(old_agent_session_key)
    logger.info(f"Cleaned up any existing interview agent session: {old_agent_session_key}")
    
    if existing_session:
        existing_data = json.loads(existing_session)
        
        # Check if it's for the same role and still active
        if (existing_data.get("role_id") == request_data.role_id and 
            existing_data.get("status") == "active"):
            raise HTTPException(
                status_code=409,
                detail="You already have an active interview session for this role"
            )
        
        # Mark old session as completed
        if existing_data.get("status") == "active":
            existing_data["status"] = "completed"
            existing_data["ended_at"] = datetime.now().isoformat()
            redis_client.setex(user_session_key, 3600, json.dumps(existing_data))
    
    # 4. Create new interview session via interview agent
    resume_content = user_data["resume"].get("extracted_text", "")
    role_description = f"Title: {role_data['title']}\nDescription: {role_data['description']}"
    
    # Generate unique session_id for each interview to avoid conversation history accumulation
    session_id = f"interview_{uuid.uuid4().hex[:12]}"
    
    try:
        # Call interview agent to create session and get first question
        interview_result = await call_interview_agent(
            "conduct_interview",
            {
                "resume_content": resume_content,
                "role_description": role_description,
                "user_session_id": session_id
                # Don't pass candidate_answer for initial question
            }
        )
        
        logger.info(f"Interview agent response: {interview_result}")
        
        if not interview_result or not interview_result.get("success"):
            error_msg = interview_result.get('error', 'Unknown error') if interview_result else 'No response from interview agent'
            logger.error(f"Interview agent failed: {error_msg}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to start interview: {error_msg}"
            )
        
        # 5. Store session metadata in Redis using user_id as key
        interview_data = {
            "session_id": session_id,
            "user_id": user_id,
            "user_email": user_email,
            "role_id": request_data.role_id,
            "role_title": role_data["title"],
            "role_description": role_data["description"],
            "duration_minutes": 5,  # 5 minute interview
            "started_at": datetime.now().isoformat(),
            "expires_at": (datetime.now().timestamp() + 300),  # 5 minutes from now
            "status": "active",
            "current_question": interview_result.get("question"),
            "question_metadata": interview_result.get("question_metadata", {}),
            "questions_asked": 1,
            "total_score": 0
        }
        
        # Store with 1 hour expiry (cleanup)
        redis_client.setex(user_session_key, 3600, json.dumps(interview_data))
        
        logger.info(f"Interview session created for user {user_id}, role {request_data.role_id}")
        
        return {
            "success": True,
            "session_id": session_id,
            "role": {
                "id": request_data.role_id,
                "title": role_data["title"],
                "description": role_data["description"]
            },
            "duration_minutes": 5,
            "expires_at": interview_data["expires_at"],
            "first_question": interview_result.get("question"),
            "question_metadata": interview_result.get("question_metadata", {}),
            "message": "Interview started successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start interview: {e}")
        raise HTTPException(status_code=500, detail="Failed to start interview")

async def generate_interview_response(user_id: str, user_email: str, candidate_answer: str):
    """Generate streaming response for interview answer."""
    try:
        # Send processing message
        yield f"data: {json.dumps({'type': 'processing', 'message': 'Analyzing your answer...', 'timestamp': datetime.now().isoformat()})}\n\n"
        
        # Get session data
        user_session_key = f"user_interview:{user_id}"
        session_data = redis_client.get(user_session_key)
        
        if not session_data:
            yield f"data: {json.dumps({'type': 'error', 'message': 'No active interview session found'})}\n\n"
            return
        
        interview_session = json.loads(session_data)
        
        # Check if session is expired
        current_time = datetime.now().timestamp()
        if interview_session.get("expires_at", 0) < current_time:
            # Mark session as completed
            interview_session["status"] = "completed"
            interview_session["ended_at"] = datetime.now().isoformat()
            redis_client.setex(user_session_key, 3600, json.dumps(interview_session))
            
            yield f"data: {json.dumps({'type': 'expired', 'message': 'Interview session has expired', 'timestamp': datetime.now().isoformat()})}\n\n"
            return
        
        # Get role and resume data
        resume_content = ""
        user_data_json = redis_client.get(f"user:{user_email}")
        if user_data_json:
            user_data = json.loads(user_data_json)
            resume_content = user_data.get("resume", {}).get("extracted_text", "")
        
        role_description = f"Title: {interview_session['role_title']}\nDescription: {interview_session['role_description']}"
        
        # Call interview agent with answer
        logger.info(f"Submitting answer for user {user_id}: {candidate_answer[:50]}...")
        
        interview_result = await call_interview_agent(
            "conduct_interview",
            {
                "resume_content": resume_content,
                "role_description": role_description,
                "user_session_id": user_id,
                "candidate_answer": candidate_answer
            }
        )
        
        if not interview_result or not interview_result.get("success"):
            error_msg = interview_result.get('error', 'Failed to process answer') if interview_result else 'No response from interview agent'
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
            return
        
        # Send evaluation feedback if available
        yield f"data: {json.dumps({'type': 'evaluation', 'message': 'Answer processed successfully', 'timestamp': datetime.now().isoformat()})}\n\n"
        
        # Check if we have a next question
        if interview_result.get("question"):
            # Update session data - increment questions_asked first
            interview_session["questions_asked"] = interview_session.get("questions_asked", 0) + 1
            interview_session["current_question"] = interview_result.get("question")
            interview_session["question_metadata"] = interview_result.get("question_metadata", {})
            interview_session["last_updated"] = datetime.now().isoformat()
            
            # Check if we should end the interview (time or question limit)
            if (current_time >= interview_session.get("expires_at", 0) or 
                interview_session["questions_asked"] >= 10):  # Max 10 questions
                
                interview_session["status"] = "completed"
                interview_session["ended_at"] = datetime.now().isoformat()
                redis_client.setex(user_session_key, 3600, json.dumps(interview_session))
                
                yield f"data: {json.dumps({'type': 'interview_complete', 'message': 'Interview completed', 'session_id': user_id, 'timestamp': datetime.now().isoformat()})}\n\n"
            else:
                # Store updated session
                redis_client.setex(user_session_key, 3600, json.dumps(interview_session))
                
                # Send next question with correct session info
                session_info = {
                    'total_questions': interview_session["questions_asked"],
                    'total_answers': interview_session["questions_asked"] - 1,  # One less than questions asked
                    'session_id': interview_session.get("session_id", user_id)
                }
                
                yield f"data: {json.dumps({'type': 'question', 'content': interview_result.get('question'), 'metadata': interview_result.get('question_metadata', {}), 'session_info': session_info, 'timestamp': datetime.now().isoformat()})}\n\n"
        else:
            # No more questions - end interview
            interview_session["status"] = "completed"
            interview_session["ended_at"] = datetime.now().isoformat()
            redis_client.setex(user_session_key, 3600, json.dumps(interview_session))
            
            yield f"data: {json.dumps({'type': 'interview_complete', 'message': 'Interview completed', 'session_id': user_id, 'timestamp': datetime.now().isoformat()})}\n\n"
        
        # Send completion marker
        yield f"data: {json.dumps({'type': 'complete'})}\n\n"
        
    except Exception as e:
        logger.error(f"Error in interview response generation: {e}")
        yield f"data: {json.dumps({'type': 'error', 'message': f'Server error: {str(e)}'})}\n\n"

@app.get("/api/interviews/status")
async def get_interview_status(request: Request):
    """Get current interview session status for the authenticated user."""
    user_data = request.state.user
    user_id = user_data.get('user_id')
    
    logger.info(f"Interview status requested by user: {user_data.get('email')}")
    
    # Check for existing active interview session
    user_session_key = f"user_interview:{user_id}"
    existing_session = redis_client.get(user_session_key)
    
    if not existing_session:
        return {
            "has_active_session": False,
            "status": "no_session"
        }
    
    session_data = json.loads(existing_session)
    
    if session_data.get("status") != "active":
        return {
            "has_active_session": False,
            "status": session_data.get("status", "unknown")
        }
    
    # User has an active session
    return {
        "has_active_session": True,
        "status": "active",
        "session_id": session_data.get("session_id", user_id),
        "role_id": session_data.get("role_id"),
        "started_at": session_data.get("started_at")
    }

@app.get("/api/interviews/current")
async def get_current_interview_question(request: Request):
    """Get the current question for the active interview session."""
    user_data = request.state.user
    user_id = user_data.get('user_id')
    user_email = user_data.get('email')
    
    logger.info(f"Current question requested by user: {user_email}")
    
    # Check for existing active interview session
    user_session_key = f"user_interview:{user_id}"
    existing_session = redis_client.get(user_session_key)
    
    if not existing_session:
        raise HTTPException(
            status_code=404,
            detail="No active interview session found"
        )
    
    session_data = json.loads(existing_session)
    
    if session_data.get("status") != "active":
        raise HTTPException(
            status_code=410,
            detail="Interview session is no longer active"
        )
    
    # Check if session is expired
    current_time = datetime.now().timestamp()
    if session_data.get("expires_at", 0) < current_time:
        # Mark as expired
        session_data["status"] = "expired"
        session_data["ended_at"] = datetime.now().isoformat()
        redis_client.setex(user_session_key, 3600, json.dumps(session_data))
        
        raise HTTPException(
            status_code=410,
            detail="Interview session has expired"
        )
    
    # Return current question and session info
    questions_asked = session_data.get("questions_asked", 1)
    return {
        "session_id": session_data.get("session_id", user_id),
        "current_question": session_data.get("current_question"),
        "question_metadata": session_data.get("question_metadata", {}),
        "questions_asked": questions_asked,
        "total_questions": questions_asked,  # Current question number
        "total_answers": questions_asked - 1,  # Answers submitted (one less than questions)
        "role_title": session_data.get("role_title"),
        "expires_at": session_data.get("expires_at"),
        "started_at": session_data.get("started_at"),
        "status": "active"
    }

@app.post("/api/interviews/answer")
async def submit_interview_answer(
    request_data: InterviewAnswerRequest,
    request: Request
):
    """Submit answer and get next question via Server-Sent Events stream."""
    user_data = request.state.user
    user_id = user_data.get('user_id')
    user_email = user_data.get('email')
    
    logger.info(f"Received answer from user: {user_email}")
    
    # Validate answer
    if not request_data.answer.strip():
        raise HTTPException(
            status_code=400,
            detail="Answer cannot be empty"
        )
    
    # Check if user has active interview session
    user_session_key = f"user_interview:{user_id}"
    existing_session = redis_client.get(user_session_key)
    
    if not existing_session:
        raise HTTPException(
            status_code=400,
            detail="No active interview session found. Please start an interview first."
        )
    
    session_data = json.loads(existing_session)
    
    # Check if session is still active
    if session_data.get("status") != "active":
        raise HTTPException(
            status_code=410,
            detail="Interview session is no longer active"
        )
    
    # Check if session is expired
    current_time = datetime.now().timestamp()
    if session_data.get("expires_at", 0) < current_time:
        # Mark as expired
        session_data["status"] = "expired"
        session_data["ended_at"] = datetime.now().isoformat()
        redis_client.setex(user_session_key, 3600, json.dumps(session_data))
        
        raise HTTPException(
            status_code=410,
            detail="Interview session has expired"
        )
    
    # Return streaming response
    return StreamingResponse(
        generate_interview_response(user_id, user_email, request_data.answer),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable NGINX buffering
        }
    )

@app.post("/api/user/upload-resume")
async def upload_user_resume(
    request: Request,
    file: UploadFile = File(...)
):
    """Upload and process user resume document."""
    user_data = request.state.user
    user_email = user_data.get('email')
    logger.info(f"Resume upload by user: {user_email}")
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400, 
            detail="Only PDF documents are supported"
        )
    
    # Validate file size (10MB limit)
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size must be less than 10MB"
        )
    
    # Read file content
    try:
        file_content = await file.read()
        logger.info(f"Resume uploaded: {file.filename} ({len(file_content)} bytes)")
    except Exception as e:
        logger.error(f"Failed to read uploaded file: {e}")
        raise HTTPException(status_code=400, detail="Failed to read uploaded file")
    
    # Generate unique file key for MinIO
    file_extension = file.filename.split('.')[-1].lower()
    unique_filename = f"resumes/{user_email}/{uuid.uuid4()}.{file_extension}"
    
    try:
        # Upload to MinIO
        logger.info(f"Uploading to MinIO: {unique_filename}")
        minio_client.put_object(
            bucket_name,
            unique_filename,
            BytesIO(file_content),
            length=len(file_content),
            content_type="application/pdf"
        )
        logger.info(f"Successfully uploaded to MinIO: {unique_filename}")
        
        # Call PDF extractor service via MCP using MinIO URL
        minio_url = f"http://minio:9000/{bucket_name}/{unique_filename}"
        logger.info(f"Calling PDF extractor service with MinIO URL: {minio_url}")
        extraction_result = await call_pdf_extractor(minio_url, file_content)
        logger.info(f"PDF extraction result keys: {extraction_result.keys() if extraction_result else 'None'}")
        if extraction_result:
            logger.info(f"Has structured_analysis: {'structured_analysis' in extraction_result}")
            logger.info(f"Has analysis_enhanced: {'analysis_enhanced' in extraction_result}")
        
        if not extraction_result:
            # For now, create a basic extraction result as fallback
            logger.warning("PDF extraction failed, creating fallback result")
            extraction_result = {
                "text": "PDF content extraction failed - using fallback",
                "structured_data": {
                    "filename": file.filename,
                    "pages": 1,
                    "status": "extraction_failed"
                },
                "metadata": {
                    "processing_time": 0,
                    "method": "fallback"
                }
            }
        
        # Update user data with resume information
        resume_data = {
            "resume": {
                "filename": file.filename,
                "minio_path": unique_filename,
                "size_bytes": len(file_content),
                "uploaded_at": datetime.now().isoformat(),
                "extracted_text": extraction_result.get("text_content", ""),
                "structured_data": extraction_result.get("sections", {}),
                "structured_analysis": extraction_result.get("structured_analysis", {}),
                "analysis_enhanced": extraction_result.get("analysis_enhanced", False),
                "extraction_metadata": {
                    "success": extraction_result.get("success", False),
                    "extraction_method": extraction_result.get("extraction_method", "unknown"),
                    "text_stats": extraction_result.get("text_stats", {}),
                    "summary": extraction_result.get("summary", "")
                }
            }
        }
        
        # Update user object in Redis
        success = update_user_data(user_email, resume_data)
        if not success:
            logger.error("Failed to update user data with resume information")
            raise HTTPException(status_code=500, detail="Failed to save resume data")
        
        return {
            "upload_success": True,
            "filename": file.filename,
            "minio_path": unique_filename,
            "extraction_result": extraction_result,
            "message": "Resume uploaded and processed successfully"
        }
        
    except S3Error as e:
        logger.error(f"MinIO upload error: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")
    except Exception as e:
        logger.error(f"Resume upload error: {e}")
        raise HTTPException(status_code=500, detail="Resume processing failed")

async def call_pdf_extractor(file_path: str, file_content: bytes) -> Optional[Dict[str, Any]]:
    """Call PDF extractor service via MCP using Server-Sent Events."""
    try:
        # MCP JSON-RPC payload following the examples format
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "extract_text_from_pdf",
                "arguments": {
                    "file_path": file_path,
                    "extraction_method": "auto"
                }
            }
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{PDF_EXTRACTOR_URL}/mcp/",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            ) as response:
                
                if response.status_code != 200:
                    logger.error(f"PDF extractor returned status {response.status_code}")
                    return None
                
                # Process Server-Sent Events stream
                response_data = None
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        try:
                            data = json.loads(data_str)
                            if "result" in data:
                                response_data = data["result"]
                                break
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse SSE data: {data_str}")
                            continue
                
                if not response_data:
                    logger.error("No valid response data received from PDF extractor")
                    return None
                
                # Extract content from MCP response
                if "content" in response_data and isinstance(response_data["content"], list):
                    content_list = response_data["content"]
                    if len(content_list) > 0:
                        content_item = content_list[0]
                        if "text" in content_item:
                            extracted_text = content_item["text"]
                            try:
                                # Try to parse as JSON if it's a string
                                if isinstance(extracted_text, str):
                                    return json.loads(extracted_text)
                                else:
                                    return extracted_text
                            except json.JSONDecodeError:
                                # If not JSON, return as plain text
                                return {
                                    "text": extracted_text,
                                    "structured_data": {},
                                    "metadata": {"extraction_method": "text_only"}
                                }
                
                logger.error(f"Unexpected response format: {response_data}")
                return None
                
    except Exception as e:
        logger.error(f"Error calling PDF extractor: {e}")
        return None

async def call_interview_agent(tool_name: str, arguments: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Call interview agent via MCP JSON-RPC."""
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST",
                f"{INTERVIEW_AGENT_URL}/mcp/",
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            ) as response:
                
                if response.status_code != 200:
                    logger.error(f"Interview agent returned status {response.status_code}")
                    return None
                
                # Process Server-Sent Events stream
                response_data = None
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix
                        try:
                            data = json.loads(data_str)
                            if "result" in data:
                                response_data = data["result"]
                                break
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse interview agent SSE data: {data_str}")
                            continue
                
                if not response_data:
                    logger.error("No valid response data received from interview agent")
                    return None
                
                # Handle MCP structured response format
                if "structuredContent" in response_data:
                    return response_data["structuredContent"]
                elif "content" in response_data and isinstance(response_data["content"], list):
                    # Try to parse content as JSON
                    content_list = response_data["content"]
                    if len(content_list) > 0 and "text" in content_list[0]:
                        try:
                            return json.loads(content_list[0]["text"])
                        except json.JSONDecodeError:
                            pass
                
                return response_data
                
    except Exception as e:
        logger.error(f"Error calling interview agent: {e}")
        return None

@app.get("/api/interviews/{interview_id}/status")
async def get_interview_status(
    interview_id: str,
    request: Request
):
    """Get current interview status."""
    user_data = request.state.user
    logger.info(f"Status check for interview {interview_id} by user: {user_data.get('email')}")
    
    try:
        session_data = redis_client.get(f"interview:{interview_id}")
        if not session_data:
            raise HTTPException(status_code=404, detail="Interview session not found")
        
        interview_data = json.loads(session_data)
        
        # Verify user owns this interview
        if interview_data.get("candidate_id") != user_data.get('user_id'):
            raise HTTPException(status_code=403, detail="Access denied")
        
        return interview_data
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid interview session data")
    except Exception as e:
        logger.error(f"Failed to get interview status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve interview status")

@app.websocket("/ws/interviews/{interview_id}")
async def interview_websocket(websocket: WebSocket, interview_id: str):
    """WebSocket for real-time interview communication."""
    await websocket.accept()
    logger.info(f"WebSocket connection established for interview: {interview_id}")
    
    # Get user context from headers (set by NGINX)
    user_id = websocket.headers.get("x-user-id")
    user_email = websocket.headers.get("x-user-email")
    
    if not user_id:
        logger.warning("WebSocket connection without user context")
        await websocket.close(code=4001)
        return
    
    try:
        # Send initial welcome message
        await websocket.send_text(json.dumps({
            "type": "welcome",
            "message": "Connected to AI Interviewer",
            "interview_id": interview_id,
            "timestamp": datetime.now().isoformat()
        }))
        
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                logger.info(f"WebSocket message from {user_email}: {message.get('type', 'unknown')}")
                
                # Handle different message types
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
                elif message.get("type") == "answer":
                    # TODO: Process answer through MCP Mesh services
                    # For now, send a mock response
                    await websocket.send_text(json.dumps({
                        "type": "question",
                        "content": "Thank you for your answer. Can you tell me more about your experience with distributed systems?",
                        "topic": "architecture",
                        "timestamp": datetime.now().isoformat(),
                        "evaluation": {
                            "score": 75,
                            "feedback": "Good technical understanding demonstrated"
                        }
                    }))
                    
                else:
                    # Unknown message type
                    await websocket.send_text(json.dumps({
                        "type": "error",
                        "message": f"Unknown message type: {message.get('type')}",
                        "timestamp": datetime.now().isoformat()
                    }))
                    
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON message format",
                    "timestamp": datetime.now().isoformat()
                }))
                
    except Exception as e:
        logger.error(f"WebSocket error for interview {interview_id}: {e}")
    finally:
        logger.info(f"WebSocket connection closed for interview: {interview_id}")

@app.get("/api/interviews/{interview_id}/results")
async def get_interview_results(
    interview_id: str,
    request: Request
):
    """Get final interview results and evaluation."""
    user_data = request.state.user
    logger.info(f"Results requested for interview {interview_id} by user: {user_data.get('email')}")
    
    # TODO: Call evaluation service for final assessment via MCP Mesh
    # For now, return mock results
    mock_results = {
        "interview_id": interview_id,
        "candidate_id": user_data.get('user_id'),
        "completed_at": datetime.now().isoformat(),
        "overall_score": 78,
        "recommendation": "Proceed to next round",
        "topic_scores": {
            "technical_skills": 82,
            "problem_solving": 75,
            "communication": 80,
            "system_design": 72
        },
        "strengths": [
            "Strong technical foundation",
            "Clear communication style",
            "Good problem-solving approach"
        ],
        "areas_for_improvement": [
            "System design scalability considerations",
            "More concrete examples from experience"
        ],
        "detailed_feedback": "The candidate demonstrated solid technical knowledge and problem-solving skills. Communication was clear and professional throughout the interview."
    }
    
    return mock_results

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

@app.post("/api/admin/roles")
async def create_role(
    role_data: RoleCreateRequest,
    request: Request
):
    """Create a new role. Admin access required."""
    logger.info("🔥 ROLE CREATION ENDPOINT REACHED! 🔥")
    check_admin_access(request)
    
    user_data = request.state.user
    logger.info(f"Role creation requested by admin: {user_data.get('email')}")
    
    # Validate status
    valid_statuses = ["open", "closed", "on_hold"]
    if role_data.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    # Generate unique role ID
    role_id = f"role_{uuid.uuid4().hex[:8]}"
    
    # Create role object
    role = {
        "role_id": role_id,
        "title": role_data.title,
        "description": role_data.description,
        "status": role_data.status,
        "created_at": datetime.now().isoformat(),
        "created_by": user_data.get("email"),
        "updated_at": datetime.now().isoformat(),
        "updated_by": user_data.get("email")
    }
    
    try:
        # Store role in Redis
        redis_client.set(f"roles:{role_id}", json.dumps(role))
        
        # Add role ID to roles index
        redis_client.sadd("roles:index", role_id)
        
        logger.info(f"Role created successfully: {role_id}")
        return RoleResponse(**role)
        
    except Exception as e:
        logger.error(f"Failed to create role: {e}")
        raise HTTPException(status_code=500, detail="Failed to create role")

@app.get("/api/roles")
async def get_roles(request: Request):
    """Get roles. Admins see all roles, regular users see only open roles."""
    user_data = request.state.user
    is_admin = user_data.get("admin", False)
    
    logger.info(f"Roles list requested by {'admin' if is_admin else 'user'}: {user_data.get('email')}")
    
    try:
        # Get all role IDs from index
        role_ids = redis_client.smembers("roles:index")
        
        if not role_ids:
            return {"roles": []}
        
        # Fetch all roles
        roles = []
        for role_id in role_ids:
            role_data_json = redis_client.get(f"roles:{role_id}")
            if role_data_json:
                role_data = json.loads(role_data_json)
                
                # Filter roles based on user type
                if is_admin or role_data.get("status") == "open":
                    roles.append(role_data)
        
        # Sort by creation date (newest first)
        roles.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        logger.info(f"Retrieved {len(roles)} roles for {'admin' if is_admin else 'user'}")
        return {
            "roles": roles,
            "user_type": "admin" if is_admin else "user",
            "total_roles": len(roles)
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve roles: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve roles")

@app.get("/api/admin/roles")
async def get_all_roles_admin(request: Request):
    """Get all roles (admin-only endpoint for backwards compatibility)."""
    check_admin_access(request)
    
    user_data = request.state.user
    logger.info(f"Admin roles list requested by: {user_data.get('email')}")
    
    try:
        # Get all role IDs from index
        role_ids = redis_client.smembers("roles:index")
        
        if not role_ids:
            return {"roles": []}
        
        # Fetch all roles
        roles = []
        for role_id in role_ids:
            role_data_json = redis_client.get(f"roles:{role_id}")
            if role_data_json:
                role_data = json.loads(role_data_json)
                roles.append(role_data)
        
        # Sort by creation date (newest first)
        roles.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        logger.info(f"Retrieved {len(roles)} roles for admin")
        return {"roles": roles}
        
    except Exception as e:
        logger.error(f"Failed to retrieve roles: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve roles")

@app.put("/api/admin/roles/{role_id}")
async def update_role(
    role_id: str,
    role_data: RoleCreateRequest,
    request: Request
):
    """Update an existing role. Admin access required."""
    check_admin_access(request)
    
    user_data = request.state.user
    logger.info(f"Role update requested by admin: {user_data.get('email')} for role: {role_id}")
    
    # Validate status
    valid_statuses = ["open", "closed", "on_hold"]
    if role_data.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
        )
    
    # Check if role exists
    existing_role_data = redis_client.get(f"roles:{role_id}")
    if not existing_role_data:
        raise HTTPException(status_code=404, detail="Role not found")
    
    existing_role = json.loads(existing_role_data)
    
    # Update role object
    updated_role = {
        "role_id": role_id,
        "title": role_data.title,
        "description": role_data.description,
        "status": role_data.status,
        "created_at": existing_role.get("created_at"),
        "created_by": existing_role.get("created_by"),
        "updated_at": datetime.now().isoformat(),
        "updated_by": user_data.get("email")
    }
    
    try:
        # Store updated role
        redis_client.set(f"roles:{role_id}", json.dumps(updated_role))
        
        logger.info(f"Role updated successfully: {role_id}")
        return {
            "success": True,
            "role": updated_role,
            "message": f"Role '{role_data.title}' updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to update role: {e}")
        raise HTTPException(status_code=500, detail="Failed to update role")

@app.delete("/api/admin/roles/{role_id}")
async def delete_role(role_id: str, request: Request):
    """Delete a role. Admin access required."""
    check_admin_access(request)
    
    user_data = request.state.user
    logger.info(f"Role deletion requested by admin: {user_data.get('email')} for role: {role_id}")
    
    # Check if role exists
    existing_role_data = redis_client.get(f"roles:{role_id}")
    if not existing_role_data:
        raise HTTPException(status_code=404, detail="Role not found")
    
    try:
        # Remove from index
        redis_client.srem("roles:index", role_id)
        
        # Delete role data
        redis_client.delete(f"roles:{role_id}")
        
        logger.info(f"Role deleted successfully: {role_id}")
        return {
            "success": True,
            "message": f"Role deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to delete role: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete role")

@app.get("/api/admin/users")
async def get_all_users(request: Request):
    """Get all users. Admin access required."""
    check_admin_access(request)
    
    user_data = request.state.user
    logger.info(f"Users list requested by admin: {user_data.get('email')}")
    
    try:
        # Get all user profile keys
        user_keys = []
        cursor = 0
        while True:
            cursor, keys = redis_client.scan(cursor, match="user_profile:*", count=100)
            user_keys.extend(keys)
            if cursor == 0:
                break
        
        users = []
        for user_key in user_keys:
            user_data_json = redis_client.get(user_key)
            if user_data_json:
                user_profile = json.loads(user_data_json)
                users.append(user_profile)
        
        # Sort by last_login (most recent first)
        users.sort(key=lambda x: x.get("last_login", ""), reverse=True)
        
        logger.info(f"Retrieved {len(users)} users for admin")
        return {"users": users}
        
    except Exception as e:
        logger.error(f"Failed to retrieve users: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve users")

@app.put("/api/admin/users/{user_id}")
async def update_user(
    user_id: str,
    user_update: dict,
    request: Request
):
    """Update user profile. Admin access required."""
    check_admin_access(request)
    
    admin_data = request.state.user
    logger.info(f"User update requested by admin: {admin_data.get('email')} for user: {user_id}")
    
    # Check if user exists
    user_profile_data = redis_client.get(f"user_profile:{user_id}")
    if not user_profile_data:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_profile = json.loads(user_profile_data)
    
    # Update allowed fields
    allowed_fields = ["admin", "blocked", "notes"]
    for field in allowed_fields:
        if field in user_update:
            user_profile[field] = user_update[field]
    
    user_profile["updated_at"] = datetime.now().isoformat()
    user_profile["updated_by"] = admin_data.get("email")
    
    try:
        # Store updated user profile
        redis_client.set(f"user_profile:{user_id}", json.dumps(user_profile))
        
        logger.info(f"User profile updated successfully: {user_id}")
        return {
            "success": True,
            "user": user_profile,
            "message": "User updated successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to update user: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")

@app.get("/api/admin/users/{user_id}/interviews")
async def get_user_interviews_admin(user_id: str, request: Request):
    """Get user's interview history. Admin access required."""
    check_admin_access(request)
    
    admin_data = request.state.user
    logger.info(f"User interviews requested by admin: {admin_data.get('email')} for user: {user_id}")
    
    try:
        # Get all interview keys for this user
        interview_keys = []
        cursor = 0
        while True:
            cursor, keys = redis_client.scan(cursor, match=f"user_interview:{user_id}*", count=100)
            interview_keys.extend(keys)
            if cursor == 0:
                break
        
        interviews = []
        for interview_key in interview_keys:
            interview_data_json = redis_client.get(interview_key)
            if interview_data_json:
                interview_data = json.loads(interview_data_json)
                interviews.append(interview_data)
        
        # Sort by started_at (most recent first)
        interviews.sort(key=lambda x: x.get("started_at", ""), reverse=True)
        
        logger.info(f"Retrieved {len(interviews)} interviews for user {user_id}")
        return {"interviews": interviews}
        
    except Exception as e:
        logger.error(f"Failed to retrieve user interviews: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve interviews")

@app.get("/api/admin/roles/{role_id}/candidates")
async def get_role_candidates(role_id: str, request: Request):
    """Get candidates who interviewed for a specific role. Admin access required."""
    check_admin_access(request)
    
    admin_data = request.state.user
    logger.info(f"Role candidates requested by admin: {admin_data.get('email')} for role: {role_id}")
    
    try:
        # Get all interview keys
        interview_keys = []
        cursor = 0
        while True:
            cursor, keys = redis_client.scan(cursor, match="user_interview:*", count=100)
            interview_keys.extend(keys)
            if cursor == 0:
                break
        
        candidates = []
        for interview_key in interview_keys:
            interview_data_json = redis_client.get(interview_key)
            if interview_data_json:
                interview_data = json.loads(interview_data_json)
                if interview_data.get("role_id") == role_id:
                    # Get user profile for additional info
                    user_profile_data = redis_client.get(f"user_profile:{interview_data.get('user_id')}")
                    user_profile = json.loads(user_profile_data) if user_profile_data else {}
                    
                    candidate_info = {
                        "user_id": interview_data.get("user_id"),
                        "user_email": interview_data.get("user_email"),
                        "user_name": user_profile.get("name", "Unknown"),
                        "interview_date": interview_data.get("started_at"),
                        "status": interview_data.get("status"),
                        "questions_asked": interview_data.get("questions_asked", 0),
                        "total_score": interview_data.get("total_score", 0),
                        "duration": interview_data.get("duration_minutes", 5),
                        "completed_at": interview_data.get("ended_at")
                    }
                    candidates.append(candidate_info)
        
        # Sort by interview date (most recent first)
        candidates.sort(key=lambda x: x.get("interview_date", ""), reverse=True)
        
        logger.info(f"Retrieved {len(candidates)} candidates for role {role_id}")
        return {"candidates": candidates}
        
    except Exception as e:
        logger.error(f"Failed to retrieve role candidates: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve candidates")

@app.post("/api/admin/users/{user_id}/reset-interview/{role_id}")
async def reset_user_interview(user_id: str, role_id: str, request: Request):
    """Allow user to retake an interview for a specific role. Admin access required."""
    check_admin_access(request)
    
    admin_data = request.state.user
    logger.info(f"Interview reset requested by admin: {admin_data.get('email')} for user: {user_id}, role: {role_id}")
    
    try:
        # Find and remove existing interview session for this user and role
        user_session_key = f"user_interview:{user_id}"
        existing_session = redis_client.get(user_session_key)
        
        if existing_session:
            session_data = json.loads(existing_session)
            if session_data.get("role_id") == role_id:
                # Remove the existing session
                redis_client.delete(user_session_key)
                logger.info(f"Removed existing interview session for user {user_id} and role {role_id}")
        
        # Clean up any interview agent session
        old_agent_session_key = f"interview_session:{user_id}"
        redis_client.delete(old_agent_session_key)
        
        logger.info(f"Interview reset successful for user {user_id} and role {role_id}")
        return {
            "success": True,
            "message": f"User can now retake the interview for this role"
        }
        
    except Exception as e:
        logger.error(f"Failed to reset interview: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset interview")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)