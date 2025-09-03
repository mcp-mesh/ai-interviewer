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
    JobFiltersResponse,
    JobFiltersData,
    JobFilters,
    ErrorResponse
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/search", response_model=JobListResponse)
@mesh.route(dependencies=["jobs_search_filtered"])
async def search_jobs(
    category: Optional[str] = None,
    job_type: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    country: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    job_agent: McpMeshAgent = None
) -> JobListResponse:
    """
    Search jobs with advanced filtering supporting multiple values per field.
    
    Query parameters support comma-separated values:
    - category: Engineering,Sales
    - job_type: Full-time,Contract
    - city: London,Remote
    - state: Pennsylvania,California
    - country: United States of America,United Kingdom
    """
    try:
        logger.info(f"Searching jobs - page {page}, limit {limit}, filters: category={category}, job_type={job_type}, city={city}, state={state}, country={country}")
        
        # Delegate to job agent's new filtered search capability
        result = await job_agent(
            category=category,
            job_type=job_type,
            city=city,
            state=state,
            country=country,
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
        logger.error(f"Failed to search jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to search jobs: {str(e)}")





@router.get("/filters", response_model=JobFiltersResponse)
@mesh.route(dependencies=["jobs_filters_all"])
async def get_job_filters(
    job_agent: McpMeshAgent = None
) -> JobFiltersResponse:
    """
    Get all available job filter values.
    
    Delegates to job_agent's jobs_filters_all capability.
    """
    try:
        logger.info("Getting job filters")
        
        # Delegate to job agent
        result = await job_agent()
        
        logger.info(f"Job agent returned filters with {len(result.get('categories', []))} categories, {len(result.get('job_types', []))} job types")
        
        filters_data = JobFiltersData(
            categories=result.get("categories", []),
            job_types=result.get("job_types", []),
            cities=result.get("cities", []),
            states=result.get("states", []),
            countries=result.get("countries", [])
        )
        
        return JobFiltersResponse(
            data=filters_data,
            success=True
        )
        
    except Exception as e:
        logger.error(f"Failed to get job filters: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve job filters: {str(e)}")


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