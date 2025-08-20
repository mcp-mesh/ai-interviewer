#!/usr/bin/env python3
"""
Profile migration utility for moving existing Redis user data to PostgreSQL.
This script migrates users from Redis-only storage to the hybrid Redis/PostgreSQL approach.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.postgres import db_manager, get_session
from app.services.hybrid_data_service import ProfileMigrationService, HybridDataService
from app.services.skill_extraction import SkillExtractionService
from app.database.redis_client import redis_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def migrate_users_with_llm_extraction(llm_service=None):
    """
    Advanced migration that re-extracts skills from resumes using LLM.
    This provides the most complete migration but requires LLM service.
    """
    logger.info("Starting advanced migration with LLM skill re-extraction...")
    
    if not llm_service:
        logger.warning("No LLM service provided - using basic migration instead")
        return migrate_users_basic()
    
    try:
        # Get all user keys from Redis
        user_keys = redis_client.scan_keys("user:*")
        logger.info(f"Found {len(user_keys)} users in Redis for advanced migration")
        
        stats = {"migrated": 0, "skipped": 0, "errors": 0, "re_extracted": 0}
        
        for user_key in user_keys:
            email = user_key.replace("user:", "")
            
            try:
                # Get current Redis data
                auth_data = HybridDataService.get_user_auth_data(email)
                if not auth_data:
                    logger.warning(f"No auth data found for {email}")
                    stats["skipped"] += 1
                    continue
                
                # Check if already migrated
                db = get_session()
                try:
                    existing_profile = HybridDataService.get_user_profile(email, db)
                    if existing_profile and existing_profile.is_profile_complete:
                        logger.info(f"User {email} already fully migrated, skipping")
                        stats["skipped"] += 1
                        continue
                    
                    # Check if user has resume content
                    resume_data = auth_data.get("resume", {})
                    resume_text = resume_data.get("extracted_text", "")
                    
                    if resume_text:
                        logger.info(f"Re-extracting skills for {email}")
                        
                        # Process resume with LLM extraction
                        file_metadata = {
                            "filename": resume_data.get("filename", "migrated_resume.pdf"),
                            "user_name": auth_data.get("name"),
                            "upload_date": resume_data.get("upload_date", datetime.utcnow().isoformat()),
                            "migrated_from_redis": True
                        }
                        
                        result = await HybridDataService.process_resume_upload(
                            email, resume_text, file_metadata, llm_service, db
                        )
                        
                        if result.get("success"):
                            stats["migrated"] += 1
                            stats["re_extracted"] += 1
                            logger.info(f"Successfully migrated and re-extracted skills for {email}")
                        else:
                            logger.error(f"Failed to migrate {email}: {result.get('error')}")
                            stats["errors"] += 1
                    else:
                        # Create basic profile without resume
                        profile_data = {
                            "name": auth_data.get("name"),
                            "admin": auth_data.get("admin", False),
                            "skills": {},
                            "leadership_experience": {},
                            "career_progression": [],
                            "is_profile_complete": False
                        }
                        
                        success = HybridDataService.create_or_update_profile(email, profile_data, db)
                        if success:
                            stats["migrated"] += 1
                            logger.info(f"Created basic profile for {email} (no resume)")
                        else:
                            stats["errors"] += 1
                            logger.error(f"Failed to create basic profile for {email}")
                
                finally:
                    db.close()
                    
            except Exception as e:
                logger.error(f"Error migrating {email}: {e}")
                stats["errors"] += 1
        
        logger.info(f"Advanced migration complete: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error in advanced migration: {e}")
        return {"error": str(e)}

def migrate_users_basic():
    """
    Basic migration that creates placeholder profiles without LLM extraction.
    Users with resumes will need to re-upload them for skill extraction.
    """
    logger.info("Starting basic migration without LLM extraction...")
    
    return ProfileMigrationService.migrate_all_users()

def check_migration_status():
    """Check the current migration status."""
    try:
        # Count Redis users
        user_keys = redis_client.scan_keys("user:*")
        redis_user_count = len(user_keys)
        
        # Count PostgreSQL profiles
        db = get_session()
        try:
            from app.models.database import UserProfile
            pg_profile_count = db.query(UserProfile).count()
            complete_profiles = db.query(UserProfile).filter(
                UserProfile.is_profile_complete == True
            ).count()
        finally:
            db.close()
        
        status = {
            "redis_users": redis_user_count,
            "postgresql_profiles": pg_profile_count,
            "complete_profiles": complete_profiles,
            "migration_needed": redis_user_count - pg_profile_count,
            "incomplete_profiles": pg_profile_count - complete_profiles
        }
        
        logger.info(f"Migration Status: {status}")
        return status
        
    except Exception as e:
        logger.error(f"Error checking migration status: {e}")
        return {"error": str(e)}

def cleanup_migrated_data():
    """
    Optional cleanup of Redis data after successful migration.
    WARNING: This will remove user data from Redis permanently.
    Only run this after confirming PostgreSQL migration is successful.
    """
    logger.warning("CLEANUP MODE - This will remove Redis user data permanently!")
    response = input("Are you sure you want to cleanup Redis data? Type 'YES' to confirm: ")
    
    if response != "YES":
        logger.info("Cleanup cancelled")
        return
    
    try:
        # Get migration status first
        status = check_migration_status()
        if status.get("migration_needed", 0) > 0:
            logger.error("Migration not complete - refusing to cleanup")
            return
        
        # Remove user data from Redis (keep auth data for sessions)
        user_keys = redis_client.scan_keys("user:*")
        cleaned = 0
        
        for user_key in user_keys:
            email = user_key.replace("user:", "")
            
            # Keep only essential auth data
            auth_data = redis_client.get_json(user_key)
            if auth_data:
                essential_data = {
                    "email": auth_data.get("email"),
                    "name": auth_data.get("name"),
                    "admin": auth_data.get("admin", False),
                    "created_at": auth_data.get("created_at"),
                    "last_active": auth_data.get("last_active"),
                    "interview_count": auth_data.get("interview_count", 0),
                    "profile_exists": True,
                    "profile_complete": True,
                    "migrated_to_postgres": True
                }
                
                redis_client.set_json(user_key, essential_data)
                cleaned += 1
        
        logger.info(f"Cleaned up {cleaned} Redis user records")
        return {"cleaned": cleaned}
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return {"error": str(e)}

async def main():
    """Main migration function."""
    logger.info("AI Interviewer - Profile Migration Utility")
    logger.info("=" * 50)
    
    # Initialize database
    if not db_manager.init_database():
        logger.error("Failed to initialize database")
        sys.exit(1)
    
    # Check current status
    logger.info("Checking current migration status...")
    status = check_migration_status()
    if "error" in status:
        logger.error("Failed to check migration status")
        sys.exit(1)
    
    if status["migration_needed"] == 0:
        logger.info("No migration needed - all users are already in PostgreSQL")
        if status["incomplete_profiles"] > 0:
            logger.info(f"However, {status['incomplete_profiles']} profiles are incomplete and may need LLM re-extraction")
        return
    
    # Ask user for migration type
    print("\nMigration Options:")
    print("1. Basic migration (fast, no LLM extraction)")
    print("2. Advanced migration with LLM re-extraction (requires LLM service)")
    print("3. Check status only")
    print("4. Cleanup Redis data (after migration)")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        logger.info("Starting basic migration...")
        result = migrate_users_basic()
        logger.info(f"Basic migration result: {result}")
        
    elif choice == "2":
        logger.info("Advanced migration requires LLM service integration")
        logger.info("This would need to be run within the FastAPI context with MCP Mesh")
        logger.info("Consider using the basic migration for now")
        
    elif choice == "3":
        logger.info("Status check complete")
        
    elif choice == "4":
        result = cleanup_migrated_data()
        logger.info(f"Cleanup result: {result}")
        
    else:
        logger.error("Invalid choice")
        sys.exit(1)
    
    # Final status check
    logger.info("\nFinal migration status:")
    final_status = check_migration_status()
    logger.info(f"Final status: {final_status}")

if __name__ == "__main__":
    asyncio.run(main())