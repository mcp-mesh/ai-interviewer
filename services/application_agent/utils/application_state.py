"""
Application State Management Utilities

Handles application state queries, updates, and creation logic.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..database import get_db_session, Application, ApplicationStatus

logger = logging.getLogger(__name__)

async def get_application_state(
    user_email: str, 
    job_id: str
) -> Optional[Dict[str, Any]]:
    """
    Get existing application state for user and job.
    
    Returns None if no application exists.
    """
    try:
        with get_db_session() as db_session:
            # Query for existing application
            application = db_session.query(Application).filter(
                and_(
                    Application.user_email == user_email,
                    Application.job_id == job_id
                )
            ).first()
            
            if not application:
                return None
            
            return {
                "id": application.id,
                "user_email": application.user_email,
                "job_id": application.job_id,
                "step": application.step,
                "status": application.status,
                "created_at": application.created_at.isoformat(),
                "updated_at": application.updated_at.isoformat(),
            }
            
    except Exception as e:
        logger.error(f"Failed to get application state: {e}")
        return None

async def create_new_application(
    user_email: str,
    job_id: str
) -> Dict[str, Any]:
    """
    Create a new application for user and job.
    
    Default: step=1, status=STARTED
    """
    try:
        with get_db_session() as db_session:
            application = Application(
                user_email=user_email,
                job_id=job_id,
                step="STEP_1",
                status="STARTED"
            )
            
            db_session.add(application)
            db_session.commit()
            db_session.refresh(application)
            
            logger.info(f"Created new application: user={user_email}, job={job_id}, id={application.id}")
            
            return {
                "id": application.id,
                "user_email": application.user_email,
                "job_id": application.job_id,
                "step": application.step,
                "status": application.status,
                "created_at": application.created_at.isoformat(),
                "updated_at": application.updated_at.isoformat(),
            }
            
    except Exception as e:
        logger.error(f"Failed to create new application: {e}")
        raise

async def update_application_step(
    application_id: str,
    new_step: int,
    status: str = "STARTED"
) -> Dict[str, Any]:
    """
    Update application to new step and status.
    
    Used after saving step data to progress to next step.
    """
    try:
        with get_db_session() as db_session:
            application = db_session.query(Application).filter(
                Application.id == application_id
            ).first()
            
            if not application:
                raise ValueError(f"Application not found: {application_id}")
            
            # Update step and status
            application.step = f"STEP_{new_step}"
            application.status = status
            application.updated_at = datetime.utcnow()
            
            # Metadata functionality removed - using dedicated columns instead
            
            db_session.commit()
            db_session.refresh(application)
            
            logger.info(f"Updated application {application_id}: step={new_step}, status={status}")
            
            return {
                "id": application.id,
                "user_email": application.user_email,
                "job_id": application.job_id,
                "step": application.step,
                "status": application.status,
                "created_at": application.created_at.isoformat(),
                "updated_at": application.updated_at.isoformat(),
            }
            
    except Exception as e:
        logger.error(f"Failed to update application step: {e}")
        raise

async def get_or_create_application(
    user_email: str,
    job_id: str
) -> Dict[str, Any]:
    """
    Get existing application or create new one if none exists.
    
    This is the main function for application_start_with_prefill.
    """
    # Try to get existing application
    existing_app = await get_application_state(user_email, job_id)
    
    if existing_app:
        # Return existing application if status is STARTED
        if existing_app["status"] == "STARTED":
            logger.info(f"Found existing application: user={user_email}, job={job_id}, step={existing_app['step']}")
            return existing_app
        else:
            logger.info(f"Application already completed: user={user_email}, job={job_id}, status={existing_app['status']}")
            # Could either return error or create new application - depends on business logic
            # For now, return the existing one
            return existing_app
    
    # Create new application if none exists
    logger.info(f"Creating new application: user={user_email}, job={job_id}")
    return await create_new_application(user_email, job_id)