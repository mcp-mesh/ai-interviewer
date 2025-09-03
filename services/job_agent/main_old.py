#!/usr/bin/env python3
"""
Job Agent - MCP Mesh Agent for Job Management

Handles all job-related operations with PostgreSQL database backend.
Phase 2B implementation with database integration and auto-migration.
Capabilities: jobs_all_listing, job_details_get, jobs_featured_listing, jobs_categories_list
"""

import logging
import os
import asyncio
from typing import Any, Dict, List, Optional
from datetime import datetime

import mesh
from fastmcp import FastMCP
from mesh.types import McpAgent
from .database import db_manager

# Create FastMCP app instance
app = FastMCP("Job Management Agent")

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Database-backed job management - no static data needed


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
    try:
        logger.info(f"Listing jobs - page {page}, limit {limit}, filters: {filters}")
        
        async with db_manager.get_connection() as conn:
            # Build query with filters
            where_conditions = ["is_active = true"]
            params = []
            param_count = 0
            
            if filters:
                if filters.get("category"):
                    param_count += 1
                    where_conditions.append(f"category ILIKE ${param_count}")
                    params.append(f"%{filters['category']}%")
                    
                if filters.get("location"):
                    param_count += 1
                    where_conditions.append(f"location ILIKE ${param_count}")
                    params.append(f"%{filters['location']}%")
                    
                if filters.get("experience_level"):
                    param_count += 1
                    where_conditions.append(f"experience_level ILIKE ${param_count}")
                    params.append(f"%{filters['experience_level']}%")
                    
                if filters.get("job_type"):
                    param_count += 1
                    where_conditions.append(f"job_type = ${param_count}")
                    params.append(filters['job_type'])
            
            where_clause = " AND ".join(where_conditions)
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM job_agent.jobs WHERE {where_clause}"
            total_jobs = await conn.fetchval(count_query, *params)
            
            # Get paginated jobs (excluding full description for summary)
            offset = (page - 1) * limit
            jobs_query = f"""
                SELECT id, title, company, location, job_type, category, 
                       experience_level, remote, short_description, salary_min, salary_max, 
                       salary_currency, is_featured, posted_date
                FROM job_agent.jobs 
                WHERE {where_clause}
                ORDER BY posted_date DESC, created_at DESC
                LIMIT ${param_count + 1} OFFSET ${param_count + 2}
            """
            
            params.extend([limit, offset])
            jobs_rows = await conn.fetch(jobs_query, *params)
            
            # Convert to dict format
            jobs = []
            for row in jobs_rows:
                job = {
                    "id": str(row['id']),
                    "title": row['title'],
                    "company": row['company'],
                    "location": row['location'],
                    "job_type": row['job_type'],
                    "category": row['category'],
                    "experience_level": row['experience_level'],
                    "remote": row['remote'],
                    "short_description": row['short_description'],
                    "salary_range": f"${row['salary_min']:,} - ${row['salary_max']:,}" if row['salary_min'] and row['salary_max'] else None,
                    "is_featured": row['is_featured'],
                    "posted_date": row['posted_date'].isoformat() if row['posted_date'] else None
                }
                jobs.append(job)
        
        result = {
            "jobs": jobs,
            "total": total_jobs,
            "page": page,
            "limit": limit
        }
        
        logger.info(f"Returning {len(jobs)} jobs (total: {total_jobs})")
        return result
        
    except Exception as e:
        logger.error(f"Error in jobs_all_listing: {str(e)}")
        return {"jobs": [], "total": 0, "page": page, "limit": limit, "error": str(e)}


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
        job_id: Unique job identifier
        
    Returns:
        Dict with complete job details or None if not found
    """
    try:
        logger.info(f"Getting job details for job_id: {job_id}")
        
        async with db_manager.get_connection() as conn:
            job_row = await conn.fetchrow("""
                SELECT id, title, company, location, job_type, category, 
                       experience_level, remote, description, short_description, requirements, 
                       benefits, skills_required, salary_min, salary_max, 
                       salary_currency, is_featured, posted_date, is_active,
                       company_size, company_industry, company_website
                FROM job_agent.jobs 
                WHERE id = $1 AND is_active = true
            """, job_id)
            
            if job_row:
                job = {
                    "id": str(job_row['id']),
                    "title": job_row['title'],
                    "company": job_row['company'],
                    "location": job_row['location'],
                    "job_type": job_row['job_type'],
                    "category": job_row['category'],
                    "experience_level": job_row['experience_level'],
                    "remote": job_row['remote'],
                    "description": job_row['description'],
                    "short_description": job_row['short_description'],
                    "requirements": list(job_row['requirements']) if job_row['requirements'] else [],
                    "benefits": list(job_row['benefits']) if job_row['benefits'] else [],
                    "skills_required": list(job_row['skills_required']) if job_row['skills_required'] else [],
                    "salary_range": f"${job_row['salary_min']:,} - ${job_row['salary_max']:,}" if job_row['salary_min'] and job_row['salary_max'] else None,
                    "is_featured": job_row['is_featured'],
                    "posted_date": job_row['posted_date'].isoformat() if job_row['posted_date'] else None,
                    "company_info": {
                        "name": job_row['company'],
                        "size": job_row['company_size'],
                        "industry": job_row['company_industry'],
                        "website": job_row['company_website']
                    } if any([job_row['company_size'], job_row['company_industry'], job_row['company_website']]) else None
                }
                
                logger.info(f"Found job: {job['title']} at {job['company']}")
                return {"job": job}
            else:
                logger.warning(f"Job not found: {job_id}")
                return {"job": None, "error": f"Job {job_id} not found"}
            
    except Exception as e:
        logger.error(f"Error in job_details_get: {str(e)}")
        return {"job": None, "error": str(e)}


@app.tool()
@mesh.tool(
    capability="jobs_featured_listing",
    tags=["job-management", "featured", "curated"],
    description="Get featured jobs list"
)
async def jobs_featured_listing(limit: int = 10) -> Dict[str, Any]:
    """
    Get featured jobs.
    
    Args:
        limit: Maximum number of featured jobs to return
        
    Returns:
        Dict with featured jobs list
    """
    try:
        logger.info(f"Getting featured jobs - limit {limit}")
        
        async with db_manager.get_connection() as conn:
            jobs_rows = await conn.fetch("""
                SELECT id, title, company, location, job_type, category, 
                       experience_level, remote, short_description, salary_min, salary_max, 
                       salary_currency, is_featured, posted_date
                FROM job_agent.jobs 
                WHERE is_featured = true AND is_active = true
                ORDER BY posted_date DESC, created_at DESC
                LIMIT $1
            """, limit)
            
            # Convert to dict format
            jobs = []
            for row in jobs_rows:
                job = {
                    "id": str(row['id']),
                    "title": row['title'],
                    "company": row['company'],
                    "location": row['location'],
                    "job_type": row['job_type'],
                    "category": row['category'],
                    "experience_level": row['experience_level'],
                    "remote": row['remote'],
                    "short_description": row['short_description'],
                    "salary_range": f"${row['salary_min']:,} - ${row['salary_max']:,}" if row['salary_min'] and row['salary_max'] else None,
                    "is_featured": row['is_featured'],
                    "posted_date": row['posted_date'].isoformat() if row['posted_date'] else None
                }
                jobs.append(job)
        
        result = {
            "jobs": jobs,
            "total": len(jobs)
        }
        
        logger.info(f"Returning {len(jobs)} featured jobs")
        return result
        
    except Exception as e:
        logger.error(f"Error in jobs_featured_listing: {str(e)}")
        return {"jobs": [], "total": 0, "error": str(e)}


@app.tool()
@mesh.tool(
    capability="jobs_categories_list",
    tags=["job-management", "categories", "metadata"],
    description="Get all available job categories"
)
async def jobs_categories_list() -> Dict[str, Any]:
    """
    Get all job categories with job counts.
    
    Returns:
        Dict with categories list
    """
    try:
        logger.info("Getting job categories")
        
        async with db_manager.get_connection() as conn:
            categories_rows = await conn.fetch("""
                SELECT category, COUNT(*) as job_count
                FROM job_agent.jobs 
                WHERE is_active = true
                GROUP BY category
                ORDER BY job_count DESC, category
            """)
            
            categories = []
            for row in categories_rows:
                category = {
                    "id": row['category'].lower().replace(' ', '-'),
                    "name": row['category'],
                    "description": f"{row['category']} related positions",
                    "job_count": row['job_count']
                }
                categories.append(category)
        
        result = {"categories": categories}
        
        logger.info(f"Returning {len(categories)} categories")
        return result
        
    except Exception as e:
        logger.error(f"Error in jobs_categories_list: {str(e)}")
        return {"categories": [], "error": str(e)}


# Agent class definition - MCP Mesh pattern
@mesh.agent(
    name="job-agent",
    auto_run=True
)
class JobAgent(McpAgent):
    """
    Job Agent for AI Interviewer Phase 2B
    
    Handles all job-related operations with PostgreSQL database backend.
    Capabilities: jobs_all_listing, job_details_get, jobs_featured_listing, jobs_categories_list
    """
    
    def __init__(self):
        logger.info("🚀 Initializing Job Agent v2.1 (Database Edition)")
        
        # Initialize database connection
        asyncio.create_task(self._initialize_database())
        
        logger.info("✅ Job Agent ready to serve requests")
    
    async def _initialize_database(self):
        """Initialize database connection and run migrations"""
        try:
            success = await db_manager.initialize()
            if success:
                logger.info("🗄️  Database initialized successfully")
                
                # Get job count for logging
                async with db_manager.get_connection() as conn:
                    job_count = await conn.fetchval("SELECT COUNT(*) FROM job_agent.jobs WHERE is_active = true")
                    featured_count = await conn.fetchval("SELECT COUNT(*) FROM job_agent.jobs WHERE is_featured = true AND is_active = true")
                    category_count = await conn.fetchval("SELECT COUNT(DISTINCT category) FROM job_agent.jobs WHERE is_active = true")
                    
                logger.info(f"📊 Database contains {job_count} active jobs")
                logger.info(f"🌟 {featured_count} featured jobs available")
                logger.info(f"🏷️  {category_count} job categories")
            else:
                logger.error("❌ Database initialization failed")
        except Exception as e:
            logger.error(f"❌ Database initialization error: {str(e)}")


# Startup function
async def startup():
    """Startup function to initialize the agent"""
    logger.info("🚀 Starting Job Agent...")
    agent = JobAgent()
    return agent

if __name__ == "__main__":
    logger.info("Job Agent starting...")
    asyncio.run(startup())