#!/usr/bin/env python3
"""
Database module for Job Agent
Handles PostgreSQL connection and schema initialization
"""

import logging
import os
from typing import Optional, Dict, Any, List
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import asyncpg

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages PostgreSQL database connections and schema initialization"""
    
    def __init__(self):
        self.connection_string = self._build_connection_string()
        self.pool: Optional[asyncpg.Pool] = None
        
    def _build_connection_string(self) -> str:
        """Build PostgreSQL connection string from environment variables"""
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        database = os.getenv("POSTGRES_DB", "ai_interviewer")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "postgres")
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    async def initialize(self) -> bool:
        """Initialize database connection and run migrations"""
        try:
            logger.info("Initializing database connection...")
            
            # Create connection pool
            self.pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=2,
                max_size=10
            )
            
            logger.info("✅ Database connection pool created")
            
            # Run migrations
            await self._run_migrations()
            
            logger.info("✅ Database initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {str(e)}")
            return False
    
    async def _run_migrations(self):
        """Run database migrations (schema and data)"""
        try:
            async with self.pool.acquire() as conn:
                logger.info("Running database migrations...")
                
                # Run V001 - Schema creation
                await self._run_schema_migration(conn)
                
                # Run V002 - Data insertion (only if no data exists)
                await self._run_data_migration(conn)
                
                logger.info("✅ All migrations completed successfully")
                
        except Exception as e:
            logger.error(f"❌ Migration failed: {str(e)}")
            raise
    
    async def _run_schema_migration(self, conn):
        """Create database schema"""
        schema_sql = """
        -- V001__Create_job_agent_schema.sql
        -- Job Agent Database Schema

        CREATE SCHEMA IF NOT EXISTS job_agent;

        CREATE TABLE IF NOT EXISTS job_agent.jobs (
            -- Primary fields
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            title VARCHAR(255) NOT NULL,
            company VARCHAR(255) NOT NULL,
            location VARCHAR(255) NOT NULL,
            
            -- Job details
            job_type VARCHAR(50) NOT NULL CHECK (job_type IN ('Full-time', 'Part-time', 'Contract', 'Internship')),
            category VARCHAR(50) NOT NULL CHECK (category IN ('Engineering', 'Operations', 'Finance', 'Marketing', 'Sales', 'Other')),
            experience_level VARCHAR(50),
            remote BOOLEAN DEFAULT FALSE,
            
            -- Content (markdown)
            description TEXT NOT NULL,
            short_description VARCHAR(500),
            requirements TEXT[],
            benefits TEXT[],
            skills_required TEXT[],
            
            -- Compensation
            salary_min INTEGER,
            salary_max INTEGER, 
            salary_currency VARCHAR(10) DEFAULT 'USD',
            
            -- Status and metadata
            is_featured BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            posted_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            application_deadline TIMESTAMP WITH TIME ZONE,
            
            -- Company info
            company_size VARCHAR(50),
            company_industry VARCHAR(100),
            company_website VARCHAR(255),
            
            -- Audit fields
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );

        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_jobs_category ON job_agent.jobs(category);
        CREATE INDEX IF NOT EXISTS idx_jobs_location ON job_agent.jobs(location);
        CREATE INDEX IF NOT EXISTS idx_jobs_job_type ON job_agent.jobs(job_type);
        CREATE INDEX IF NOT EXISTS idx_jobs_posted_date ON job_agent.jobs(posted_date);
        CREATE INDEX IF NOT EXISTS idx_jobs_is_active ON job_agent.jobs(is_active);
        CREATE INDEX IF NOT EXISTS idx_jobs_is_featured ON job_agent.jobs(is_featured);

        -- Full text search index on title and description
        CREATE INDEX IF NOT EXISTS idx_jobs_search ON job_agent.jobs USING gin(to_tsvector('english', title || ' ' || description));
        """
        
        await conn.execute(schema_sql)
        logger.info("✅ Schema migration (V001) completed")
    
    async def _run_data_migration(self, conn):
        """Insert initial job data if not exists"""
        # Check if data already exists
        count = await conn.fetchval("SELECT COUNT(*) FROM job_agent.jobs WHERE company = 'S. Corp'")
        
        if count > 0:
            logger.info(f"📊 Job data already exists ({count} jobs), skipping data migration")
            return
        
        logger.info("🔄 Running data migration (V002)...")
        
        # Job data from converted files
        jobs_data = [
            {
                'title': 'Operations Analyst - Institutional Private Client',
                'company': 'S. Corp',
                'location': 'Oaks, Pennsylvania, United States of America',
                'job_type': 'Full-time',
                'category': 'Operations',
                'remote': False,
                'description': """## 🎯 About the Role

The Investment Manager Services Division (IMS) at S. Corp is growing rapidly and is seeking new members on our Institutional Private Client (IPC) team. Our primary goal is to provide exceptional administration servicing for our clients' assigned alternative investment funds, mutual funds, or ETFs. As an operations analyst, you will ensure the reconciliation of custodial and prime broker accounts are accurate.

## 💼 What You Will Do

### Reconciliation & Client Support
- Work closely with Account Administration, Trade Settlement, and Client Service teams to understand client portfolios and fund structures
- Perform various types of reconciliations to ensure data accuracy and meet client service expectations
- Research, escalate, and clear all outstanding cash and security differences
- Ensure accurate postings to our accounting system

### Process Management
- Follow established practices and procedures while recommending process improvements
- Partner with Client Service and various support teams on client requests
- Support preparation of Client Review Committee materials and client communications
- Learn and adopt new technologies and advancements to enhance client service

## 🎓 Required Qualifications

### Education & Experience
- **Education:** Bachelor's degree from a four-year college or university (Finance, Accounting, or Business preferred)
- **Experience:** 0-2 years of professional experience in financial services industry
- **Technical:** Strong Excel skills and proficiency in Microsoft Office Suite

### Skills & Attributes
- **Detail-oriented:** Strong attention to detail and accuracy in work product
- **Communication:** Excellent verbal and written communication skills
- **Analytical:** Strong analytical and problem-solving skills
- **Team Player:** Ability to work effectively in team environments
- **Adaptability:** Willingness to learn new systems and adapt to changing priorities

## 🌟 What We Value
- **Attention to Detail** | **Teamwork** | **Client Focus**
- **Innovation:** Drive process improvements and embrace new technologies
- **Values Alignment:** S. Corp Values of courage, integrity, collaboration, inclusion, connection and fun

## 💰 Benefits

Comprehensive benefits including competitive compensation, health insurance, retirement plans, professional development opportunities, flexible work arrangements, and access to employee resource groups.

---
**Equal Opportunity:** S. Corp is an Equal Opportunity Employer committed to diversity and inclusion.""",
                'requirements': [
                    'Bachelor''s degree from a four-year college or university (Finance, Accounting, or Business preferred)',
                    '0-2 years of professional experience in financial services industry',
                    'Strong Excel skills and proficiency in Microsoft Office Suite',
                    'Strong attention to detail and accuracy in work product',
                    'Excellent verbal and written communication skills',
                    'Strong analytical and problem-solving skills',
                    'Ability to work effectively in team environments',
                    'Willingness to learn new systems and adapt to changing priorities'
                ],
                'benefits': [
                    'Comprehensive benefits including competitive compensation',
                    'Health insurance and retirement plans',
                    'Professional development opportunities',
                    'Flexible work arrangements',
                    'Access to employee resource groups'
                ],
                'skills_required': ['Excel', 'Financial Services'],
                'salary_min': None,
                'salary_max': None,
                'salary_currency': 'USD',
                'is_featured': True,
                'posted_date': '2025-04-10T00:00:00Z',
                'is_active': True
            },
            # Additional jobs would be added here...
        ]
        
        # Insert jobs
        for job in jobs_data:
            await conn.execute("""
                INSERT INTO job_agent.jobs (
                    title, company, location, job_type, category, remote,
                    description, requirements, benefits, skills_required, 
                    salary_min, salary_max, salary_currency, is_featured, 
                    posted_date, is_active
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            """, 
                job['title'], job['company'], job['location'], job['job_type'],
                job['category'], job['remote'], job['description'], job['requirements'],
                job['benefits'], job['skills_required'], job['salary_min'], job['salary_max'],
                job['salary_currency'], job['is_featured'], job['posted_date'], job['is_active']
            )
        
        # For demo purposes, let's also execute the full V002 data migration
        # This ensures all 12 jobs are inserted
        await self._execute_v002_migration(conn)
        
        logger.info("✅ Data migration (V002) completed")
    
    async def _execute_v002_migration(self, conn):
        """Execute the full V002 data migration from generated SQL"""
        import os
        
        # Get current directory (should be the job_agent directory)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Try different possible paths for the migration file
        possible_paths = [
            os.path.join(current_dir, 'V002__Insert_job_data.sql'),
            os.path.join(current_dir, 'migrations', 'V002__Insert_job_data.sql'),
            'V002__Insert_job_data.sql',
            'migrations/V002__Insert_job_data.sql'
        ]
        
        v002_sql = None
        migration_path = None
        for path in possible_paths:
            try:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        v002_sql = f.read()
                    migration_path = path
                    logger.info(f"Found V002 migration file at: {path}")
                    break
            except Exception as e:
                logger.debug(f"Could not read {path}: {str(e)}")
                continue
                
        if v002_sql:
            # Execute the SQL (skip the DELETE statement for safety in initialization)
            # Only execute INSERT statements and UPDATE statements
            sql_statements = v002_sql.split(';')
            executed_count = 0
            for statement in sql_statements:
                statement = statement.strip()
                if statement and (statement.upper().startswith('INSERT') or statement.upper().startswith('UPDATE')):
                    try:
                        await conn.execute(statement)
                        executed_count += 1
                    except Exception as e:
                        logger.error(f"Error executing statement: {str(e)}")
                        # Continue with other statements
            
            logger.info(f"Executed {executed_count} SQL statements from V002 migration")
        else:
            logger.warning(f"V002 migration file not found. Searched paths: {possible_paths}")
            logger.warning("Jobs table will be empty - no demo data available")
    
    async def get_connection(self):
        """Get a database connection from the pool"""
        if not self.pool:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self.pool.acquire()
    
    async def close(self):
        """Close database connections"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connections closed")

# Global database manager instance
db_manager = DatabaseManager()