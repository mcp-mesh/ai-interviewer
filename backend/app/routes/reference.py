"""
Reference data endpoints for UI dropdowns and validation.
"""

import logging
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.database import CompanyLocation, EmploymentType
from app.database.postgres import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/reference", tags=["reference"])

@router.get("/categories")
async def get_business_categories():
    """Get available business categories for role classification."""
    categories = [
        {"code": "investment_management", "name": "Investment Management"},
        {"code": "legal_compliance", "name": "Legal & Compliance"},
        {"code": "marketing", "name": "Marketing"},
        {"code": "operations", "name": "Operations"},
        {"code": "relationship_management", "name": "Relationship Management"},
        {"code": "sales", "name": "Sales"},
        {"code": "technology", "name": "Technology"}
    ]
    
    logger.info(f"Retrieved {len(categories)} business categories")
    return {"categories": categories}

@router.get("/locations")
async def get_company_locations(db: Session = Depends(get_db)):
    """Get available company locations for role assignments."""
    
    locations = db.query(CompanyLocation).filter(CompanyLocation.active == True).all()
    
    location_list = []
    for location in locations:
        location_data = {
            "id": location.id,
            "country": location.country,
            "state": location.state,
            "city": location.city,
            "office_name": location.office_name,
            "remote_allowed": location.remote_allowed,
            "display_name": f"{location.city}, {location.state}, {location.country}" if location.state else f"{location.city}, {location.country}"
        }
        location_list.append(location_data)
    
    logger.info(f"Retrieved {len(location_list)} company locations")
    return {"locations": location_list}

@router.get("/employment-types")
async def get_employment_types(db: Session = Depends(get_db)):
    """Get available employment types for role classification."""
    
    employment_types = db.query(EmploymentType).filter(EmploymentType.active == True).all()
    
    types_list = []
    for emp_type in employment_types:
        type_data = {
            "id": emp_type.id,
            "code": emp_type.type_code,
            "name": emp_type.display_name,
            "description": emp_type.description
        }
        types_list.append(type_data)
    
    logger.info(f"Retrieved {len(types_list)} employment types")
    return {"types": types_list}

@router.get("/experience-levels")
async def get_experience_levels():
    """Get available experience levels for role requirements."""
    levels = [
        {"code": "intern", "name": "Intern", "description": "Learning role, 0-1 years, academic projects"},
        {"code": "junior", "name": "Junior", "description": "Entry level, 1-3 years, works with guidance"},
        {"code": "mid", "name": "Mid Level", "description": "Independent contributor, 3-7 years"},
        {"code": "senior", "name": "Senior", "description": "Expert contributor, 7-12 years, mentors others"},
        {"code": "lead", "name": "Lead", "description": "Leadership role, 10+ years, strategic decisions"},
        {"code": "principal", "name": "Principal", "description": "Senior leadership, 15+ years, sets direction"}
    ]
    
    logger.info(f"Retrieved {len(levels)} experience levels")
    return {"levels": levels}

@router.get("/role-statuses")
async def get_role_statuses():
    """Get available role status options."""
    statuses = [
        {"code": "open", "name": "Open", "description": "Actively recruiting candidates"},
        {"code": "closed", "name": "Closed", "description": "No longer accepting applications"},
        {"code": "on_hold", "name": "On Hold", "description": "Temporarily paused recruitment"}
    ]
    
    logger.info(f"Retrieved {len(statuses)} role statuses")
    return {"statuses": statuses}