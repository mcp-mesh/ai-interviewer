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
