#!/usr/bin/env python3
"""
Job Agent - MCP Mesh Agent for Job Management (SQLAlchemy Version)

Handles all job-related operations with PostgreSQL database backend using SQLAlchemy ORM.
Phase 2B implementation with database integration and auto-migration.
Capabilities: jobs_all_listing, job_details_get, jobs_featured_listing, jobs_categories_list
"""

import logging
import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session

import mesh
from fastmcp import FastMCP
from mesh.types import McpAgent
from .database import (
    Job, get_db_session, create_tables, insert_sample_data, test_connection
)

# Create FastMCP app instance
app = FastMCP("Job Management Agent")

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize database at module level - executed when MCP Mesh loads this module
logger.info("🚀 Initializing Job Agent v2.1 (SQLAlchemy + ORM)")

# Test database connection
if test_connection():
    logger.info("✅ PostgreSQL connection successful")
    
    # Create tables and schema
    if create_tables():
        logger.info("✅ Database schema initialized")
        
        # Insert sample data for demo
        if insert_sample_data():
            logger.info("✅ Sample job data ready")
        else:
            logger.warning("⚠️ Sample data insertion failed")
    else:
        logger.error("❌ Failed to initialize database schema")
else:
    logger.error("❌ PostgreSQL connection failed")


async def _search_jobs_with_filters(
    filters: Optional[Dict[str, List[str]]] = None,
    page: int = 1,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Internal function to search jobs with advanced filtering.
    
    Args:
        filters: Dict where keys are field names and values are lists of allowed values
        page: Page number for pagination (1-based)
        limit: Number of jobs per page
        
    Returns:
        Dict with jobs list, total count, and pagination info
    """
    try:
        logger.info(f"Searching jobs - page {page}, limit {limit}, filters: {filters}")
        
        with get_db_session() as db:
            # Build query with filters
            query = db.query(Job).filter(Job.is_active == True)
            
            if filters:
                # Multiple values within same field = OR condition
                # Multiple fields = AND condition across fields
                
                if filters.get("category"):
                    query = query.filter(Job.category.in_(filters["category"]))
                    
                if filters.get("job_type"):
                    query = query.filter(Job.job_type.in_(filters["job_type"]))
                    
                if filters.get("city"):
                    query = query.filter(Job.city.in_(filters["city"]))
                    
                if filters.get("state"):
                    # Handle None/null values for international jobs
                    state_values = filters["state"]
                    if "null" in state_values or None in state_values:
                        # Include jobs where state is in list OR state is null
                        query = query.filter(or_(
                            Job.state.in_([s for s in state_values if s and s != "null"]),
                            Job.state.is_(None)
                        ))
                    else:
                        query = query.filter(Job.state.in_(state_values))
                    
                if filters.get("country"):
                    query = query.filter(Job.country.in_(filters["country"]))
                    
                # Legacy filters for backward compatibility
                if filters.get("location"):
                    query = query.filter(Job.location.ilike(f"%{filters['location'][0]}%"))
                    
                if filters.get("experience_level"):
                    query = query.filter(Job.experience_level.ilike(f"%{filters['experience_level'][0]}%"))
            
            # Get total count
            total_jobs = query.count()
            
            # Get paginated jobs
            offset = (page - 1) * limit
            jobs_query = query.order_by(Job.posted_date.desc(), Job.created_at.desc())
            jobs_rows = jobs_query.offset(offset).limit(limit).all()
            
            # Convert to frontend-expected format
            jobs = []
            for job in jobs_rows:
                # Parse salary range into object format
                salary_range = None
                if job.salary_min and job.salary_max:
                    salary_range = {
                        "min": job.salary_min,
                        "max": job.salary_max,
                        "currency": job.salary_currency or "USD"
                    }
                
                job_dict = {
                    "id": str(job.id),
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "city": job.city,
                    "state": job.state,
                    "country": job.country,
                    "type": job.job_type,
                    "category": job.category,
                    "description": job.short_description,
                    "requirements": job.requirements or [],
                    "benefits": job.benefits or [],
                    "salaryRange": salary_range,
                    "remote": job.remote,
                    "postedAt": job.posted_date.isoformat() if job.posted_date else None,
                    "matchScore": 0  # Will be implemented with matching algorithm
                }
                jobs.append(job_dict)
        
        result = {
            "jobs": jobs,
            "total": total_jobs,
            "page": page,
            "limit": limit
        }
        
        logger.info(f"Returning {len(jobs)} jobs (total: {total_jobs})")
        return result
        
    except Exception as e:
        logger.error(f"Error in _search_jobs_with_filters: {str(e)}")
        return {"jobs": [], "total": 0, "page": page, "limit": limit, "error": str(e)}


@app.tool()
@mesh.tool(
    capability="jobs_all_listing",
    tags=["job-management", "listing", "search"],
    description="List all available jobs with optional filtering and pagination"
)
async def jobs_all_listing(
    filters: Optional[Dict[str, Any]] = None,
    page: int = 1,
    limit: int = 20
) -> Dict[str, Any]:
    """
    List all jobs with optional filtering.
    
    Args:
        filters: Optional filters (category, location, experience_level, job_type)
        page: Page number for pagination (1-based)
        limit: Number of jobs per page
        
    Returns:
        Dict with jobs list, total count, and pagination info
    """
    # Convert legacy filter format to new format
    parsed_filters = {}
    if filters:
        for key, value in filters.items():
            if value:  # Only add non-empty filters
                # Convert single values to arrays for consistency
                parsed_filters[key] = [value] if isinstance(value, str) else value
    
    # Delegate to internal filtering function
    return await _search_jobs_with_filters(parsed_filters, page, limit)


@app.tool()
@mesh.tool(
    capability="jobs_search_filtered",
    tags=["job-management", "search", "advanced-filtering"],
    description="Search jobs with advanced multi-value filtering"
)
async def jobs_search_filtered(
    category: Optional[str] = None,
    job_type: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    country: Optional[str] = None,
    page: int = 1,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Search jobs with advanced filtering supporting multiple values per field.
    
    Args:
        category: Comma-separated categories (e.g., "Engineering,Sales")
        job_type: Comma-separated job types (e.g., "Full-time,Contract")
        city: Comma-separated cities (e.g., "London,Remote")
        state: Comma-separated states (e.g., "Pennsylvania,California")
        country: Comma-separated countries (e.g., "United States of America,United Kingdom")
        page: Page number for pagination (1-based)
        limit: Number of jobs per page
        
    Returns:
        Dict with jobs list, total count, and pagination info
    """
    filters = {}
    
    # Parse comma-separated values into arrays
    if category:
        filters["category"] = [c.strip() for c in category.split(",") if c.strip()]
    if job_type:
        filters["job_type"] = [j.strip() for j in job_type.split(",") if j.strip()]
    if city:
        filters["city"] = [c.strip() for c in city.split(",") if c.strip()]
    if state:
        filters["state"] = [s.strip() for s in state.split(",") if s.strip()]
    if country:
        filters["country"] = [c.strip() for c in country.split(",") if c.strip()]
    
    # Delegate to internal filtering function
    return await _search_jobs_with_filters(filters, page, limit)


@app.tool()
@mesh.tool(
    capability="job_details_get",
    tags=["job-management", "details", "individual"],
    description="Get detailed information about a specific job"
)
async def job_details_get(job_id: str) -> Dict[str, Any]:
    """
    Get detailed job information by ID.
    
    Args:
        job_id: UUID of the job to retrieve
        
    Returns:
        Dict with complete job information or error
    """
    try:
        logger.info(f"Getting job details for ID: {job_id}")
        
        with get_db_session() as db:
            job = db.query(Job).filter(Job.id == job_id, Job.is_active == True).first()
            
            if not job:
                logger.warning(f"Job not found: {job_id}")
                return {"error": "Job not found", "job_id": job_id}
            
            # Return full job details using the model's to_dict method
            result = job.to_dict()
            logger.info(f"Returning job details for: {job.title}")
            return result
            
    except Exception as e:
        logger.error(f"Error in job_details_get: {str(e)}")
        return {"error": str(e), "job_id": job_id}


@app.tool()
@mesh.tool(
    capability="jobs_featured_listing",
    tags=["job-management", "featured", "highlights"],
    description="Get list of featured jobs for homepage/dashboard"
)
async def jobs_featured_listing(limit: int = 5) -> Dict[str, Any]:
    """
    Get featured jobs for homepage display.
    
    Args:
        limit: Maximum number of featured jobs to return
        
    Returns:
        Dict with featured jobs list
    """
    try:
        logger.info(f"Getting featured jobs (limit: {limit})")
        
        with get_db_session() as db:
            featured_jobs = db.query(Job).filter(
                and_(Job.is_featured == True, Job.is_active == True)
            ).order_by(Job.posted_date.desc()).limit(limit).all()
            
            # Convert to summary format
            jobs = []
            for job in featured_jobs:
                job_dict = {
                    "id": str(job.id),
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "job_type": job.job_type,
                    "category": job.category,
                    "remote": job.remote,
                    "short_description": job.short_description,
                    "posted_date": job.posted_date.isoformat() if job.posted_date else None
                }
                jobs.append(job_dict)
        
        result = {"featured_jobs": jobs, "count": len(jobs)}
        logger.info(f"Returning {len(jobs)} featured jobs")
        return result
        
    except Exception as e:
        logger.error(f"Error in jobs_featured_listing: {str(e)}")
        return {"featured_jobs": [], "count": 0, "error": str(e)}


@app.tool()
@mesh.tool(
    capability="jobs_categories_list",
    tags=["job-management", "categories", "metadata"],
    description="Get list of job categories with counts"
)
async def jobs_categories_list() -> Dict[str, Any]:
    """
    Get all job categories with job counts.
    
    Returns:
        Dict with categories and their counts
    """
    try:
        logger.info("Getting job categories with counts")
        
        with get_db_session() as db:
            # Get categories with counts using GROUP BY
            categories_query = db.query(
                Job.category,
                func.count(Job.id).label('count')
            ).filter(Job.is_active == True).group_by(Job.category).all()
            
            categories = []
            total_jobs = 0
            for category, count in categories_query:
                categories.append({
                    "category": category,
                    "count": count
                })
                total_jobs += count
        
        result = {
            "categories": categories,
            "total_active_jobs": total_jobs
        }
        
        logger.info(f"Returning {len(categories)} categories with {total_jobs} total jobs")
        return result
        
    except Exception as e:
        logger.error(f"Error in jobs_categories_list: {str(e)}")
        return {"categories": [], "total_active_jobs": 0, "error": str(e)}


@app.tool()
@mesh.tool(
    capability="jobs_filters_all",
    tags=["job-management", "filters", "metadata"],
    description="Get all unique filter values for job filtering (categories, locations, types)"
)
async def jobs_filters_all() -> Dict[str, Any]:
    """
    Get all unique filter values from active jobs.
    
    Returns:
        Dict with unique values for category, job_type, city, state, country
    """
    try:
        logger.info("Getting all unique job filter values")
        
        with get_db_session() as db:
            # Get unique categories
            categories = db.query(Job.category).filter(
                and_(Job.is_active == True, Job.category.isnot(None))
            ).distinct().all()
            
            # Get unique job types
            job_types = db.query(Job.job_type).filter(
                and_(Job.is_active == True, Job.job_type.isnot(None))
            ).distinct().all()
            
            # Get unique cities
            cities = db.query(Job.city).filter(
                and_(Job.is_active == True, Job.city.isnot(None))
            ).distinct().all()
            
            # Get unique states (excluding None values)
            states = db.query(Job.state).filter(
                and_(Job.is_active == True, Job.state.isnot(None))
            ).distinct().all()
            
            # Get unique countries
            countries = db.query(Job.country).filter(
                and_(Job.is_active == True, Job.country.isnot(None))
            ).distinct().all()
            
            # Convert to simple lists
            result = {
                "categories": [cat[0] for cat in categories],
                "job_types": [jt[0] for jt in job_types],
                "cities": [city[0] for city in cities],
                "states": [state[0] for state in states],
                "countries": [country[0] for country in countries]
            }
        
        logger.info(f"Returning filters: {len(result['categories'])} categories, {len(result['job_types'])} types, {len(result['cities'])} cities, {len(result['states'])} states, {len(result['countries'])} countries")
        return result
        
    except Exception as e:
        logger.error(f"Error in jobs_filters_all: {str(e)}")
        return {"categories": [], "job_types": [], "cities": [], "states": [], "countries": [], "error": str(e)}


@app.tool()
@mesh.tool(
    capability="jobs_search",
    tags=["job-management", "search", "full-text"],
    description="Search jobs by title, description, or company"
)
async def jobs_search(
    query: str,
    page: int = 1,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Search jobs using full-text search.
    
    Args:
        query: Search query string
        page: Page number for pagination (1-based)
        limit: Number of jobs per page
        
    Returns:
        Dict with matching jobs and pagination info
    """
    try:
        logger.info(f"Searching jobs for query: '{query}' (page {page}, limit {limit})")
        
        with get_db_session() as db:
            # Use ILIKE for simple text search (can be enhanced with PostgreSQL full-text search)
            search_filter = or_(
                Job.title.ilike(f"%{query}%"),
                Job.description.ilike(f"%{query}%"),
                Job.company.ilike(f"%{query}%"),
                Job.skills_required.any(query)  # Search in skills array
            )
            
            search_query = db.query(Job).filter(
                and_(Job.is_active == True, search_filter)
            )
            
            # Get total count
            total_jobs = search_query.count()
            
            # Get paginated results
            offset = (page - 1) * limit
            jobs_rows = search_query.order_by(
                Job.posted_date.desc()
            ).offset(offset).limit(limit).all()
            
            # Convert to dict format
            jobs = []
            for job in jobs_rows:
                job_dict = {
                    "id": str(job.id),
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "job_type": job.job_type,
                    "category": job.category,
                    "remote": job.remote,
                    "short_description": job.short_description,
                    "is_featured": job.is_featured,
                    "posted_date": job.posted_date.isoformat() if job.posted_date else None
                }
                jobs.append(job_dict)
        
        result = {
            "jobs": jobs,
            "total": total_jobs,
            "page": page,
            "limit": limit,
            "query": query
        }
        
        logger.info(f"Search returned {len(jobs)} jobs (total: {total_jobs})")
        return result
        
    except Exception as e:
        logger.error(f"Error in jobs_search: {str(e)}")
        return {"jobs": [], "total": 0, "page": page, "limit": limit, "query": query, "error": str(e)}


# Register as MCP agent
@mesh.agent(
    name="job-agent",
    auto_run=True)
class JobAgent(McpAgent):
    """Job Management Agent with database backend"""
    
    name = "job-agent"
    description = "Manages job postings with PostgreSQL database backend"
    capabilities = [
        "jobs_all_listing",
        "job_details_get", 
        "jobs_featured_listing",
        "jobs_categories_list",
        "jobs_filters_all",
        "jobs_search_filtered",
        "jobs_search"
    ]
    
    def __init__(self):
        super().__init__()
        logger.info("Job Agent initialized with SQLAlchemy ORM")


# Create and export agent instance
agent = JobAgent()

if __name__ == "__main__":
    logger.info("Job Agent started successfully")
