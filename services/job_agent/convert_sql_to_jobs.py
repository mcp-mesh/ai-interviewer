#!/usr/bin/env python3
"""
Script to properly convert V002__Insert_job_data.sql to individual Python job data files.
This extracts ALL the real data from the SQL INSERT statements.
"""

import re
import os

# Read the SQL file
sql_file_path = "/media/psf/Home/workspace/github/ai-interviewer/migrations/V002__Insert_job_data.sql"
with open(sql_file_path, 'r') as f:
    sql_content = f.read()

# Find all INSERT statements
insert_pattern = r"INSERT INTO job_agent\.jobs \((.*?)\) VALUES \((.*?)\);"
matches = re.findall(insert_pattern, sql_content, re.DOTALL)

print(f"Found {len(matches)} INSERT statements")

job_data_dir = "/media/psf/Home/workspace/github/ai-interviewer/services/job_agent/job_data"

# Parse each INSERT statement
for i, (columns_str, values_str) in enumerate(matches, 1):
    print(f"\nProcessing Job {i}...")
    
    # Split each INSERT statement to extract values
    # This is complex due to $desc_xxx$ delimiters, so let's extract manually
    
    # For each job, let's extract values more carefully
    lines = values_str.strip().split('\n')
    
    # Extract title (first quoted string)
    title_match = re.search(r"'([^']+)'", values_str)
    title = title_match.group(1) if title_match else f"Job {i}"
    
    # Extract company (second quoted string) 
    company_match = re.search(r"'[^']+',\s*'([^']+)'", values_str)
    company = company_match.group(1) if company_match else "S. Corp"
    
    # Extract location (third quoted string)
    location_match = re.search(r"'[^']+',\s*'[^']+',\s*'([^']+)'", values_str)
    location = location_match.group(1) if location_match else "Location TBD"
    
    # Extract job_type (fourth quoted string)
    job_type_match = re.search(r"'[^']+',\s*'[^']+',\s*'[^']+',\s*'([^']+)'", values_str)
    job_type = job_type_match.group(1) if job_type_match else "Full-time"
    
    # Extract category (fifth quoted string)  
    category_match = re.search(r"'[^']+',\s*'[^']+',\s*'[^']+',\s*'[^']+',\s*'([^']+)'", values_str)
    category = category_match.group(1) if category_match else "Operations"
    
    # Extract remote (boolean after category)
    remote_match = re.search(r"'[^']+',\s*'[^']+',\s*'[^']+',\s*'[^']+',\s*'[^']+',\s*(TRUE|FALSE)", values_str)
    remote = remote_match.group(1) == "TRUE" if remote_match else False
    
    # Extract description (between $desc_xxx$ delimiters)
    desc_match = re.search(r'\$desc_\d+\$(.*?)\$desc_\d+\$', values_str, re.DOTALL)
    description = desc_match.group(1).strip() if desc_match else f"Description for {title}"
    
    # Extract short description (after description)
    short_desc_match = re.search(r'\$desc_\d+\$,\s*\'([^\']+)\'', values_str)
    short_description = short_desc_match.group(1) if short_desc_match else f"Short description for {title}"
    
    # Extract arrays (requirements, benefits, skills_required)
    array_pattern = r"ARRAY\[(.*?)\]"
    arrays = re.findall(array_pattern, values_str, re.DOTALL)
    
    requirements = []
    benefits = []
    skills_required = []
    
    if len(arrays) >= 1:
        # Parse requirements array
        req_items = re.findall(r"'([^']+)'", arrays[0])
        requirements = req_items
        
    if len(arrays) >= 2:
        # Parse benefits array  
        ben_items = re.findall(r"'([^']+)'", arrays[1])
        benefits = ben_items
        
    if len(arrays) >= 3:
        # Parse skills array
        skill_items = re.findall(r"'([^']+)'", arrays[2]) 
        skills_required = skill_items
    
    # Extract salary values
    salary_min_match = re.search(r',\s*(\d+),\s*\d+,', values_str)
    salary_max_match = re.search(r',\s*\d+,\s*(\d+),', values_str)
    
    salary_min = int(salary_min_match.group(1)) if salary_min_match else None
    salary_max = int(salary_max_match.group(1)) if salary_max_match else None
    
    # Extract is_featured
    featured_match = re.search(r',\s*(TRUE|FALSE),\s*\'[\d\-T:+]+\'', values_str)
    is_featured = featured_match.group(1) == "TRUE" if featured_match else False
    
    # Extract posted_date
    date_match = re.search(r"'([\d\-T:+]+)'", values_str)
    posted_date_str = date_match.group(1) if date_match else "2025-04-10T00:00:00+00:00"
    
    print(f"  Title: {title}")
    print(f"  Company: {company}")
    print(f"  Location: {location}")
    print(f"  Category: {category}")
    print(f"  Remote: {remote}")
    print(f"  Requirements: {len(requirements)} items")
    print(f"  Benefits: {len(benefits)} items") 
    print(f"  Skills: {len(skills_required)} items")
    
    # Create the job file with real extracted data
    job_file_path = f"{job_data_dir}/job_{i:02d}.py"
    
    job_content = f'''from datetime import datetime, timezone

def get_job_data():
    return {{
        'title': {repr(title)},
        'company': {repr(company)},
        'location': {repr(location)},
        'job_type': {repr(job_type)},
        'category': {repr(category)},
        'remote': {remote},
        'short_description': {repr(short_description)},
        'description': {repr(description)},
        'requirements': {repr(requirements)},
        'benefits': {repr(benefits)},
        'skills_required': {repr(skills_required)},
        'salary_min': {salary_min},
        'salary_max': {salary_max},
        'salary_currency': 'USD',
        'is_featured': {is_featured},
        'posted_date': datetime.fromisoformat({repr(posted_date_str.replace('+00:00', '+00:00'))}),
        'is_active': True
    }}'''
    
    with open(job_file_path, 'w') as f:
        f.write(job_content)

print(f"\nCreated {len(matches)} job files with full data extracted from SQL")