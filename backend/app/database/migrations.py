"""
Database migrations and reference data seeding.
"""

import logging
from sqlalchemy import text
from app.database.postgres import engine

logger = logging.getLogger(__name__)

def seed_reference_data():
    """Insert reference data if not exists - idempotent operation."""
    try:
        with engine.connect() as conn:
            # Employment types
            logger.info("Seeding employment types...")
            result = conn.execute(text("""
                SELECT COUNT(*) FROM employment_types WHERE type_code IN ('full-time', 'part-time', 'contract', 'internship')
            """)).fetchone()
            
            if result[0] == 0:
                conn.execute(text("""
                    INSERT INTO employment_types (type_code, display_name, description, active)
                    VALUES 
                        ('full-time', 'Full Time', 'Standard full-time employment', true),
                        ('part-time', 'Part Time', 'Part-time employment', true),
                        ('contract', 'Contract', 'Contractor/freelance work', true),
                        ('internship', 'Internship', 'Student internship program', true);
                """))
                logger.info("Inserted employment types")
            else:
                logger.info("Employment types already exist, skipping")
            
            # Company locations - SEI office locations  
            logger.info("Seeding SEI company locations...")
            
            # Check if any locations exist
            location_count = conn.execute(text("SELECT COUNT(*) FROM company_locations")).fetchone()[0]
            
            if location_count == 0:
                conn.execute(text("""
                    INSERT INTO company_locations (country, state, city, office_name, remote_allowed, active)
                    VALUES 
                        ('United Kingdom', NULL, 'London', 'London Office', false, true),
                        ('United States of America', 'Pennsylvania', 'Oaks', 'Oaks Office', false, true),
                        ('India', 'West Bengal', 'Kolkata', 'Kolkata Office', false, true),
                        ('Luxembourg', NULL, 'Luxembourg City', 'Luxembourg Office', false, true),
                        ('United States of America', 'New York', 'New York', 'New York Office', false, true),
                        ('United States of America', 'District of Columbia', 'Remote', 'Remote Office', true, true),
                        ('United States of America', 'Indiana', 'Indianapolis', 'Indianapolis Office', false, true),
                        ('Ireland', 'Dublin', 'Dublin 2', 'Dublin Office', false, true);
                """))
                logger.info("Inserted SEI company locations")
            else:
                logger.info("Company locations already exist, skipping")
            
            conn.commit()
            logger.info("Reference data seeding completed successfully")
            
    except Exception as e:
        logger.error(f"Failed to seed reference data: {e}")
        raise

def run_schema_migrations():
    """Run any pending schema migrations."""
    try:
        with engine.connect() as conn:
            # Add any schema changes here
            logger.info("Checking for schema migrations...")
            
            # Phase 1: Role schema updates
            conn.execute(text("""
                ALTER TABLE roles 
                ADD COLUMN IF NOT EXISTS confidence_score REAL DEFAULT 0.5;
            """))
            
            conn.execute(text("""
                ALTER TABLE roles 
                ADD COLUMN IF NOT EXISTS location_id INTEGER;
            """))
            
            conn.execute(text("""
                ALTER TABLE roles 
                ADD COLUMN IF NOT EXISTS employment_type_id INTEGER;
            """))
            
            # Phase 2: User profile schema updates for role matching
            logger.info("Adding Phase 2 profile columns...")
            
            conn.execute(text("""
                ALTER TABLE user_profiles 
                ADD COLUMN IF NOT EXISTS categories JSONB DEFAULT '[]';
            """))
            
            conn.execute(text("""
                ALTER TABLE user_profiles 
                ADD COLUMN IF NOT EXISTS experience_level VARCHAR(20);
            """))
            
            conn.execute(text("""
                ALTER TABLE user_profiles 
                ADD COLUMN IF NOT EXISTS years_experience INTEGER DEFAULT 0;
            """))
            
            conn.execute(text("""
                ALTER TABLE user_profiles 
                ADD COLUMN IF NOT EXISTS tags JSONB DEFAULT '[]';
            """))
            
            conn.execute(text("""
                ALTER TABLE user_profiles 
                ADD COLUMN IF NOT EXISTS professional_summary TEXT;
            """))
            
            conn.execute(text("""
                ALTER TABLE user_profiles 
                ADD COLUMN IF NOT EXISTS education_level VARCHAR(100);
            """))
            
            conn.execute(text("""
                ALTER TABLE user_profiles 
                ADD COLUMN IF NOT EXISTS confidence_score REAL DEFAULT 0.0;
            """))
            
            conn.execute(text("""
                ALTER TABLE user_profiles 
                ADD COLUMN IF NOT EXISTS profile_strength VARCHAR(20) DEFAULT 'average';
            """))
            
            conn.execute(text("""
                ALTER TABLE user_profiles 
                ADD COLUMN IF NOT EXISTS profile_version INTEGER DEFAULT 1;
            """))
            
            # Add foreign key constraints if they don't exist
            conn.execute(text("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.table_constraints 
                        WHERE constraint_name = 'fk_roles_location'
                    ) THEN
                        ALTER TABLE roles 
                        ADD CONSTRAINT fk_roles_location 
                        FOREIGN KEY (location_id) REFERENCES company_locations(id);
                    END IF;
                END $$;
            """))
            
            conn.execute(text("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.table_constraints 
                        WHERE constraint_name = 'fk_roles_employment_type'
                    ) THEN
                        ALTER TABLE roles 
                        ADD CONSTRAINT fk_roles_employment_type 
                        FOREIGN KEY (employment_type_id) REFERENCES employment_types(id);
                    END IF;
                END $$;
            """))
            
            # Phase 2: Add indexes for profile matching queries
            logger.info("Creating indexes for profile matching...")
            
            # Convert JSON columns to JSONB for better indexing
            logger.info("Converting JSON columns to JSONB...")
            conn.execute(text("""
                ALTER TABLE user_profiles 
                ALTER COLUMN categories TYPE JSONB USING categories::jsonb;
            """))
            
            conn.execute(text("""
                ALTER TABLE user_profiles 
                ALTER COLUMN tags TYPE JSONB USING tags::jsonb;
            """))
            
            # Now create GIN indexes on JSONB columns
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_profiles_categories 
                ON user_profiles USING GIN (categories);
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_profiles_tags 
                ON user_profiles USING GIN (tags);
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_profiles_experience 
                ON user_profiles (experience_level, years_experience);
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_user_profiles_complete 
                ON user_profiles (is_profile_complete);
            """))
            
            conn.commit()
            logger.info("Schema migrations completed successfully")
            
    except Exception as e:
        logger.error(f"Failed to run schema migrations: {e}")
        raise

def run_all_migrations():
    """Run all migrations - schema changes and reference data seeding."""
    logger.info("Starting database migrations...")
    run_schema_migrations()
    seed_reference_data()
    logger.info("All migrations completed successfully")