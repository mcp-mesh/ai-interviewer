#!/usr/bin/env python3
"""
Application Agent - MCP Mesh Agent for Application Management

Handles all application-related operations with static mock data matching frontend expectations.
Phase 2A implementation with capabilities: application_submit, applications_user_list, application_status_update
"""

import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

import mesh
from fastmcp import FastMCP
from mesh.types import McpAgent

# Create FastMCP app instance
app = FastMCP("Application Management Agent")

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Static Mock Data - Matching frontend/src/lib/mock-data.ts
STATIC_APPLICATIONS = [
    {
        "id": "app-1",
        "userId": "user-1",
        "jobId": "1",
        "status": "submitted",
        "submittedAt": "2024-03-02T14:00:00Z",
        "notes": "I am excited to apply for the Senior Frontend Developer position..."
    },
    {
        "id": "app-2", 
        "userId": "user-1",
        "jobId": "2",
        "status": "under-review",
        "submittedAt": "2024-03-01T10:30:00Z",
        "notes": "Looking forward to contributing to your startup..."
    }
]

# Additional complete applications for better testing
EXTENDED_APPLICATIONS = [
    {
        "id": "app-3",
        "userId": "user-1", 
        "jobId": "3",
        "status": "interview_scheduled",
        "submittedAt": "2024-02-28T16:30:00Z",
        "notes": "I would love to join your backend team...",
        "interview_date": "2024-03-05T10:00:00Z"
    },
    {
        "id": "app-4",
        "userId": "user-1",
        "jobId": "4", 
        "status": "rejected",
        "submittedAt": "2024-02-25T09:15:00Z",
        "notes": "My DevOps experience aligns perfectly with your needs...",
        "rejection_reason": "Position filled by another candidate"
    }
]

# Combine all applications
ALL_APPLICATIONS = STATIC_APPLICATIONS + EXTENDED_APPLICATIONS


@app.tool()
@mesh.tool(
    capability="application_submit",
    tags=["application-management", "submission", "workflow"],
    description="Submit a new job application"
)
def application_submit(
    user_email: str,
    job_id: str,
    application_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Submit a new job application.
    
    Args:
        user_email: User's email address
        job_id: Job ID to apply for
        application_data: Application details (notes, cover letter, etc.)
        
    Returns:
        Dict with application details and success status
    """
    try:
        logger.info(f"Submitting application for user {user_email} to job {job_id}")
        
        # Generate new application ID
        app_id = f"app-{uuid.uuid4().hex[:8]}"
        
        # Create new application
        new_application = {
            "id": app_id,
            "userId": user_email,  # Using email as user ID for simplicity
            "jobId": job_id,
            "status": "submitted",
            "submittedAt": datetime.utcnow().isoformat() + "Z",
            "notes": application_data.get("notes", ""),
            "cover_letter": application_data.get("cover_letter", ""),
            "resume_url": application_data.get("resume_url", ""),
            "additional_info": application_data.get("additional_info", {})
        }
        
        # In a real system, this would be saved to database
        # For now, we'll just return the created application
        
        result = {
            "application": new_application,
            "success": True,
            "message": "Application submitted successfully"
        }
        
        logger.info(f"Application {app_id} submitted successfully for job {job_id}")
        return result
        
    except Exception as e:
        logger.error(f"Error in application_submit: {str(e)}")
        return {"success": False, "error": str(e)}


@app.tool()
@mesh.tool(
    capability="applications_user_list",
    tags=["application-management", "listing", "user-specific"],
    description="Get all applications for a specific user"
)
def applications_user_list(
    user_email: str,
    page: int = 1,
    limit: int = 20,
    status_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get all applications for a specific user.
    
    Args:
        user_email: User's email address
        page: Page number for pagination
        limit: Number of applications per page
        status_filter: Optional status filter ("submitted", "under-review", "interview_scheduled", "rejected")
        
    Returns:
        Dict with user's applications list and metadata
    """
    try:
        logger.info(f"Getting applications for user {user_email}, page {page}, limit {limit}")
        
        # Filter applications by user (using email as user ID)
        user_applications = [app for app in ALL_APPLICATIONS if app["userId"] == user_email]
        
        # Apply status filter if provided
        if status_filter:
            user_applications = [app for app in user_applications if app["status"] == status_filter]
        
        total_applications = len(user_applications)
        
        # Apply pagination
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        paginated_applications = user_applications[start_idx:end_idx]
        
        result = {
            "applications": paginated_applications,
            "total": total_applications,
            "page": page,
            "limit": limit,
            "success": True
        }
        
        logger.info(f"Returning {len(paginated_applications)} applications for user {user_email}")
        return result
        
    except Exception as e:
        logger.error(f"Error in applications_user_list: {str(e)}")
        return {"applications": [], "total": 0, "page": page, "limit": limit, "error": str(e)}


@app.tool()
@mesh.tool(
    capability="application_status_update",
    tags=["application-management", "status", "workflow"],
    description="Update application status"
)
def application_status_update(
    application_id: str,
    new_status: str,
    admin_notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update the status of an application.
    
    Args:
        application_id: Application ID to update
        new_status: New status ("submitted", "under-review", "interview_scheduled", "rejected", "hired")
        admin_notes: Optional admin notes about the status change
        
    Returns:
        Dict with updated application details
    """
    try:
        logger.info(f"Updating application {application_id} status to {new_status}")
        
        # Find application (in real system, this would be a database update)
        application = None
        for app in ALL_APPLICATIONS:
            if app["id"] == application_id:
                application = app.copy()
                break
        
        if not application:
            logger.warning(f"Application not found: {application_id}")
            return {"success": False, "error": f"Application {application_id} not found"}
        
        # Update status
        application["status"] = new_status
        application["status_updated_at"] = datetime.utcnow().isoformat() + "Z"
        
        if admin_notes:
            application["admin_notes"] = admin_notes
        
        # Add status-specific fields
        if new_status == "interview_scheduled":
            application["interview_date"] = (datetime.utcnow()).isoformat() + "Z"  # Mock future date
        elif new_status == "rejected" and not admin_notes:
            application["rejection_reason"] = "Position filled by another candidate"
        
        result = {
            "application": application,
            "success": True,
            "message": f"Application status updated to {new_status}"
        }
        
        logger.info(f"Application {application_id} status updated to {new_status}")
        return result
        
    except Exception as e:
        logger.error(f"Error in application_status_update: {str(e)}")
        return {"success": False, "error": str(e)}


# Agent class definition - MCP Mesh pattern
@mesh.agent(
    name="application-agent",
    auto_run=True
)
class ApplicationAgent(McpAgent):
    """
    Application Agent for AI Interviewer Phase 2
    
    Handles all application-related operations with static mock data.
    Capabilities: application_submit, applications_user_list, application_status_update
    """
    
    def __init__(self):
        logger.info("🚀 Initializing Application Agent v2.0")
        logger.info(f"📋 Loaded {len(ALL_APPLICATIONS)} applications")
        logger.info("✅ Application Agent ready to serve requests")


if __name__ == "__main__":
    logger.info("Application Agent starting...")