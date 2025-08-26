#!/usr/bin/env python3
"""
Script to convert V002__Insert_job_data.sql to individual Python job data files.
This creates job_01.py through job_12.py in the job_data directory.
"""

import re
import os

# Read the SQL file
sql_file_path = "/media/psf/Home/workspace/github/ai-interviewer/migrations/V002__Insert_job_data.sql"
with open(sql_file_path, 'r') as f:
    sql_content = f.read()

# Extract all INSERT statements
insert_pattern = r"INSERT INTO job_agent\.jobs \((.*?)\) VALUES \((.*?)\);"
matches = re.findall(insert_pattern, sql_content, re.DOTALL)

print(f"Found {len(matches)} INSERT statements")

job_data_dir = "/media/psf/Home/workspace/github/ai-interviewer/services/job_agent/job_data"
os.makedirs(job_data_dir, exist_ok=True)

for i, (columns_str, values_str) in enumerate(matches, 1):
    # Parse column names
    columns = [col.strip() for col in columns_str.split(',')]
    
    # Parse values - this is complex due to multiline strings with $desc_xxx$ delimiters
    # For now, let's extract key values manually from the SQL for each job
    
    # Extract title (always the first value)
    title_match = re.search(r"'([^']+)'", values_str)
    title = title_match.group(1) if title_match else f"Job {i}"
    
    print(f"Creating job_{i:02d}.py for: {title}")
    
    # Create the job file
    job_file_path = f"{job_data_dir}/job_{i:02d}.py"
    
    # For now, create a template - we'll fill in the details manually for the key jobs
    job_content = f'''from datetime import datetime, timezone

def get_job_data():
    return {{
        'title': '{title}',
        'company': 'S. Corp',
        'location': 'Location TBD',
        'job_type': 'Full-time',
        'category': 'Operations',
        'remote': False,
        'short_description': 'Job description for {title}',
        'description': """## 🎯 About the Role
        
{title} at S. Corp. More details to be added.
        
## 💼 What You Will Do
- Key responsibilities TBD
        
## 🎓 Required Qualifications
- Requirements TBD
        
## 💰 Benefits
- Comprehensive benefits package""",
        'requirements': ['Requirements TBD'],
        'benefits': ['Benefits TBD'],
        'skills_required': ['Skills TBD'],
        'salary_min': None,
        'salary_max': None,
        'salary_currency': 'USD',
        'is_featured': {i <= 3},  # First 3 jobs are featured
        'posted_date': datetime(2025, 4, 10, tzinfo=timezone.utc),
        'is_active': True
    }}'''
    
    with open(job_file_path, 'w') as f:
        f.write(job_content)

print(f"Created {len(matches)} job files in {job_data_dir}")