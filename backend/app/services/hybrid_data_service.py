"""
Hybrid data service that manages both Redis and PostgreSQL data.
Redis: Fast auth data, sessions, flags
PostgreSQL: Rich profile data, structured content
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.database.redis_client import redis_client
from app.database.postgres import get_session
from app.models.database import UserProfile, Role, Interview
from app.services.skill_extraction import SkillExtractionService

logger = logging.getLogger(__name__)

class HybridDataService:
    """Manages data across Redis (fast auth) and PostgreSQL (rich profiles)."""
    
    @staticmethod
    def get_user_auth_data(email: str) -> Optional[Dict[str, Any]]:
        """Get fast authentication data from Redis."""
        try:
            user_key = f"user:{email}"
            return redis_client.get_json(user_key)
        except Exception as e:
            logger.error(f"Error getting auth data for {email}: {e}")
            return None
    
    @staticmethod
    def get_user_profile(email: str, db: Session = None) -> Optional[UserProfile]:
        """Get rich profile data from PostgreSQL."""
        close_session = False
        if db is None:
            db = get_session()
            close_session = True
        
        try:
            return db.query(UserProfile).filter(UserProfile.email == email).first()
        except Exception as e:
            logger.error(f"Error getting profile for {email}: {e}")
            return None
        finally:
            if close_session:
                db.close()
    
    @staticmethod
    def get_user_complete_data(email: str, db: Session = None) -> Dict[str, Any]:
        """Get combined user data from both Redis and PostgreSQL."""
        # Get auth data from Redis
        auth_data = HybridDataService.get_user_auth_data(email)
        if not auth_data:
            return {"exists": False}
        
        # Get profile data from PostgreSQL
        profile_data = HybridDataService.get_user_profile(email, db)
        
        return {
            "exists": True,
            "auth": auth_data,
            "profile": profile_data,
            "has_rich_profile": profile_data is not None,
            "has_resume": bool(auth_data.get("resume")) if auth_data else False
        }
    
    @staticmethod
    def create_or_update_profile(
        email: str, 
        profile_data: Dict[str, Any], 
        db: Session = None
    ) -> bool:
        """Create or update rich profile in PostgreSQL and sync flags to Redis."""
        close_session = False
        if db is None:
            db = get_session()
            close_session = True
        
        try:
            # Get or create profile
            profile = db.query(UserProfile).filter(UserProfile.email == email).first()
            
            if profile:
                # Update existing profile
                for key, value in profile_data.items():
                    if hasattr(profile, key):
                        setattr(profile, key, value)
            else:
                # Create new profile
                profile = UserProfile(email=email, **profile_data)
                db.add(profile)
            
            db.commit()
            db.refresh(profile)
            
            # Update Redis flags
            HybridDataService._sync_profile_flags_to_redis(email, profile)
            
            logger.info(f"Successfully created/updated profile for {email}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating/updating profile for {email}: {e}")
            if db:
                db.rollback()
            return False
        finally:
            if close_session:
                db.close()
    
    @staticmethod
    def update_auth_data(email: str, updates: Dict[str, Any]) -> bool:
        """Update or create authentication data in Redis."""
        try:
            user_key = f"user:{email}"
            current_data = redis_client.get_json(user_key)
            
            if not current_data:
                # User doesn't exist - create new user with provided data
                logger.info(f"Creating new user in Redis: {email}")
                current_data = updates.copy()
            else:
                # User exists - update existing data
                current_data.update(updates)
            
            current_data["last_active"] = datetime.utcnow().isoformat()
            
            # Save back to Redis
            success = redis_client.set_json(user_key, current_data)
            if success:
                logger.info(f"Updated auth data for {email}")
            return success
            
        except Exception as e:
            logger.error(f"Error updating auth data for {email}: {e}")
            return False
    
    @staticmethod
    async def process_resume_upload(
        email: str, 
        resume_content: str, 
        file_metadata: Dict[str, Any],
        llm_service,
        db: Session = None
    ) -> Dict[str, Any]:
        """Process resume upload: extract skills, update both Redis and PostgreSQL."""
        try:
            # Extract skills using LLM
            logger.info(f"Extracting skills from resume for {email}")
            extracted_data = await SkillExtractionService.extract_profile_data(
                resume_content, llm_service
            )
            
            if "error" in extracted_data:
                return {"success": False, "error": extracted_data["error"]}
            
            # Prepare profile data for PostgreSQL
            profile_data = {
                "name": file_metadata.get("user_name"),
                "overall_experience_level": extracted_data.get("overall_experience_level"),
                "total_years_experience": extracted_data.get("total_years_experience"),
                "skills": extracted_data.get("skills", {}),
                "leadership_experience": extracted_data.get("leadership_experience", {}),
                "career_progression": extracted_data.get("career_progression", []),
                "preferred_experience_levels": extracted_data.get("preferred_next_levels", []),
                "category_preferences": extracted_data.get("categories_of_interest", []),
                "resume_content": resume_content,
                "resume_metadata": file_metadata,
                "is_profile_complete": True
            }
            
            # Save to PostgreSQL
            profile_success = HybridDataService.create_or_update_profile(
                email, profile_data, db
            )
            
            if not profile_success:
                return {"success": False, "error": "Failed to save profile data"}
            
            # Update Redis with resume info (for backward compatibility)
            resume_data = {
                "resume": {
                    "filename": file_metadata.get("filename"),
                    "extracted_text": resume_content,
                    "upload_date": datetime.utcnow().isoformat(),
                    "structured_analysis": {
                        "skills_count": len(extracted_data.get("skills", {})),
                        "experience_level": extracted_data.get("overall_experience_level"),
                        "confidence_avg": HybridDataService._calculate_avg_confidence(
                            extracted_data.get("skills", {})
                        )
                    }
                }
            }
            
            redis_success = HybridDataService.update_auth_data(email, resume_data)
            
            if not redis_success:
                logger.warning(f"Profile saved to PostgreSQL but Redis update failed for {email}")
            
            return {
                "success": True,
                "skills_extracted": len(extracted_data.get("skills", {})),
                "experience_level": extracted_data.get("overall_experience_level"),
                "profile_complete": True
            }
            
        except Exception as e:
            logger.error(f"Error processing resume upload for {email}: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def _sync_profile_flags_to_redis(email: str, profile: UserProfile):
        """Sync PostgreSQL profile status flags to Redis for fast access."""
        try:
            flags = {
                "profile_exists": True,
                "profile_complete": profile.is_profile_complete,
                "skills_count": len(profile.skills) if profile.skills else 0,
                "experience_level": profile.overall_experience_level,
                "last_profile_update": datetime.utcnow().isoformat()
            }
            
            HybridDataService.update_auth_data(email, flags)
            
        except Exception as e:
            logger.error(f"Error syncing profile flags to Redis for {email}: {e}")
    
    @staticmethod
    def _calculate_avg_confidence(skills: Dict[str, Any]) -> float:
        """Calculate average confidence score from skills."""
        if not skills:
            return 0.0
        
        confidences = []
        for skill_data in skills.values():
            if isinstance(skill_data, dict) and "confidence" in skill_data:
                confidences.append(skill_data["confidence"])
        
        return sum(confidences) / len(confidences) if confidences else 0.0
    
    @staticmethod
    def check_user_has_profile(email: str) -> Dict[str, bool]:
        """Quick check if user has various types of data."""
        auth_data = HybridDataService.get_user_auth_data(email)
        
        if not auth_data:
            return {
                "exists": False,
                "has_auth": False,
                "has_resume": False,
                "has_rich_profile": False,
                "profile_complete": False
            }
        
        return {
            "exists": True,
            "has_auth": True,
            "has_resume": bool(auth_data.get("resume")),
            "has_rich_profile": auth_data.get("profile_exists", False),
            "profile_complete": auth_data.get("profile_complete", False)
        }
    
    @staticmethod
    def get_user_quick_stats(email: str) -> Dict[str, Any]:
        """Get quick user stats for dashboards (from Redis flags)."""
        auth_data = HybridDataService.get_user_auth_data(email)
        
        if not auth_data:
            return {"exists": False}
        
        return {
            "email": email,
            "name": auth_data.get("name"),
            "admin": auth_data.get("admin", False),
            "created_at": auth_data.get("created_at"),
            "last_active": auth_data.get("last_active"),
            "interview_count": auth_data.get("interview_count", 0),
            "has_resume": bool(auth_data.get("resume")),
            "skills_count": auth_data.get("skills_count", 0),
            "experience_level": auth_data.get("experience_level"),
            "profile_complete": auth_data.get("profile_complete", False)
        }

class ProfileMigrationService:
    """Service for migrating existing Redis data to PostgreSQL."""
    
    @staticmethod
    def migrate_user_from_redis(email: str, db: Session = None) -> bool:
        """Migrate a single user's data from Redis to PostgreSQL."""
        close_session = False
        if db is None:
            db = get_session()
            close_session = True
        
        try:
            # Get current Redis data
            auth_data = HybridDataService.get_user_auth_data(email)
            if not auth_data:
                logger.warning(f"No Redis data found for {email}")
                return False
            
            # Check if already migrated
            existing_profile = db.query(UserProfile).filter(
                UserProfile.email == email
            ).first()
            
            if existing_profile:
                logger.info(f"Profile already exists for {email}, skipping migration")
                return True
            
            # Extract resume data if available
            resume_data = auth_data.get("resume", {})
            if not resume_data:
                # Create basic profile without resume
                profile = UserProfile(
                    email=email,
                    name=auth_data.get("name"),
                    admin=auth_data.get("admin", False),
                    skills={},
                    leadership_experience={},
                    career_progression=[],
                    is_profile_complete=False
                )
                db.add(profile)
                db.commit()
                
                logger.info(f"Created basic profile for {email} (no resume)")
                return True
            
            # Has resume - need to re-extract with new LLM service
            resume_text = resume_data.get("extracted_text", "")
            if resume_text:
                logger.info(f"Re-extracting skills for migration: {email}")
                # This would need LLM service - for now create basic structure
                profile = UserProfile(
                    email=email,
                    name=auth_data.get("name"),
                    admin=auth_data.get("admin", False),
                    resume_content=resume_text,
                    resume_metadata={
                        "filename": resume_data.get("filename"),
                        "upload_date": resume_data.get("upload_date"),
                        "migrated_from_redis": True
                    },
                    skills={},  # Would be populated by LLM re-extraction
                    leadership_experience={},
                    career_progression=[],
                    is_profile_complete=False  # Mark as incomplete until LLM re-extraction
                )
                db.add(profile)
                db.commit()
                
                # Update Redis flags
                HybridDataService._sync_profile_flags_to_redis(email, profile)
                
                logger.info(f"Migrated profile for {email} (requires LLM re-extraction)")
                return True
            
        except Exception as e:
            logger.error(f"Error migrating user {email}: {e}")
            if db:
                db.rollback()
            return False
        finally:
            if close_session:
                db.close()
    
    @staticmethod
    def migrate_all_users(batch_size: int = 100) -> Dict[str, int]:
        """Migrate all users from Redis to PostgreSQL."""
        stats = {"migrated": 0, "skipped": 0, "errors": 0}
        
        try:
            # Get all user keys from Redis
            user_keys = redis_client.scan_keys("user:*")
            logger.info(f"Found {len(user_keys)} users in Redis")
            
            for user_key in user_keys:
                email = user_key.replace("user:", "")
                
                try:
                    success = ProfileMigrationService.migrate_user_from_redis(email)
                    if success:
                        stats["migrated"] += 1
                    else:
                        stats["skipped"] += 1
                        
                except Exception as e:
                    logger.error(f"Error migrating {email}: {e}")
                    stats["errors"] += 1
            
            logger.info(f"Migration complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error in bulk migration: {e}")
            return stats