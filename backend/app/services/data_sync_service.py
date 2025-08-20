"""
Data synchronization service for maintaining consistency between Redis and PostgreSQL.
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.database.redis_client import redis_client
from app.database.postgres import get_session
from app.models.database import UserProfile, Role, Interview
from app.services.hybrid_data_service import HybridDataService

logger = logging.getLogger(__name__)

class DataSyncService:
    """Service for synchronizing data between Redis and PostgreSQL."""
    
    @staticmethod
    def sync_user_profile_flags(email: str, db: Session = None) -> bool:
        """Sync PostgreSQL profile data flags to Redis for fast access."""
        close_session = False
        if db is None:
            db = get_session()
            close_session = True
        
        try:
            # Get profile from PostgreSQL
            profile = db.query(UserProfile).filter(UserProfile.email == email).first()
            
            if profile:
                # Update Redis flags
                flags = {
                    "profile_exists": True,
                    "profile_complete": profile.is_profile_complete,
                    "skills_count": len(profile.skills) if profile.skills else 0,
                    "experience_level": profile.overall_experience_level,
                    "last_profile_update": datetime.utcnow().isoformat(),
                    "has_resume": bool(profile.resume_content)
                }
                
                success = HybridDataService.update_auth_data(email, flags)
                if success:
                    logger.info(f"Synced profile flags to Redis for {email}")
                return success
            else:
                # Profile doesn't exist - clear flags
                flags = {
                    "profile_exists": False,
                    "profile_complete": False,
                    "skills_count": 0,
                    "experience_level": None,
                    "has_resume": False
                }
                
                success = HybridDataService.update_auth_data(email, flags)
                if success:
                    logger.info(f"Cleared profile flags in Redis for {email}")
                return success
                
        except Exception as e:
            logger.error(f"Error syncing profile flags for {email}: {e}")
            return False
        finally:
            if close_session:
                db.close()
    
    @staticmethod
    def sync_interview_count(email: str, db: Session = None) -> bool:
        """Sync interview count from PostgreSQL to Redis."""
        close_session = False
        if db is None:
            db = get_session()
            close_session = True
        
        try:
            # Count completed interviews
            interview_count = db.query(Interview).filter(
                Interview.user_email == email,
                Interview.status == "completed"
            ).count()
            
            # Update Redis
            success = HybridDataService.update_auth_data(email, {
                "interview_count": interview_count,
                "last_interview_sync": datetime.utcnow().isoformat()
            })
            
            if success:
                logger.info(f"Synced interview count ({interview_count}) for {email}")
            return success
            
        except Exception as e:
            logger.error(f"Error syncing interview count for {email}: {e}")
            return False
        finally:
            if close_session:
                db.close()
    
    @staticmethod
    def validate_data_consistency(email: str, db: Session = None) -> Dict[str, Any]:
        """Validate consistency between Redis and PostgreSQL data for a user."""
        close_session = False
        if db is None:
            db = get_session()
            close_session = True
        
        try:
            # Get data from both sources
            auth_data = HybridDataService.get_user_auth_data(email)
            profile_data = HybridDataService.get_user_profile(email, db)
            
            validation_result = {
                "email": email,
                "timestamp": datetime.utcnow().isoformat(),
                "consistent": True,
                "issues": [],
                "redis_data": bool(auth_data),
                "postgres_data": bool(profile_data)
            }
            
            if not auth_data:
                validation_result["issues"].append("No Redis auth data found")
                validation_result["consistent"] = False
            
            if not profile_data:
                if auth_data and auth_data.get("profile_exists"):
                    validation_result["issues"].append("Redis indicates profile exists but not found in PostgreSQL")
                    validation_result["consistent"] = False
            else:
                # Check flag consistency
                if auth_data:
                    redis_profile_complete = auth_data.get("profile_complete", False)
                    pg_profile_complete = profile_data.is_profile_complete
                    
                    if redis_profile_complete != pg_profile_complete:
                        validation_result["issues"].append(
                            f"Profile complete flag mismatch: Redis={redis_profile_complete}, PG={pg_profile_complete}"
                        )
                        validation_result["consistent"] = False
                    
                    redis_skills_count = auth_data.get("skills_count", 0)
                    pg_skills_count = len(profile_data.skills) if profile_data.skills else 0
                    
                    if redis_skills_count != pg_skills_count:
                        validation_result["issues"].append(
                            f"Skills count mismatch: Redis={redis_skills_count}, PG={pg_skills_count}"
                        )
                        validation_result["consistent"] = False
                    
                    redis_experience = auth_data.get("experience_level")
                    pg_experience = profile_data.overall_experience_level
                    
                    if redis_experience != pg_experience:
                        validation_result["issues"].append(
                            f"Experience level mismatch: Redis={redis_experience}, PG={pg_experience}"
                        )
                        validation_result["consistent"] = False
            
            # Check interview count
            if auth_data and profile_data:
                redis_interview_count = auth_data.get("interview_count", 0)
                actual_interview_count = db.query(Interview).filter(
                    Interview.user_email == email,
                    Interview.status == "completed"
                ).count()
                
                if redis_interview_count != actual_interview_count:
                    validation_result["issues"].append(
                        f"Interview count mismatch: Redis={redis_interview_count}, Actual={actual_interview_count}"
                    )
                    validation_result["consistent"] = False
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating data consistency for {email}: {e}")
            return {
                "email": email,
                "timestamp": datetime.utcnow().isoformat(),
                "consistent": False,
                "issues": [f"Validation error: {str(e)}"],
                "error": True
            }
        finally:
            if close_session:
                db.close()
    
    @staticmethod
    def repair_data_inconsistencies(email: str, db: Session = None) -> Dict[str, Any]:
        """Repair data inconsistencies for a user."""
        close_session = False
        if db is None:
            db = get_session()
            close_session = True
        
        try:
            validation = DataSyncService.validate_data_consistency(email, db)
            
            repair_result = {
                "email": email,
                "timestamp": datetime.utcnow().isoformat(),
                "repairs_attempted": [],
                "repairs_successful": [],
                "repairs_failed": []
            }
            
            if validation["consistent"]:
                repair_result["message"] = "No repairs needed - data is consistent"
                return repair_result
            
            # Attempt to repair each issue
            for issue in validation["issues"]:
                try:
                    if "profile exists but not found in PostgreSQL" in issue:
                        # Clear Redis profile flags
                        repair_result["repairs_attempted"].append("Clear invalid Redis profile flags")
                        success = HybridDataService.update_auth_data(email, {
                            "profile_exists": False,
                            "profile_complete": False,
                            "skills_count": 0,
                            "experience_level": None
                        })
                        if success:
                            repair_result["repairs_successful"].append("Cleared invalid Redis profile flags")
                        else:
                            repair_result["repairs_failed"].append("Failed to clear Redis profile flags")
                    
                    elif "Profile complete flag mismatch" in issue or "Skills count mismatch" in issue or "Experience level mismatch" in issue:
                        # Sync flags from PostgreSQL
                        repair_result["repairs_attempted"].append("Sync profile flags from PostgreSQL")
                        success = DataSyncService.sync_user_profile_flags(email, db)
                        if success:
                            repair_result["repairs_successful"].append("Synced profile flags from PostgreSQL")
                        else:
                            repair_result["repairs_failed"].append("Failed to sync profile flags")
                    
                    elif "Interview count mismatch" in issue:
                        # Sync interview count
                        repair_result["repairs_attempted"].append("Sync interview count")
                        success = DataSyncService.sync_interview_count(email, db)
                        if success:
                            repair_result["repairs_successful"].append("Synced interview count")
                        else:
                            repair_result["repairs_failed"].append("Failed to sync interview count")
                
                except Exception as e:
                    repair_result["repairs_failed"].append(f"Error repairing '{issue}': {str(e)}")
            
            repair_result["success"] = len(repair_result["repairs_failed"]) == 0
            return repair_result
            
        except Exception as e:
            logger.error(f"Error repairing data inconsistencies for {email}: {e}")
            return {
                "email": email,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "success": False
            }
        finally:
            if close_session:
                db.close()
    
    @staticmethod
    async def bulk_data_validation(limit: int = 100) -> Dict[str, Any]:
        """Validate data consistency for multiple users."""
        try:
            # Get all user keys from Redis
            user_keys = redis_client.scan_keys("user:*")
            if not user_keys:
                return {"message": "No users found in Redis", "total": 0}
            
            # Limit the check if requested
            if limit and len(user_keys) > limit:
                user_keys = user_keys[:limit]
            
            logger.info(f"Validating data consistency for {len(user_keys)} users")
            
            results = {
                "total_checked": len(user_keys),
                "consistent": 0,
                "inconsistent": 0,
                "errors": 0,
                "issues_found": [],
                "users_with_issues": []
            }
            
            db = get_session()
            try:
                for user_key in user_keys:
                    email = user_key.replace("user:", "")
                    
                    try:
                        validation = DataSyncService.validate_data_consistency(email, db)
                        
                        if validation.get("error"):
                            results["errors"] += 1
                        elif validation["consistent"]:
                            results["consistent"] += 1
                        else:
                            results["inconsistent"] += 1
                            results["users_with_issues"].append({
                                "email": email,
                                "issues": validation["issues"]
                            })
                            results["issues_found"].extend(validation["issues"])
                    
                    except Exception as e:
                        logger.error(f"Error validating {email}: {e}")
                        results["errors"] += 1
            
            finally:
                db.close()
            
            logger.info(f"Bulk validation complete: {results['consistent']} consistent, {results['inconsistent']} inconsistent, {results['errors']} errors")
            return results
            
        except Exception as e:
            logger.error(f"Error in bulk data validation: {e}")
            return {"error": str(e)}
    
    @staticmethod
    async def bulk_data_repair(emails: List[str] = None, auto_repair: bool = False) -> Dict[str, Any]:
        """Repair data inconsistencies for multiple users."""
        try:
            if not emails:
                # Get users with issues from validation
                validation_result = await DataSyncService.bulk_data_validation()
                if "users_with_issues" in validation_result:
                    emails = [user["email"] for user in validation_result["users_with_issues"]]
                else:
                    return {"message": "No users with issues found"}
            
            if not emails:
                return {"message": "No users to repair"}
            
            logger.info(f"Attempting to repair data for {len(emails)} users")
            
            results = {
                "total_processed": len(emails),
                "successful_repairs": 0,
                "failed_repairs": 0,
                "repair_details": []
            }
            
            db = get_session()
            try:
                for email in emails:
                    try:
                        if auto_repair:
                            repair_result = DataSyncService.repair_data_inconsistencies(email, db)
                            results["repair_details"].append(repair_result)
                            
                            if repair_result.get("success"):
                                results["successful_repairs"] += 1
                            else:
                                results["failed_repairs"] += 1
                        else:
                            # Just validate and report
                            validation = DataSyncService.validate_data_consistency(email, db)
                            results["repair_details"].append({
                                "email": email,
                                "validation": validation,
                                "auto_repair": False
                            })
                    
                    except Exception as e:
                        logger.error(f"Error processing {email}: {e}")
                        results["failed_repairs"] += 1
                        results["repair_details"].append({
                            "email": email,
                            "error": str(e)
                        })
            
            finally:
                db.close()
            
            logger.info(f"Bulk repair complete: {results['successful_repairs']} successful, {results['failed_repairs']} failed")
            return results
            
        except Exception as e:
            logger.error(f"Error in bulk data repair: {e}")
            return {"error": str(e)}

class DataSyncScheduler:
    """Scheduled data synchronization tasks."""
    
    @staticmethod
    async def hourly_sync_check():
        """Hourly task to check and repair data inconsistencies."""
        logger.info("Starting hourly data sync check...")
        
        try:
            # Validate a sample of users
            validation_result = await DataSyncService.bulk_data_validation(limit=50)
            
            if validation_result.get("inconsistent", 0) > 0:
                logger.warning(f"Found {validation_result['inconsistent']} users with data inconsistencies")
                
                # Auto-repair if issues are found
                repair_result = await DataSyncService.bulk_data_repair(auto_repair=True)
                logger.info(f"Auto-repair results: {repair_result.get('successful_repairs', 0)} successful")
            
        except Exception as e:
            logger.error(f"Error in hourly sync check: {e}")
    
    @staticmethod
    async def daily_full_validation():
        """Daily task to validate all user data."""
        logger.info("Starting daily full data validation...")
        
        try:
            validation_result = await DataSyncService.bulk_data_validation()
            logger.info(f"Daily validation: {validation_result}")
            
            # Log summary
            if validation_result.get("inconsistent", 0) > 0:
                logger.warning(f"Daily validation found {validation_result['inconsistent']} inconsistent users")
            else:
                logger.info("Daily validation: All user data is consistent")
                
        except Exception as e:
            logger.error(f"Error in daily validation: {e}")