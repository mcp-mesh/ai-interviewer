"""
JWT token parsing utilities for extracting user information from OAuth tokens.
"""

import logging
from typing import Optional, Dict, Any
import jwt

logger = logging.getLogger(__name__)


def parse_oauth_jwt_token(bearer_token: str) -> Optional[Dict[str, Any]]:
    """
    Parse OAuth JWT token to extract user info (without signature verification).
    
    nginx sets this token after OAuth flow, containing user's email, name, etc.
    We don't verify signature since nginx already validated it during OAuth.
    """
    try:
        # Decode JWT without signature verification
        payload = jwt.decode(bearer_token, options={"verify_signature": False})
        
        logger.info(f"Parsed JWT token for user: {payload.get('email', 'unknown')} from provider: {payload.get('provider', 'unknown')}")
        
        # Extract user information from JWT payload
        user_info = {
            "email": payload.get("email"),
            "name": payload.get("name"),
            "given_name": payload.get("given_name"),
            "family_name": payload.get("family_name"),
            "provider": payload.get("provider", "unknown"),
            "sub": payload.get("sub")
        }
        
        # Parse first_name and last_name from name or given_name/family_name
        if user_info.get("given_name") and user_info.get("family_name"):
            user_info["first_name"] = user_info["given_name"]
            user_info["last_name"] = user_info["family_name"]
        elif user_info.get("name"):
            name_parts = user_info["name"].split()
            user_info["first_name"] = name_parts[0] if name_parts else ""
            user_info["last_name"] = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""
        else:
            user_info["first_name"] = ""
            user_info["last_name"] = ""
            
        return user_info
        
    except jwt.DecodeError as e:
        logger.error(f"Failed to decode JWT token: {e}")
        return None
    except Exception as e:
        logger.error(f"Error parsing OAuth JWT token: {e}")
        return None


def extract_user_from_request_headers(authorization_header: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Extract user information from Authorization header containing Bearer JWT token.
    
    Args:
        authorization_header: The Authorization header value
        
    Returns:
        Dict containing user info (email, first_name, last_name) or None if invalid
    """
    if not authorization_header or not authorization_header.startswith("Bearer "):
        logger.warning("No valid Authorization header found")
        return None
        
    bearer_token = authorization_header[7:]  # Remove "Bearer " prefix
    
    return parse_oauth_jwt_token(bearer_token)


def get_optional_user_from_request(request) -> Optional[Dict[str, Any]]:
    """
    Extract user info if valid token exists, return None if no token (for unprotected routes).
    Only raises HTTPException if token exists but is invalid.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Dict containing user info or None if no token provided
        
    Raises:
        HTTPException: 401 if token exists but is invalid
    """
    from fastapi import HTTPException
    
    auth_header = request.headers.get("Authorization")
    
    # No token provided - OK for unprotected routes
    if not auth_header or auth_header.strip() == "Bearer" or auth_header.strip() == "Bearer ":
        logger.info("No authentication token provided - proceeding as unauthenticated user")
        return None
        
    # Token provided - must be valid
    user_info = extract_user_from_request_headers(auth_header)
    if not user_info:
        logger.error("Invalid authentication token provided")
        raise HTTPException(status_code=401, detail="Invalid authentication token")
        
    logger.info(f"Valid authentication token found for user: {user_info.get('email', 'unknown')}")
    return user_info


def require_user_from_request(request) -> Dict[str, Any]:
    """
    Extract user info and require valid authentication (for protected routes).
    Always raises HTTPException if no valid token.
    
    Args:
        request: FastAPI Request object
        
    Returns:
        Dict containing user info
        
    Raises:
        HTTPException: 401 if no valid token provided
    """
    from fastapi import HTTPException
    
    user_info = get_optional_user_from_request(request)
    if not user_info:
        logger.error("Authentication required but no valid token provided")
        raise HTTPException(status_code=401, detail="Authentication required")
    return user_info