#!/usr/bin/env python3
"""
Database initialization script for AI Interviewer PostgreSQL setup.
"""

import os
import sys
import logging
from datetime import datetime

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.postgres import db_manager, get_session
from app.models.database import Role, UserProfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_sample_roles():
    """Create sample roles for testing."""
    sample_roles = [
        {
            "title": "Senior Python Developer",
            "description": """We are looking for an experienced Python developer to join our backend team. 
            You will be responsible for building scalable APIs, working with databases, and implementing 
            microservices architecture. Experience with FastAPI, PostgreSQL, and cloud platforms is highly valued.""",
            "short_description": "Experienced Python developer for backend APIs and microservices architecture.",
            "category": "engineering",
            "type": "full-time",
            "country": "USA",
            "state": "California",
            "city": "San Francisco",
            "required_experience_level": "senior",
            "required_years_min": 5,
            "required_years_max": 12,
            "required_skills": {
                "python": {"level": "senior", "required": True, "years": 5},
                "fastapi": {"level": "mid", "required": True, "years": 2},
                "postgresql": {"level": "mid", "required": True, "years": 3},
                "docker": {"level": "mid", "required": False, "years": 2},
                "aws": {"level": "junior", "required": False, "years": 1}
            },
            "tags": ["backend", "api", "microservices", "python", "fastapi"],
            "status": "open",
            "duration": 45,
            "created_by": "admin@example.com",
            "updated_by": "admin@example.com"
        },
        {
            "title": "Frontend React Developer",
            "description": """Join our frontend team to build modern web applications using React and TypeScript. 
            You'll work on user interfaces, implement responsive designs, and collaborate with UX designers. 
            Experience with Next.js, state management, and testing frameworks is a plus.""",
            "short_description": "Frontend developer for modern React and TypeScript web applications.",
            "category": "engineering",
            "type": "full-time",
            "country": "USA",
            "state": "New York",
            "city": "New York",
            "required_experience_level": "mid",
            "required_years_min": 3,
            "required_years_max": 8,
            "required_skills": {
                "react": {"level": "senior", "required": True, "years": 3},
                "typescript": {"level": "mid", "required": True, "years": 2},
                "javascript": {"level": "senior", "required": True, "years": 4},
                "nextjs": {"level": "mid", "required": False, "years": 1},
                "css": {"level": "mid", "required": True, "years": 3}
            },
            "tags": ["frontend", "react", "typescript", "ui", "web"],
            "status": "open",
            "duration": 40,
            "created_by": "admin@example.com",
            "updated_by": "admin@example.com"
        },
        {
            "title": "Junior Data Scientist",
            "description": """Entry-level position for a data scientist to work on machine learning projects. 
            You'll analyze data, build predictive models, and create visualizations. Knowledge of Python, 
            pandas, scikit-learn, and SQL is required. This is a great opportunity for recent graduates.""",
            "short_description": "Entry-level data scientist for machine learning and analytics projects.",
            "category": "engineering",
            "type": "full-time",
            "country": "Canada",
            "state": "Ontario",
            "city": "Toronto",
            "required_experience_level": "junior",
            "required_years_min": 1,
            "required_years_max": 3,
            "required_skills": {
                "python": {"level": "mid", "required": True, "years": 2},
                "pandas": {"level": "mid", "required": True, "years": 1},
                "sql": {"level": "mid", "required": True, "years": 2},
                "machine learning": {"level": "junior", "required": True, "years": 1},
                "scikit-learn": {"level": "junior", "required": False, "years": 1}
            },
            "tags": ["data science", "machine learning", "python", "analytics"],
            "status": "open",
            "duration": 35,
            "created_by": "admin@example.com",
            "updated_by": "admin@example.com"
        },
        {
            "title": "Product Designer",
            "description": """We're seeking a talented product designer to create intuitive user experiences. 
            You'll work on wireframes, prototypes, and high-fidelity designs for web and mobile applications. 
            Proficiency in Figma, user research, and design systems is essential.""",
            "short_description": "Product designer for intuitive UX design and prototyping.",
            "category": "design",
            "type": "full-time",
            "country": "Remote",
            "state": None,
            "city": "Remote",
            "required_experience_level": "mid",
            "required_years_min": 3,
            "required_years_max": 7,
            "required_skills": {
                "figma": {"level": "senior", "required": True, "years": 3},
                "user research": {"level": "mid", "required": True, "years": 2},
                "prototyping": {"level": "mid", "required": True, "years": 3},
                "design systems": {"level": "mid", "required": False, "years": 2}
            },
            "tags": ["design", "ui", "ux", "figma", "product"],
            "status": "open",
            "duration": 30,
            "created_by": "admin@example.com",
            "updated_by": "admin@example.com"
        },
        {
            "title": "DevOps Engineer Intern",
            "description": """Internship opportunity to learn DevOps practices and cloud technologies. 
            You'll work with CI/CD pipelines, containerization, and infrastructure automation. 
            Basic knowledge of Linux, Git, and cloud platforms is preferred.""",
            "short_description": "DevOps internship for CI/CD pipelines and cloud infrastructure.",
            "category": "engineering",
            "type": "internship",
            "country": "USA",
            "state": "Texas",
            "city": "Austin",
            "required_experience_level": "intern",
            "required_years_min": 0,
            "required_years_max": 1,
            "required_skills": {
                "linux": {"level": "junior", "required": True, "years": 1},
                "git": {"level": "junior", "required": True, "years": 1},
                "docker": {"level": "beginner", "required": False, "years": 0},
                "aws": {"level": "beginner", "required": False, "years": 0}
            },
            "tags": ["devops", "cloud", "intern", "ci/cd", "automation"],
            "status": "open",
            "duration": 25,
            "created_by": "admin@example.com",
            "updated_by": "admin@example.com"
        }
    ]
    
    session = get_session()
    try:
        for role_data in sample_roles:
            # Check if role already exists
            existing = session.query(Role).filter(Role.title == role_data["title"]).first()
            if not existing:
                role = Role(**role_data)
                session.add(role)
                logger.info(f"Created sample role: {role_data['title']}")
        
        session.commit()
        logger.info("Sample roles created successfully")
        
    except Exception as e:
        logger.error(f"Error creating sample roles: {e}")
        session.rollback()
    finally:
        session.close()

def create_admin_user():
    """Create an admin user for testing."""
    admin_email = "admin@example.com"
    
    session = get_session()
    try:
        # Check if admin already exists
        existing = session.query(UserProfile).filter(UserProfile.email == admin_email).first()
        if not existing:
            admin_user = UserProfile(
                email=admin_email,
                name="Admin User",
                admin=True,
                is_profile_complete=True,
                skills={
                    "administration": {"level": "expert", "years": 10, "confidence": 1.0, "context": "System administration"},
                    "management": {"level": "senior", "years": 8, "confidence": 0.9, "context": "Team management"}
                },
                overall_experience_level="principal",
                total_years_experience=15,
                leadership_experience={
                    "has_leadership": True,
                    "team_size_managed": 20,
                    "leadership_years": 8,
                    "leadership_level": "director"
                }
            )
            session.add(admin_user)
            session.commit()
            logger.info(f"Created admin user: {admin_email}")
        else:
            logger.info(f"Admin user already exists: {admin_email}")
            
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        session.rollback()
    finally:
        session.close()

def main():
    """Main initialization function."""
    logger.info("Starting database initialization...")
    
    # Initialize database (create tables)
    if not db_manager.init_database():
        logger.error("Failed to initialize database")
        sys.exit(1)
    
    # Create sample data
    logger.info("Creating sample data...")
    create_admin_user()
    create_sample_roles()
    
    logger.info("Database initialization completed successfully!")
    logger.info("You can now:")
    logger.info("1. Start the FastAPI server")
    logger.info("2. Login as admin@example.com to manage roles")
    logger.info("3. Upload resumes to test skill extraction")
    logger.info("4. Test role matching algorithms")

if __name__ == "__main__":
    main()