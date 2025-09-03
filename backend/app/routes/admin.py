"""
Phase 2 Backend - Admin API Routes

Admin functionality for user and job management.
All routes require admin authentication.
"""

import logging
from typing import Optional

import mesh
from fastapi import APIRouter, HTTPException, Request
from mesh.types import McpMeshAgent

from app.models.schemas import (
    AdminUsersResponse,
    AdminUserUpdate,
    AdminUserUpdateResponse,
    AdminJobsResponse,
    AdminJobCreate,
    AdminJobCreateResponse,
    AdminJobUpdate,
    AdminJobUpdateResponse,
    AdminJobDeleteResponse,
    AdminJobDetailsResponse,
    AdminJobDetailsInterview,
    AdminJobDetailsStatistics,
    ErrorResponse
)
from app.utils.admin import require_admin_user, format_admin_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=AdminUsersResponse)
@mesh.route(dependencies=["user_profile_get", "user_list_all"])
async def get_admin_users(
    request: Request,
    user_profile_agent: McpMeshAgent = None,
    user_list_agent: McpMeshAgent = None
) -> AdminUsersResponse:
    """
    Get all users for admin management.
    
    Requires admin authentication.
    Delegates to user_agent's user_list_all capability.
    """
    try:
        # Verify admin privileges
        admin_user = await require_admin_user(request, user_profile_agent)
        
        logger.info(f"Admin user {admin_user['email']} requesting user list")
        
        # Get all users from user agent
        result = await user_list_agent()
        
        if not result.get("success"):
            error_msg = result.get("error", "Failed to retrieve users")
            logger.error(f"Failed to get users list: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        users_data = result.get("users", [])
        total_count = result.get("total_count", len(users_data))
        
        # Format users for admin response
        formatted_users = [format_admin_user(user) for user in users_data]
        
        logger.info(f"Retrieved {total_count} users for admin: {admin_user['email']}")
        
        return AdminUsersResponse(
            data=formatted_users,
            total_count=total_count,
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve admin users: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve users: {str(e)}")


@router.put("/users/{user_email}", response_model=AdminUserUpdateResponse)
@mesh.route(dependencies=["user_profile_get", "user_admin_update"])
async def update_admin_user(
    user_email: str,
    user_update: AdminUserUpdate,
    request: Request,
    user_profile_agent: McpMeshAgent = None,
    user_admin_agent: McpMeshAgent = None
) -> AdminUserUpdateResponse:
    """
    Update user admin status, blocked status, and admin notes.
    
    Requires admin authentication.
    Delegates to user_agent's user_admin_update capability.
    """
    try:
        # Verify admin privileges
        admin_user = await require_admin_user(request, user_profile_agent)
        
        logger.info(f"Admin user {admin_user['email']} updating user: {user_email}")
        
        # Prepare update parameters
        update_params = {"user_email": user_email}
        
        # Map frontend field names to user agent parameters
        if user_update.admin is not None:
            update_params["is_admin"] = user_update.admin
            
        if user_update.notes is not None:
            update_params["notes"] = user_update.notes
            
        # Note: The backup frontend sends 'blocked' field, but the user agent doesn't 
        # currently support a blocked status. We'll log this for future implementation.
        if user_update.blocked is not None:
            logger.warning(f"Blocked status update requested but not yet implemented: {user_update.blocked}")
        
        # Call user agent to update user
        result = await user_admin_agent(**update_params)
        
        if not result.get("success"):
            error_msg = result.get("error", "Failed to update user")
            logger.error(f"Failed to update user {user_email}: {error_msg}")
            
            if "not found" in error_msg.lower():
                raise HTTPException(status_code=404, detail=error_msg)
            else:
                raise HTTPException(status_code=500, detail=error_msg)
        
        updated_user = result.get("user", {})
        
        # Format user for admin response
        formatted_user = format_admin_user(updated_user)
        
        logger.info(f"Successfully updated user {user_email} by admin {admin_user['email']}")
        
        return AdminUserUpdateResponse(
            data=formatted_user,
            success=True,
            message=f"User {user_email} updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user {user_email}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")


@router.get("/jobs", response_model=AdminJobsResponse)
@mesh.route(dependencies=["user_profile_get", "jobs_all_listing"])
async def get_admin_jobs(
    request: Request,
    page: int = 1,
    limit: int = 20,
    status: Optional[str] = None,
    user_profile_agent: McpMeshAgent = None,
    job_agent: McpMeshAgent = None
) -> AdminJobsResponse:
    """
    Get all jobs for admin management with pagination.
    
    Requires admin authentication.
    Delegates to job_agent's jobs_all_listing capability.
    """
    try:
        # Verify admin privileges
        admin_user = await require_admin_user(request, user_profile_agent)
        
        logger.info(f"Admin user {admin_user['email']} requesting jobs list - page {page}, limit {limit}, status: {status}")
        
        # Get all jobs from job agent with pagination
        result = await job_agent(page=page, limit=limit)
        
        if not result.get("jobs"):
            error_msg = "Failed to retrieve jobs from job agent"
            logger.error(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
        
        jobs_data = result.get("jobs", [])
        total_count = result.get("total", len(jobs_data))
        
        # Filter by status if specified (since job agent doesn't support status filtering yet)
        if status:
            jobs_data = [job for job in jobs_data if job.get("status") == status]
            total_count = len(jobs_data)
        
        logger.info(f"Retrieved {len(jobs_data)} jobs (total: {total_count}) for admin: {admin_user['email']}")
        
        return AdminJobsResponse(
            data=jobs_data,
            total=total_count,
            page=page,
            limit=limit,
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve admin jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve jobs: {str(e)}")


@router.post("/jobs", response_model=AdminJobCreateResponse)
@mesh.route(dependencies=["user_profile_get", "job_create"])
async def create_admin_job(
    job_create: AdminJobCreate,
    request: Request,
    user_profile_agent: McpMeshAgent = None,
    job_create_agent: McpMeshAgent = None
) -> AdminJobCreateResponse:
    """
    Create a new job posting.
    
    Requires admin authentication.
    Delegates to job_agent's job_create capability.
    """
    try:
        # Verify admin privileges
        admin_user = await require_admin_user(request, user_profile_agent)
        
        logger.info(f"Admin user {admin_user['email']} creating job: {job_create.title}")
        
        # Prepare job creation parameters
        create_params = {
            "title": job_create.title,
            "description": job_create.description,
            "status": job_create.status,
            "interview_duration_minutes": job_create.duration,
            "created_by": admin_user['email']
        }
        
        # Add optional fields if provided
        if job_create.company:
            create_params["company"] = job_create.company
        if job_create.location:
            create_params["location"] = job_create.location
        if job_create.city:
            create_params["city"] = job_create.city
        if job_create.state:
            create_params["state"] = job_create.state
        if job_create.country:
            create_params["country"] = job_create.country
        if job_create.job_type:
            create_params["job_type"] = job_create.job_type
        if job_create.category:
            create_params["category"] = job_create.category
        if job_create.experience_level:
            create_params["experience_level"] = job_create.experience_level
        if job_create.requirements:
            create_params["requirements"] = job_create.requirements
        if job_create.benefits:
            create_params["benefits"] = job_create.benefits
        if job_create.salary_min is not None:
            create_params["salary_min"] = job_create.salary_min
        if job_create.salary_max is not None:
            create_params["salary_max"] = job_create.salary_max
        if job_create.salary_currency:
            create_params["salary_currency"] = job_create.salary_currency
        if job_create.remote is not None:
            create_params["remote"] = job_create.remote
        
        # Call job agent to create job
        result = await job_create_agent(**create_params)
        
        if not result.get("success"):
            error_msg = result.get("error", "Failed to create job")
            logger.error(f"Failed to create job: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        created_job = result.get("job", {})
        
        logger.info(f"Successfully created job {created_job.get('id', 'N/A')} by admin {admin_user['email']}")
        
        return AdminJobCreateResponse(
            data=created_job,
            success=True,
            message=f"Job '{job_create.title}' created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create job: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create job: {str(e)}")


@router.put("/jobs/{job_id}", response_model=AdminJobUpdateResponse)
@mesh.route(dependencies=["user_profile_get", "job_update"])
async def update_admin_job(
    job_id: str,
    job_update: AdminJobUpdate,
    request: Request,
    user_profile_agent: McpMeshAgent = None,
    job_update_agent: McpMeshAgent = None
) -> AdminJobUpdateResponse:
    """
    Update an existing job posting.
    
    Requires admin authentication.
    Delegates to job_agent's job_update capability.
    """
    try:
        # Verify admin privileges
        admin_user = await require_admin_user(request, user_profile_agent)
        
        logger.info(f"Admin user {admin_user['email']} updating job: {job_id}")
        
        # Prepare update parameters - only include fields that are being updated
        update_params = {
            "job_id": job_id,
            "updated_by": admin_user['email']
        }
        
        # Add fields that are being updated
        if job_update.title is not None:
            update_params["title"] = job_update.title
        if job_update.description is not None:
            update_params["description"] = job_update.description
        if job_update.status is not None:
            update_params["status"] = job_update.status
        if job_update.duration is not None:
            update_params["interview_duration_minutes"] = job_update.duration
        if job_update.company is not None:
            update_params["company"] = job_update.company
        if job_update.location is not None:
            update_params["location"] = job_update.location
        if job_update.city is not None:
            update_params["city"] = job_update.city
        if job_update.state is not None:
            update_params["state"] = job_update.state
        if job_update.country is not None:
            update_params["country"] = job_update.country
        if job_update.job_type is not None:
            update_params["job_type"] = job_update.job_type
        if job_update.category is not None:
            update_params["category"] = job_update.category
        if job_update.experience_level is not None:
            update_params["experience_level"] = job_update.experience_level
        if job_update.requirements is not None:
            update_params["requirements"] = job_update.requirements
        if job_update.benefits is not None:
            update_params["benefits"] = job_update.benefits
        if job_update.salary_min is not None:
            update_params["salary_min"] = job_update.salary_min
        if job_update.salary_max is not None:
            update_params["salary_max"] = job_update.salary_max
        if job_update.salary_currency is not None:
            update_params["salary_currency"] = job_update.salary_currency
        if job_update.remote is not None:
            update_params["remote"] = job_update.remote
        
        # Call job agent to update job
        result = await job_update_agent(**update_params)
        
        if not result.get("success"):
            error_msg = result.get("error", "Failed to update job")
            logger.error(f"Failed to update job {job_id}: {error_msg}")
            
            if "not found" in error_msg.lower():
                raise HTTPException(status_code=404, detail=error_msg)
            else:
                raise HTTPException(status_code=500, detail=error_msg)
        
        updated_job = result.get("job", {})
        
        logger.info(f"Successfully updated job {job_id} by admin {admin_user['email']}")
        
        return AdminJobUpdateResponse(
            data=updated_job,
            success=True,
            message=f"Job {job_id} updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update job: {str(e)}")


@router.delete("/jobs/{job_id}", response_model=AdminJobDeleteResponse)
@mesh.route(dependencies=["user_profile_get", "job_delete"])
async def delete_admin_job(
    job_id: str,
    request: Request,
    user_profile_agent: McpMeshAgent = None,
    job_delete_agent: McpMeshAgent = None
) -> AdminJobDeleteResponse:
    """
    Delete a job posting (soft delete).
    
    Requires admin authentication.
    Delegates to job_agent's job_delete capability.
    """
    try:
        # Verify admin privileges
        admin_user = await require_admin_user(request, user_profile_agent)
        
        logger.info(f"Admin user {admin_user['email']} deleting job: {job_id}")
        
        # Call job agent to delete job
        result = await job_delete_agent(
            job_id=job_id,
            deleted_by=admin_user['email']
        )
        
        if not result.get("success"):
            error_msg = result.get("error", "Failed to delete job")
            logger.error(f"Failed to delete job {job_id}: {error_msg}")
            
            if "not found" in error_msg.lower():
                raise HTTPException(status_code=404, detail=error_msg)
            else:
                raise HTTPException(status_code=500, detail=error_msg)
        
        logger.info(f"Successfully deleted job {job_id} by admin {admin_user['email']}")
        
        return AdminJobDeleteResponse(
            success=True,
            message=f"Job {job_id} deleted successfully",
            job_id=job_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")


@router.get("/jobs/{job_id}", response_model=AdminJobDetailsResponse)
@mesh.route(dependencies=["user_profile_get", "job_details_get", "get_job_interviews"])
async def get_admin_job_details(
    job_id: str,
    request: Request,
    user_profile_agent: McpMeshAgent = None,
    job_details_agent: McpMeshAgent = None,
    interview_agent: McpMeshAgent = None
) -> AdminJobDetailsResponse:
    """
    Get detailed job information with interview statistics for admin.
    
    Requires admin authentication.
    Returns job details, all completed interviews, and statistics.
    """
    try:
        # Verify admin privileges
        admin_user = await require_admin_user(request, user_profile_agent)
        
        logger.info(f"Admin user {admin_user['email']} requesting details for job {job_id}")
        
        # Get job details from job agent
        job_result = await job_details_agent(job_id=job_id)
        
        if not job_result:
            error_msg = "Failed to get job data - no response from job agent"
            logger.error(f"Failed to get job {job_id}: {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Check if job agent returned an error
        if job_result.get("isError") or "error" in job_result:
            error_msg = job_result.get("error", "Job not found")
            logger.error(f"Job agent returned error for {job_id}: {error_msg}")
            
            # Return 404 if job not found
            if "not found" in error_msg.lower():
                raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
            else:
                raise HTTPException(status_code=500, detail=error_msg)
        
        # Extract job data from the MCP response format
        # For MCP Mesh, the response can come in different formats:
        # 1. Direct response (job data at root level)
        # 2. Wrapped response with "structuredContent" 
        # 3. Content array format
        
        logger.debug(f"Job result keys: {list(job_result.keys())}")
        
        # Check if this is a direct job response (has 'id' field)
        if 'id' in job_result and job_result.get('id') == job_id:
            job_data = job_result
            logger.debug("Using direct job response format")
        else:
            # Try structured content format  
            job_data = job_result.get("structuredContent", {})
            logger.debug(f"structuredContent data: {bool(job_data)}")
            
            if not job_data:
                # Fallback to checking content array
                content = job_result.get("content", [])
                logger.debug(f"Content array length: {len(content)}")
                if content and len(content) > 0:
                    # Try to parse JSON from text content
                    import json
                    try:
                        text_content = content[0].get("text", "{}")
                        logger.debug(f"Text content length: {len(text_content)}")
                        job_data = json.loads(text_content)
                        logger.debug(f"Parsed job data successfully: {bool(job_data)}")
                    except Exception as e:
                        logger.error(f"Failed to parse JSON from text content: {e}")
                        job_data = {}
        
        logger.debug(f"Final job_data: {bool(job_data)} with id: {job_data.get('id') if job_data else 'None'}")
        
        if not job_data or not job_data.get('id'):
            logger.error(f"No valid job data found in response for {job_id}")
            logger.error(f"Full job_result keys: {list(job_result.keys())}")
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        logger.info(f"Retrieved job details for {job_id}: {job_data.get('title', 'Unknown Title')}")
        
        # Get all completed interviews for this job from interview agent
        interviews_result = await interview_agent(job_id=job_id)
        
        if not interviews_result or not interviews_result.get("success"):
            error_msg = interviews_result.get("error", "Failed to get interviews") if interviews_result else "No interview data"
            logger.warning(f"Failed to get interviews for job {job_id}: {error_msg}")
            
            # Continue with empty interviews if interview agent fails
            interviews_data = []
            statistics_data = AdminJobDetailsStatistics()
        else:
            interviews_raw = interviews_result.get("interviews", [])
            statistics_raw = interviews_result.get("statistics", {})
            
            logger.info(f"Retrieved {len(interviews_raw)} interviews for job {job_id}")
            
            # Transform interviews to response format
            interviews_data = []
            for interview in interviews_raw:
                interview_obj = AdminJobDetailsInterview(
                    session_id=interview.get("session_id", ""),
                    candidate_name=interview.get("candidate_name", "Unknown"),
                    candidate_email=interview.get("candidate_email", ""),
                    interview_date=interview.get("interview_date"),
                    overall_score=interview.get("overall_score"),
                    technical_knowledge=interview.get("technical_knowledge"),
                    problem_solving=interview.get("problem_solving"),
                    communication=interview.get("communication"),
                    experience_relevance=interview.get("experience_relevance"),
                    hire_recommendation=interview.get("hire_recommendation", "not_evaluated"),
                    feedback=interview.get("feedback", ""),
                    completion_reason=interview.get("completion_reason"),
                    ended_at=interview.get("ended_at"),
                    duration=interview.get("duration"),
                    duration_minutes=interview.get("duration_minutes"),
                    questions_asked=interview.get("questions_asked"),
                    questions_answered=interview.get("questions_answered")
                )
                interviews_data.append(interview_obj)
            
            # Transform statistics to response format
            statistics_data = AdminJobDetailsStatistics(
                total_interviews=statistics_raw.get("total_interviews", 0),
                average_score=statistics_raw.get("average_score", 0.0),
                strong_yes_count=statistics_raw.get("strong_yes_count", 0),
                yes_count=statistics_raw.get("yes_count", 0),
                hire_rate=statistics_raw.get("hire_rate", 0.0)
            )
        
        logger.info(f"Returning job details for {job_id} with {len(interviews_data)} interviews to admin {admin_user['email']}")
        
        return AdminJobDetailsResponse(
            success=True,
            job=job_data,
            interviews=interviews_data,
            statistics=statistics_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get admin job details for {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get job details: {str(e)}")