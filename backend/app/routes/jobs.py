"""
Phase 2 Backend - Jobs API Routes

Clean delegation to job_agent via MCP Mesh dependency injection.
No authentication checks for testing phase.
"""

import logging
from typing import Optional

import mesh
from fastapi import APIRouter, HTTPException, Depends
from mesh.types import McpMeshAgent

from app.models.schemas import (
    JobListResponse, 
    JobDetailResponse, 
    JobCategoriesResponse,
    JobFilters,
    ErrorResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=JobListResponse)
@mesh.route(dependencies=["jobs_all_listing"])
async def list_jobs(
    category: Optional[str] = None,
    location: Optional[str] = None,
    experience_level: Optional[str] = None,
    job_type: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    job_agent: McpMeshAgent = None
) -> JobListResponse:
    """
    List all available jobs with optional filtering.
    
    Delegates to job_agent's jobs_all_listing capability.
    """
    try:
        logger.info(f"Listing jobs - page {page}, limit {limit}, category: {category}")
        
        # Build filters
        filters = {}
        if category:
            filters["category"] = category
        if location:
            filters["location"] = location  
        if experience_level:
            filters["experience_level"] = experience_level
        if job_type:
            filters["job_type"] = job_type
        
        # Delegate to job agent
        result = await job_agent(
            filters=filters,
            page=page,
            limit=limit
        )
        
        logger.info(f"Job agent returned {len(result.get('jobs', []))} jobs")
        
        return JobListResponse(
            data=result.get("jobs", []),
            total=result.get("total", 0),
            page=page,
            limit=limit,
            success=True
        )
        
    except Exception as e:
        logger.error(f"Failed to list jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve jobs: {str(e)}")


@router.get("/categories", response_model=JobCategoriesResponse)
@mesh.route(dependencies=["jobs_categories_list"])
async def get_job_categories(
    job_agent: McpMeshAgent = None
) -> JobCategoriesResponse:
    """
    Get all available job categories.
    
    Delegates to job_agent's jobs_categories_list capability.
    """
    try:
        logger.info("Getting job categories")
        
        # Delegate to job agent
        result = await job_agent()
        
        logger.info(f"Job agent returned {len(result.get('categories', []))} categories")
        
        return JobCategoriesResponse(
            data=result.get("categories", []),
            success=True
        )
        
    except Exception as e:
        logger.error(f"Failed to get job categories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve job categories: {str(e)}")


@router.get("/featured", response_model=JobListResponse)  
@mesh.route(dependencies=["jobs_featured_listing"])
async def get_featured_jobs(
    limit: int = 10,
    job_agent: McpMeshAgent = None
) -> JobListResponse:
    """
    Get featured jobs list.
    
    Delegates to job_agent's jobs_featured_listing capability.
    """
    try:
        logger.info(f"Getting featured jobs - limit {limit}")
        
        # Delegate to job agent
        result = await job_agent(limit=limit)
        
        logger.info(f"Job agent returned {len(result.get('featured_jobs', []))} featured jobs")
        
        return JobListResponse(
            data=result.get("featured_jobs", []),
            total=result.get("count", 0),
            page=1,
            limit=limit,
            success=True
        )
        
    except Exception as e:
        logger.error(f"Failed to get featured jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve featured jobs: {str(e)}")


@router.get("/{job_id}", response_model=JobDetailResponse)
@mesh.route(dependencies=["job_details_get"])
async def get_job_details(
    job_id: str,
    job_agent: McpMeshAgent = None
) -> JobDetailResponse:
    """
    Get detailed information about a specific job.
    
    Delegates to job_agent's job_details_get capability.
    """
    try:
        logger.info(f"Getting job details for job_id: {job_id}")
        
        # Delegate to job agent
        result = await job_agent(job_id=job_id)
        
        if not result or result.get("error"):
            logger.warning(f"Job not found: {job_id}")
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        logger.info(f"Job details retrieved for: {result['title']}")
        
        return JobDetailResponse(
            data=result,
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve job details: {str(e)}")