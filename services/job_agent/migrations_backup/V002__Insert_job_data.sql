-- V002__Insert_job_data.sql
-- Initial Job Data for Demo

-- Clear existing data
DELETE FROM job_agent.jobs WHERE company = 'S. Corp';

-- Insert job data
INSERT INTO job_agent.jobs (
    title, company, location, job_type, category, remote,
    description, short_description, requirements, benefits, skills_required, 
    salary_min, salary_max, salary_currency, is_featured, 
    posted_date, is_active
) VALUES (
    'Operations Analyst - Institutional Private Client',
    'S. Corp',
    'Oaks, Pennsylvania, United States of America',
    'Full-time',
    'Operations',
    FALSE,
    $desc_926$## 🎯 About the Role

The Investment Manager Services Division (IMS) at S. Corp is growing rapidly and is seeking new members on our Institutional Private Client (IPC) team. Our primary goal is to provide exceptional administration servicing for our clients' assigned alternative investment funds, mutual funds, or ETFs. As an operations analyst, you will ensure the reconciliation of custodial and prime broker accounts are accurate.

## 💼 What You Will Do

### Reconciliation & Client Support
- Work closely with Account Administration, Trade Settlement, and Client Service teams to understand client portfolios and fund structures
- Perform various types of reconciliations to ensure data accuracy and meet client service expectations
- Research, escalate, and clear all outstanding cash and security differences
- Ensure accurate postings to our accounting system
- Coordinate documentation of processes and procedures for individual client needs

### Communication & Problem-Solving
- Communicate with internal teams and client teams to resolve open issues and questions
- Collaborate with internal technology support and vendor support for production issues
- Participate in professional development sessions across IMS and corporate divisions
- Partner with diverse teams to grow your career and identify process improvements

## 🎓 Required Qualifications

- **Education:** BA/BS in Business, Accounting, Finance, Economics, Mathematics or equivalent experience
- **Experience:** Internship experience preferred
- **Technical Skills:** Intermediate Microsoft Excel proficiency
- **Core Competencies:**
  - Self-motivation and drive to complete multiple client objectives without sacrificing quality
  - Strong written and verbal communication skills for client support via email and phone
  - Excellent customer service skills for daily internal and external client communication

## 🌟 Preferred Qualities

- **Professional Growth:** Aim to broaden financial services industry knowledge through continuous learning
- **Collaboration:** Work effectively with internal and external stakeholders; adapt to changing client needs
- **Attitude:** Positive, supportive approach with strong teamwork abilities
- **Analytical Skills:** Curiosity, critical thinking, and attention to detail for problem-solving and process improvement
- **Values Alignment:** Embody S. Corp Values of courage, integrity, collaboration, inclusion, connection and fun

## 💰 Benefits & Compensation

### Comprehensive Benefits Package
- **Healthcare:** Medical, dental, vision, prescription, wellness, EAP, FSA
- **Insurance:** Life and disability insurance (premiums paid for base coverage)
- **Retirement:** 401(k) match, discounted stock purchase plan, investment options
- **Time Off:** Up to 11 paid holidays/year, 16 days PTO/year (increases over time), paid parental leave
- **Work-Life Balance:** Hybrid working environment, flexible PTO, back-up childcare arrangements
- **Professional Development:** Tuition reimbursement, education assistance
- **Additional Perks:** Commuter benefits, paid volunteer days, access to employee networks

## 🏢 About S. Corp

We are a technology and asset management company delivering on our promise of building brave futures—for our clients, our communities, and ourselves. After over 50 years in business, S. Corp remains a leading global provider of investment processing, investment management, and investment operations solutions.

### Our Work Environment
- Open floor plan offices with numerous art installations
- Designed to encourage innovation and creativity
- Focus on healthy, happy, and motivated workforce
- Investment in employee success through comprehensive support programs

---

**Note:** S. Corp is not hiring individuals who require sponsorship for employment or continued employment now or anytime in the future.

**Equal Opportunity:** S. Corp is an equal opportunity/affirmative action employer and all qualified applicants will receive consideration for employment without regard to race, color, religion, sex, sexual orientation, gender identity, national origin, age, disability status, protected veteran status, or any other characteristic protected by law.$desc_926$,
    'The Investment Manager Services Division (IMS) at S. Corp is growing rapidly and is seeking new members on our Institutional Private Client (IPC) team. Our primary goal is to provide exceptional administration servicing for our clients'' assigned alternative investment funds, mutual funds, or ETFs. As an operations analyst, you will ensure the reconciliation of custodial and prime broker accounts are accurate.',
    ARRAY['Education: BA/BS in Business, Accounting, Finance, Economics, Mathematics or equivalent experience', 'Experience: Internship experience preferred', 'Technical Skills: Intermediate Microsoft Excel proficiency', 'Core Competencies:', 'Self-motivation and drive to complete multiple client objectives without sacrificing quality', 'Strong written and verbal communication skills for client support via email and phone', 'Excellent customer service skills for daily internal and external client communication'],
    ARRAY['Healthcare: Medical, dental, vision, prescription, wellness, EAP, FSA', 'Insurance: Life and disability insurance (premiums paid for base coverage)', 'Retirement: 401(k) match, discounted stock purchase plan, investment options', 'Time Off: Up to 11 paid holidays/year, 16 days PTO/year (increases over time), paid parental leave', 'Work-Life Balance: Hybrid working environment, flexible PTO, back-up childcare arrangements', 'Professional Development: Tuition reimbursement, education assistance', 'Additional Perks: Commuter benefits, paid volunteer days, access to employee networks'],
    ARRAY['Fund Accounting', 'SSIS', 'Excel', 'GAAP', 'Financial Services', 'API'],
    NULL,
    NULL,
    'USD',
    FALSE,
    '2025-04-10T00:00:00+00:00',
    TRUE
);
INSERT INTO job_agent.jobs (
    title, company, location, job_type, category, remote,
    description, short_description, requirements, benefits, skills_required, 
    salary_min, salary_max, salary_currency, is_featured, 
    posted_date, is_active
) VALUES (
    'Fund Accountant - Investment Fund Services',
    'S. Corp',
    'Oaks, Pennsylvania, United States of America',
    'Full-time',
    'Finance',
    FALSE,
    $desc_139$## 🎯 About the Role

The Investment Manager Services Division (IMS) at S. Corp is growing rapidly and is seeking new members on our Investment Fund Services accounting team. Our primary goal is to provide exceptional accounting and administration servicing for our clients' assigned mutual funds, CITs, ETFs and other pooled vehicles. As a Fund Accountant, you will act as an intermediary between the funds and their investment managers and serve as the official record keeper for the funds.

## 💼 What You Will Do

### Daily Accounting Operations
- Calculate funds' daily investable cash, expenses, and income using your accounting skills
- Calculate and report funds' daily Net Asset Values (NAVs)
- Process shareholders' activity and perform timely reconciliations to fund transfer agents
- Communicate fund transactions and work closely with internal and external clients
- Provide accurate and thorough accounting packages

### Record Keeping & Compliance
- Act as official record keeper for assigned funds
- Support various year-end audit engagements in accordance with GAAP accounting standards
- Correspond with external investment managers on day-to-day fund inquiries
- Handle security trades, fee payments, cash position breaks, and reconciliations

### Professional Development
- Participate in IMS and corporate professional development sessions
- Acquire tools to identify processes across the division and organization
- Collaborate with diverse teams and grow your career

## 🎓 Required Qualifications

- **Education:** BA/BS in Accounting, Finance, Economics, Mathematics, or equivalent experience
- **Experience:** Internship experience preferred
- **Technical Skills:** Intermediate Microsoft Excel proficiency
- **Core Competencies:**
  - Self-motivation, organization and drive to complete multiple client deliverables timely without sacrificing quality
  - Strong written and verbal communication skills for client support via email and phone
  - Excellent customer service skills for daily client and service provider communication

## 🌟 Preferred Qualities

- **Industry Knowledge:** Broaden financial services industry knowledge through continuous learning and system mastery
- **Quality Focus:** Attention-to-detail ensuring all deliverables meet highest standards of quality and accuracy
- **Adaptability:** Collaborate with internal and external stakeholders; flexibility to adapt to changing client needs
- **Team Player:** Positive, congenial approach with strong teamwork abilities
- **Problem Solver:** Curiosity, critical thinking and attention to detail for process improvements
- **Values Alignment:** Embody S. Corp Values of courage, integrity, collaboration, inclusion, connection and fun

## 💰 Benefits & Compensation

### Comprehensive Benefits Package
- **Healthcare:** Medical, dental, vision, prescription, wellness, EAP, FSA
- **Insurance:** Life and disability insurance (premiums paid for base coverage)
- **Retirement:** 401(k) match, discounted stock purchase plan, investment options
- **Time Off:** Up to 11 paid holidays/year, 16 days PTO/year (increases over time), paid parental leave
- **Work-Life Balance:** Hybrid working environment, flexible PTO, back-up childcare arrangements
- **Professional Development:** Tuition reimbursement, education assistance
- **Additional Perks:** Commuter benefits, paid volunteer days, access to employee networks

## 🏢 About S. Corp

We are a technology and asset management company delivering on our promise of building brave futures—for our clients, our communities, and ourselves. After over 50 years in business, S. Corp remains a leading global provider of investment processing, investment management, and investment operations solutions.

### Our Work Environment
- Open floor plan offices with numerous art installations
- Designed to encourage innovation and creativity
- Focus on healthy, happy, and motivated workforce
- Investment in employee success through comprehensive support programs

---

**Note:** S. Corp is not hiring individuals who require sponsorship for employment or continued employment now or anytime in the future.

**Equal Opportunity:** S. Corp is an equal opportunity/affirmative action employer and all qualified applicants will receive consideration for employment without regard to race, color, religion, sex, sexual orientation, gender identity, national origin, age, disability status, protected veteran status, or any other characteristic protected by law.$desc_139$,
    'The Investment Manager Services Division (IMS) at S. Corp is growing rapidly and is seeking new members on our Investment Fund Services accounting team. Our primary goal is to provide exceptional accounting and administration servicing for our clients'' assigned mutual funds, CITs, ETFs and other pooled vehicles. As a Fund Accountant, you will act as an intermediary between the funds and their investment managers and serve as the official record keeper for the funds.',
    ARRAY['Education: BA/BS in Accounting, Finance, Economics, Mathematics, or equivalent experience', 'Experience: Internship experience preferred', 'Technical Skills: Intermediate Microsoft Excel proficiency', 'Core Competencies:', 'Self-motivation, organization and drive to complete multiple client deliverables timely without sacrificing quality', 'Strong written and verbal communication skills for client support via email and phone', 'Excellent customer service skills for daily client and service provider communication'],
    ARRAY['Healthcare: Medical, dental, vision, prescription, wellness, EAP, FSA', 'Insurance: Life and disability insurance (premiums paid for base coverage)', 'Retirement: 401(k) match, discounted stock purchase plan, investment options', 'Time Off: Up to 11 paid holidays/year, 16 days PTO/year (increases over time), paid parental leave', 'Work-Life Balance: Hybrid working environment, flexible PTO, back-up childcare arrangements', 'Professional Development: Tuition reimbursement, education assistance', 'Additional Perks: Commuter benefits, paid volunteer days, access to employee networks'],
    ARRAY['Fund Accounting', 'SSIS', 'Excel', 'Compliance', 'Data Privacy', 'Risk Management'],
    NULL,
    NULL,
    'USD',
    TRUE,
    '2025-04-10T00:00:00+00:00',
    TRUE
);
INSERT INTO job_agent.jobs (
    title, company, location, job_type, category, remote,
    description, short_description, requirements, benefits, skills_required, 
    salary_min, salary_max, salary_currency, is_featured, 
    posted_date, is_active
) VALUES (
    'Software Engineer I - SQL Developer',
    'S. Corp',
    'Kolkata, India',
    'Full-time',
    'Engineering',
    FALSE,
    $desc_847$## 🎯 About the Role

We are seeking a highly skilled and experienced SQL Developer with 2–4 years of experience to join our data team. This role requires a strong background in writing optimized SQL queries, designing data models, building ETL processes, and supporting analytics teams with reliable, high-performance data solutions. You will play a key role in ensuring data quality, integrity, and accessibility across the organization.

## 💼 What You Will Do

### Database Development & Optimization
- Develop, optimize, and maintain complex SQL queries, stored procedures, views, and functions
- Design and implement efficient data models and database objects to support applications and reporting needs
- Tune SQL queries and indexes to ensure high performance of large-scale datasets
- Assist in database deployments, migrations, and version control as part of the release process

### ETL & Data Processing
- Build, schedule, and monitor ETL processes for ingesting, transforming, and exporting data across systems
- Perform data profiling, validation, and cleansing activities to maintain data integrity
- Create and maintain technical documentation for data architecture, ETL workflows, and query logic

### Collaboration & Support
- Collaborate with business analysts and developers to understand data requirements
- Support ad-hoc data requests and report development for internal teams
- Work closely with analytics teams to provide reliable, high-performance data solutions

## 🎓 Required Qualifications

### Technical Requirements
- **Database Skills:** Strong command of Microsoft T-SQL development
- **Query Optimization:** Experience with writing and optimizing complex stored procedures and queries
- **Performance Tuning:** Experience with performance tuning and query optimization
- **Data Modeling:** Solid understanding of normalization, indexing, and relational data modeling
- **ETL Tools:** Familiarity with ETL tools like SSIS and data integration processes
- **Reporting Tools:** Familiarity with reporting tools like SSRS and/or Power BI

### Core Competencies
- Strong problem-solving skills and attention to detail
- Understanding of data governance, data quality, and security practices
- Excellent communication and collaboration skills

## 🌟 Preferred Qualifications

- **Education:** Bachelor's (or above) degree in Computer Science, Information Systems, Engineering, or a related field
- **Experience:** 2-4 years of experience in SQL development and relational database management
- **Values Alignment:** Embody S. Corp Values of courage, integrity, collaboration, inclusion, connection and fun

## 💰 Benefits & Compensation

### India-Specific Benefits Package
- **Healthcare:** Medical Insurance, Term Life Insurance
- **Retirement:** Voluntary Provident Fund
- **Time Off:** 10 Predefined Holidays and 2 Floating Holidays per year, Paid Time Off
- **Work-Life Balance:** Hybrid working environment
- **Professional Development:** Professional development assistance

## 🏢 About S. Corp

We are a technology and asset management company delivering on our promise of building brave futures—for our clients, our communities, and ourselves. After 50 years in business, S. Corp is a leading global provider of investment processing, investment management, and investment operations solutions.

### Our Work Environment
- Open floor plan offices with numerous art installations
- Designed to encourage innovation and creativity in our workforce
- Focus on healthy, happy, and motivated workforce for continued growth
- Investment in employee success through comprehensive support programs

---

**Equal Opportunity:** S. Corp is an Equal Opportunity Employer and all qualified applicants will receive consideration for employment without regard to race, color, religion, sex, sexual orientation, gender identity, national origin, age, disability status, protected veteran status, or any other characteristic protected by law.$desc_847$,
    'Join S. Corp''s growing team. We are seeking a highly skilled and experienced SQL Developer with 2–4 years of experience to join our data team. This role requires a strong background in writing optimized SQL queries, designing data models, building ETL processes, and supporting analytics teams with reliable, highperformance data solutions. You will play a key role in ensuring data quality, integrity, and accessibility across the organization.',
    ARRAY['Database Skills: Strong command of Microsoft T-SQL development', 'Query Optimization: Experience with writing and optimizing complex stored procedures and queries', 'Performance Tuning: Experience with performance tuning and query optimization', 'Data Modeling: Solid understanding of normalization, indexing, and relational data modeling', 'ETL Tools: Familiarity with ETL tools like SSIS and data integration processes', 'Reporting Tools: Familiarity with reporting tools like SSRS and/or Power BI', 'Strong problem-solving skills and attention to detail', 'Understanding of data governance, data quality, and security practices'],
    ARRAY['Healthcare: Medical Insurance, Term Life Insurance', 'Retirement: Voluntary Provident Fund', 'Time Off: 10 Predefined Holidays and 2 Floating Holidays per year, Paid Time Off', 'Work-Life Balance: Hybrid working environment', 'Professional Development: Professional development assistance'],
    ARRAY['T-SQL', 'Power BI', 'SSIS', 'Excel', 'SQL'],
    NULL,
    NULL,
    'USD',
    FALSE,
    '2025-05-09T00:00:00+00:00',
    TRUE
);
INSERT INTO job_agent.jobs (
    title, company, location, job_type, category, remote,
    description, short_description, requirements, benefits, skills_required, 
    salary_min, salary_max, salary_currency, is_featured, 
    posted_date, is_active
) VALUES (
    'Quantitative Developer - Investment Management',
    'S. Corp',
    'London, United Kingdom',
    'Full-time',
    'Engineering',
    FALSE,
    $desc_325$## 🎯 About the Role

Our Quantitative Investment Management (QIM) team manages over 50 equity strategies across a variety of geographies, investment styles and risk/return profiles. The team is experiencing strong asset and account growth, requiring further investment into people, data, and tools.

S. Corp is seeking to hire a Quantitative Developer to develop, enhance and support platforms and tools that facilitate signal research, portfolio construction, performance attribution and reporting.

## 💼 What You Will Do

### Infrastructure Development (40%)
- Design, develop, and maintain high-quality, scalable systems using industry best practices
- Apply SOLID principles and design patterns where applicable
- Enhance and optimize systems for equity factor modelling, portfolio construction, trading, and reporting

### Pipeline Optimization (20%)
- Identify and implement performance optimizations for data pipelines and processing workflows
- Work on data processing efficiency and system performance improvements

### Production Management (20%)
- Oversee the maintenance and operational stability of investment process systems
- Monitor and manage production jobs to ensure reliability

### Communication & Documentation (20%)
- Ensure comprehensive documentation for applications, including system architecture and design specifications
- Collaborate closely with senior developers to drive innovation and efficiency

## 🎓 Required Qualifications

### Technical Skills
- **Experience:** 3+ years of professional development experience in a commercial environment (preferably quant equity setup)
- **Programming:** Proficiency in Python (3.9+), with experience in system architecture and application development
- **Concurrency:** Good knowledge of multi-processing and multi-threaded programming
- **Design Principles:** Solid understanding of design patterns, SOLID principles, and unit testing practices
- **Database:** 2+ years of experience with SQL, including query optimization and execution plan analysis
- **DevOps:** Experience with auditing, CI/CD processes, Bitbucket (GitHub), Team City, setup and create pipelines
- **Data Management:** Proficiency in data modelling, data management processes, and data profiling

### Development Tools
- Experience in developing APIs and working with WebSockets
- Knowledge of React, Django, FastAPI, or equivalent technologies
- Previous experience with AirFlow, Linux shell commands and setup websites on IIS

## 🌟 Preferred Qualifications

### Education & Experience
- Bachelor's or Master's degree in a relevant field
- Creative and solutions-oriented, with ability to excel in fast-paced, self-starting environment

### Personal Qualities
- Exceptional analytical skills with strong attention to detail
- Strong problem-solving ability and results-driven mindset
- Collaborative and proactive approach, with a "roll-up-your-sleeves" attitude
- Ability to explain results and model features to non-technical audiences
- **Values Alignment:** Embody S. Corp Values of courage, integrity, collaboration, inclusion, connection and fun

## 💰 Benefits & Compensation

### UK-Specific Benefits Package
- **Healthcare:** Comprehensive care for physical and mental well-being, private medical care for you and your family
- **Pension:** Strong pension plan
- **Education:** Tuition reimbursement
- **Work-Life Balance:** Hybrid working environment, enhanced family leave
- **Time Off:** Volunteer days, access to thriving employee networks
- **Additional Perks:** Access to GPs online for appointments, free fruit

## 🏢 About S. Corp

We are a technology and asset management company delivering on our promise of building brave futures—for our clients, our communities, and ourselves. After over 50 years, S. Corp remains a leading global provider of investment management, investment processing and investment operations solutions.

### Our UK Office Environment
- **Location:** Based between the City of London and the growing technology hub of Shoreditch
- **Design:** Open plan office space with flowing lines and numerous art installations
- **Culture:** Designed to encourage innovation and creativity in our workforce
- **Focus:** Healthy work-life balance with comprehensive employee benefits

---

**Regulatory Note:** S. Corp Investments (Europe) Ltd ('SIEL') is authorised and regulated by the Financial Conduct Authority (FRN 191713).

**Equal Opportunity:** S. Corp is an Equal Opportunity Employer and all qualified applicants will receive consideration for employment without regard to race, color, religion, sex, sexual orientation, gender identity, national origin, age, disability status, protected veteran status, or any other characteristic protected by law.$desc_325$,
    'Our Quantitative Investment Management (QIM) team manages over 50 equity strategies across a variety of geographies, investment styles and risk/return profiles. The team is experiencing strong asset and account growth, requiring further investment into people, data, and tools. S. Corp is seeking to hire a Quantitative Developer to develop, enhance and support platforms and tools that facilitate signal research, portfolio construction, performance attribution and reporting.',
    ARRAY['Experience: 3+ years of professional development experience in a commercial environment (preferably quant equity setup)', 'Programming: Proficiency in Python (3.9+), with experience in system architecture and application development', 'Concurrency: Good knowledge of multi-processing and multi-threaded programming', 'Design Principles: Solid understanding of design patterns, SOLID principles, and unit testing practices', 'Database: 2+ years of experience with SQL, including query optimization and execution plan analysis', 'DevOps: Experience with auditing, CI/CD processes, Bitbucket (GitHub), Team City, setup and create pipelines', 'Data Management: Proficiency in data modelling, data management processes, and data profiling', 'Experience in developing APIs and working with WebSockets'],
    ARRAY['Healthcare: Comprehensive care for physical and mental well-being, private medical care for you and your family', 'Pension: Strong pension plan', 'Education: Tuition reimbursement', 'Work-Life Balance: Hybrid working environment, enhanced family leave', 'Time Off: Volunteer days, access to thriving employee networks', 'Additional Perks: Access to GPs online for appointments, free fruit'],
    ARRAY['GitHub', 'Excel', 'Python', 'Linux', 'React', 'FastAPI'],
    NULL,
    NULL,
    'USD',
    FALSE,
    '2025-02-25T00:00:00+00:00',
    TRUE
);
INSERT INTO job_agent.jobs (
    title, company, location, job_type, category, remote,
    description, short_description, requirements, benefits, skills_required, 
    salary_min, salary_max, salary_currency, is_featured, 
    posted_date, is_active
) VALUES (
    'EMEA Sales Executive - Private Equity Fund Administration',
    'S. Corp',
    'Luxembourg City, Luxembourg',
    'Full-time',
    'Finance',
    FALSE,
    $desc_585$## 🎯 About the Role

The S. Corp Luxembourg team is seeking a Sales Executive to focus on our global sales strategy in EMEA. This position will be responsible for managing the sales process for our complete service and solutions offering for private equity funds—developing a pipeline, managing client relationships and providing input as to the future direction of our business in this market.

## 💼 What You Will Do

### Sales & Business Development
- Execute assigned marketing and sales plan for European private asset administration services (UK, Ireland, Scandinavia, Channel Islands, Luxembourg)
- Identify, qualify and pursue new business prospects, generate proposals and quotes
- Work with internal and external counterparts to close sales
- Build and maintain credible relationships with prospects, clients and industry "Centers of Influence"

### Industry Expertise & Market Intelligence
- Demonstrate clear understanding of prospect business needs and S. Corp's services and solutions
- Possess and maintain deep knowledge of the European private equity management industry
- Attend industry-related trade shows, seminars, and conferences
- Monitor evolution of market conditions, regulations, S. Corp products and services

### Data Management & Compliance
- Maintain and update internal systems/data reference points in agreed format
- Ensure consistency and communication of relevant information within the team
- Adhere to all relevant CSSF requirements for compliance

## 🎓 Required Qualifications

### Education & Experience
- **Education:** BA/BS in Business, Accounting, Finance or equivalent professional experience
- **Industry Experience:** Extensive experience in the private equity industry, especially:
  - Expertise in sales, marketing or relationship management with private equity manager
  - Sales or senior operations with 3rd party private equity manager or administrator
  - Private equity law or audit firm experience

### Sales & Communication Skills
- Broad-based knowledge and demonstrated ability to establish and manage sales process
- Experience from lead generation to relationship management and prospect pipeline nurturing
- Ability to drive agenda and adapt to fast-paced, challenging sales environment
- Tactful, effective and persuasive communication skills (verbal and written)
- Willingness to travel extensively throughout Europe

## 🌟 Preferred Qualities

- **Results-Oriented:** Capacity to deliver results independently and collaborate seamlessly
- **Cross-functional Collaboration:** Work effectively in multi-cultural team environment
- **Continuous Learning:** Initiative to broaden industry knowledge and apply it daily
- **Process-Driven:** Methodical approach to completing assigned tasks
- **Strategic Thinking:** Superior analytical, strategic and critical thinking skills
- **Attention to Detail:** Meticulous organization and attention to detail
- **Values Alignment:** Embody S. Corp Values of courage, integrity, collaboration, inclusion, connection and fun

## 🏢 About S. Corp & S. Corp Lux

**S. Corp (NASDAQ:SEIC)** delivers technology and investment solutions that connect the financial services industry. With capabilities across investment processing, operations, and asset management, S. Corp works with corporations, financial institutions and professionals, and ultra-high-net-worth families to help drive growth, make confident decisions, and protect futures. As of June 30, 2023, S. Corp manages, advises, or administers approximately $1.3 trillion in assets.

**S. Corp Investments - S.A. ("S. Corp Lux")** is S. Corp's Luxembourg-based European subsidiary, a specialized PSF, authorised and regulated by the Commission de Surveillance du Secteur Financier ("CSSF") (B257752), providing administrative and transfer agency services to Luxembourg investment funds.

---

**Background Check Required:** This position will require a successful background check, including employment verification, education verification and criminal history review, once an offer has been extended and accepted.

**Equal Opportunity:** S. Corp is an equal opportunity employer and all qualified applicants will receive consideration for employment without regard to race, color, religion, sex, sexual orientation, gender identity, national origin, age, disability status, protected veteran status, or any other characteristic protected by law.$desc_585$,
    'The S. Corp Luxembourg team is seeking a Sales Executive to focus on our global sales strategy in EMEA. This position will be responsible for managing the sales process for our complete service and solutions offering for private equity funds—developing a pipeline, managing client relationships and providing input as to the future direction of our business in this market.',
    ARRAY['Education: BA/BS in Business, Accounting, Finance or equivalent professional experience', 'Industry Experience: Extensive experience in the private equity industry, especially:', 'Expertise in sales, marketing or relationship management with private equity manager', 'Sales or senior operations with 3rd party private equity manager or administrator', 'Private equity law or audit firm experience', 'Broad-based knowledge and demonstrated ability to establish and manage sales process', 'Experience from lead generation to relationship management and prospect pipeline nurturing', 'Ability to drive agenda and adapt to fast-paced, challenging sales environment'],
    NULL,
    ARRAY['Fund Accounting', 'Compliance', 'Data Privacy', 'Risk Management', 'GAAP', 'Financial Services'],
    NULL,
    NULL,
    'USD',
    FALSE,
    '2025-05-29T00:00:00+00:00',
    TRUE
);
INSERT INTO job_agent.jobs (
    title, company, location, job_type, category, remote,
    description, short_description, requirements, benefits, skills_required, 
    salary_min, salary_max, salary_currency, is_featured, 
    posted_date, is_active
) VALUES (
    'Senior Business Analyst - Wealth Platform Implementation',
    'S. Corp',
    'London, United Kingdom',
    'Full-time',
    'Operations',
    FALSE,
    $desc_460$## 🎯 About the Role
The SWP Change Team (UK) is accountable for the success of all implementation and conversion activities within the S. Corp (UK) Private Banking Wealth Platform Business. As a Senior BA, you will lead specific projects and/or key workstreams in larger programmes, working with cross-functional stakeholders internally and externally.

## 💼 Key Responsibilities
- Serve as S. Corp Wealth Platform subject matter expert for operational, middle & front office workflows
- Assist clients with policy decisions, post-conversion organization structure, and impact analysis
- Evaluate effectiveness of testing in Model Office environment and during Dress Rehearsals
- Define, manage and deliver key change programmes through full project lifecycle
- Build effective relationships with key stakeholders and ensure project adherence to PMO Standards

## 🎓 Required Qualifications
- **Education:** Ideally degree educated (or equivalent) with Wealth Management or Private Banking industry experience
- **Experience:** Significant experience delivering projects within financial services environment
- **Skills:** Comfortable in ambiguous environments, proactive/self-starter mentality
- **Technical:** Experience with agile software environment, platform technology (advantageous)
- **Certifications:** Prince 2, Agile PM or similar qualification (advantageous)

## 🌟 What We're Looking For
- Attention to detail | Teamwork | Tenacity and Perseverance
- Innovation mindset for change and improvement at all levels
- Values alignment with S. Corp Values of courage, integrity, collaboration, inclusion, connection and fun

## 💰 Benefits
**UK-Specific Package:** Comprehensive care for physical and mental well-being, strong pension plan, tuition reimbursement, hybrid working environment, private medical care, enhanced family leave, volunteer days, access to employee networks.

---
**Regulatory:** S. Corp Investments (Europe) Ltd is authorised and regulated by the Financial Conduct Authority (FRN 191713).$desc_460$,
    'The SWP Change Team (UK) is accountable for the success of all implementation and conversion activities within the S. Corp (UK) Private Banking Wealth Platform Business. As a Senior BA, you will lead specific projects and/or key workstreams in larger programmes, working with crossfunctional stakeholders internally and externally.',
    ARRAY['Education: Ideally degree educated (or equivalent) with Wealth Management or Private Banking industry experience', 'Experience: Significant experience delivering projects within financial services environment', 'Skills: Comfortable in ambiguous environments, proactive/self-starter mentality', 'Technical: Experience with agile software environment, platform technology (advantageous)', 'Certifications: Prince 2, Agile PM or similar qualification (advantageous)'],
    NULL,
    ARRAY['Agile', 'SSIS'],
    NULL,
    NULL,
    'USD',
    FALSE,
    '2025-06-16T00:00:00+00:00',
    TRUE
);
INSERT INTO job_agent.jobs (
    title, company, location, job_type, category, remote,
    description, short_description, requirements, benefits, skills_required, 
    salary_min, salary_max, salary_currency, is_featured, 
    posted_date, is_active
) VALUES (
    'Business Development Director - S. Corp Wealth Platform',
    'S. Corp',
    'London, United Kingdom',
    'Full-time',
    'Sales',
    FALSE,
    $desc_565$## 🎯 About the Role
S. Corp's Private Banking & Wealth Management business is seeking an outstanding Sales professional as a Business Development Director. You will establish, build and close new business sales opportunities with a core focus on the UK market, targeting wealth managers such as Private Banks, Advisers and Private Client Investment Managers.

## 💼 What You Will Do
- Use outstanding relationship skills and existing network to maximize current relationships and develop new ones
- Execute consultative sales process from prospecting through closing new business
- Position S. Corp and enterprise capabilities including the S. Corp Wealth Platform (SWP)
- Attend networking and industry events, provide market intelligence
- Liaise with internal teams (Marketing, Solutions, PMO, legal, Relationship Managers)

## 🎓 Required Qualifications
- **Experience:** Proven track record in Business Development with executive-level relationships in financial services
- **Market Knowledge:** Understanding of UK Wealth Management market, technology, operations and asset management
- **Network:** Strong existing network within the market
- **Sales Experience:** Experience with procurement/decision making processes within Wealth Managers
- **Success Record:** Proven success managing and closing high-value outsourcing arrangements

## 🌟 Regulatory Categories
- **SMCR Category:** Certified role subject to Senior Manager and Certification Regime Rules (FCA)
- **MiFID II Category:** Staff giving information about investment products and services

## 🏢 About S. Corp Wealth Platform
The Platform supports trading and transactions on 156 stock exchanges in 58 countries and 51 currencies, through straight-through processing and single operating infrastructure environment as of June 30, 2024.

---
**Regulatory:** S. Corp Investments (Europe) Ltd is authorised and regulated by the Financial Conduct Authority (FRN 191713).$desc_565$,
    'S. Corp''s Private Banking & Wealth Management business is seeking an outstanding Sales professional as a Business Development Director. You will establish, build and close new business sales opportunities with a core focus on the UK market, targeting wealth managers such as Private Banks, Advisers and Private Client Investment Managers.',
    ARRAY['Experience: Proven track record in Business Development with executive-level relationships in financial services', 'Market Knowledge: Understanding of UK Wealth Management market, technology, operations and asset management', 'Network: Strong existing network within the market', 'Sales Experience: Experience with procurement/decision making processes within Wealth Managers', 'Success Record: Proven success managing and closing high-value outsourcing arrangements'],
    NULL,
    NULL,
    NULL,
    NULL,
    'USD',
    TRUE,
    '2024-11-27T00:00:00+00:00',
    TRUE
);
INSERT INTO job_agent.jobs (
    title, company, location, job_type, category, remote,
    description, short_description, requirements, benefits, skills_required, 
    salary_min, salary_max, salary_currency, is_featured, 
    posted_date, is_active
) VALUES (
    'Supervisor - Private Equity / Hedge Funds (REMOTE)',
    'S. Corp',
    'Remote, Pennsylvania, United States of America',
    'Full-time',
    'Operations',
    TRUE,
    $desc_946$## 🎯 About the Role

The Investment Manager Services Division (IMS) at S. Corp is growing rapidly and is seeking new members on our Alternative Investment Funds team. Our primary goal is to provide exceptional customer service and administration servicing for our clients' assigned hedge and private equity funds. As a Fund Accounting Supervisor, you will act as an intermediary between the funds and their investment managers and serve as the official record keeper for the funds. You will also train and supervise the accounting analysts on the team.

## 💼 What You Will Do

### Fund Accounting & Reconciliation
- Use your accounting skills to price and maintain timely records for hedge and private equity holdings using various external pricing resources
- Perform timely reconciliations regarding Net Asset Values and provide accounting reports
- Communicate transactions associated with the funds and work closely with internal and external clients
- Provide accurate and thorough accounting packages

### Compliance & Audit Support
- Coordinate and support various year-end audit engagements in accordance with GAAP accounting standards
- Perform due-diligence to ensure clients are in compliance with government laws and regulations
- Serve as official record keeper for assigned funds

### Team Leadership & Development
- Train and supervise accounting analysts on systems, processing, procedures, and job responsibilities
- Assist in managing a team environment that encourages self-motivation, organization and drive
- Conduct performance appraisals and monthly one-on-ones with team analysts
- Provide career pathing and training opportunities
- Participate in analyst interviews to ensure proper staffing
- Foster team environment including individual development, promotions and disciplinary action

### Client Relations & Problem Solving
- Correspond with external investment managers regarding day-to-day fund inquiries
- Handle reconciliations, coordinate scheduled deliverables, and manage escalation concerns
- Ensure client engagement and dedication to quality service
- Participate in professional development sessions to identify process improvements

## 🎓 Required Qualifications

### Education & Experience
- **Education:** BA/BS in Business, Accounting, Finance, Economics, Mathematics or equivalent professional experience
- **Industry Experience:** Minimum 2 years experience in the fund services industry (alternatives experience preferred)
- **Technical Skills:** Intermediate Microsoft Excel skills

### Core Competencies
- Self-motivation, organization and drive to complete multiple client deliverables timely without sacrificing quality
- Strong written and verbal communication skills for client support via email and phone
- Excellent customer service skills for daily client and service provider communication

## 🌟 Preferred Qualities

### Professional Development
- Drive to broaden financial services industry knowledge through continuous learning
- Initiative to apply new concepts and systems to daily work assignments

### Leadership & Collaboration
- Attention-to-detail ensuring all deliverables meet highest standards of quality and accuracy
- Collaborate effectively with internal and external stakeholders
- Flexibility to adapt to changing client needs
- Positive, collegial approach with strong teamwork abilities

### Problem-Solving Skills
- Curiosity, critical thinking and attention to detail for identifying solutions
- Ability to implement more efficient processes or procedures
- **Values Alignment:** Embody S. Corp Values of courage, integrity, collaboration, inclusion, connection and fun

## 💰 Benefits & Compensation

### Salary Range
- **Base Salary:** $70,000 - $112,000 per year
- **Bonus:** Eligible for discretionary annual bonus (subject to company approval)

### Comprehensive Benefits Package
- **Healthcare:** Medical, dental, vision, prescription, wellness, EAP, FSA
- **Insurance:** Life and disability insurance (premiums paid for base coverage)
- **Retirement:** 401(k) match, discounted stock purchase plan, investment options
- **Time Off:** Up to 11 paid holidays/year, 21 days PTO/year (increases over time), paid parental leave
- **Work-Life Balance:** Remote work environment, flexible PTO, back-up childcare arrangements
- **Professional Development:** Tuition reimbursement, education assistance
- **Additional Perks:** Commuter benefits, paid volunteer days, access to employee networks

## 🏢 About S. Corp

We are a technology and asset management company delivering on our promise of building brave futures—for our clients, our communities, and ourselves. After over 50 years in business, S. Corp remains a leading global provider of investment processing, investment management, and investment operations solutions.

### Our Work Culture
- Investment in employee success with comprehensive support programs
- Focus on healthy, happy, and motivated workforce
- Commitment to work-life balance and professional growth
- Access to thriving employee networks and development opportunities

---

**Equal Opportunity:** S. Corp is an equal opportunity employer and all qualified applicants will receive consideration for employment without regard to race, color, religion, sex, sexual orientation, gender identity, national origin, age, disability status, protected veteran status, or any other characteristic protected by law.$desc_946$,
    'The Investment Manager Services Division (IMS) at S. Corp is growing rapidly and is seeking new members on our Alternative Investment Funds team. Our primary goal is to provide exceptional customer service and administration servicing for our clients'' assigned hedge and private equity funds. As a Fund Accounting Supervisor, you will act as an intermediary between the funds and their investment managers and serve as the official record keeper for the funds. You will also train and super',
    ARRAY['Education: BA/BS in Business, Accounting, Finance, Economics, Mathematics or equivalent professional experience', 'Industry Experience: Minimum 2 years experience in the fund services industry (alternatives experience preferred)', 'Technical Skills: Intermediate Microsoft Excel skills', 'Self-motivation, organization and drive to complete multiple client deliverables timely without sacrificing quality', 'Strong written and verbal communication skills for client support via email and phone', 'Excellent customer service skills for daily client and service provider communication'],
    ARRAY['Base Salary: $70,000 - $112,000 per year', 'Bonus: Eligible for discretionary annual bonus (subject to company approval)', 'Healthcare: Medical, dental, vision, prescription, wellness, EAP, FSA', 'Insurance: Life and disability insurance (premiums paid for base coverage)', 'Retirement: 401(k) match, discounted stock purchase plan, investment options', 'Time Off: Up to 11 paid holidays/year, 21 days PTO/year (increases over time), paid parental leave', 'Work-Life Balance: Remote work environment, flexible PTO, back-up childcare arrangements', 'Professional Development: Tuition reimbursement, education assistance'],
    ARRAY['Fund Accounting', 'SSIS', 'Excel', 'Compliance', 'Data Privacy', 'Risk Management'],
    70000,
    112000,
    'USD',
    FALSE,
    '2025-05-28T00:00:00+00:00',
    TRUE
);
INSERT INTO job_agent.jobs (
    title, company, location, job_type, category, remote,
    description, short_description, requirements, benefits, skills_required, 
    salary_min, salary_max, salary_currency, is_featured, 
    posted_date, is_active
) VALUES (
    'Supervisor - Alternative Investment Funds (HYBRID)',
    'S. Corp',
    'Oaks, Pennsylvania, United States of America',
    'Full-time',
    'Operations',
    FALSE,
    $desc_285$## 🎯 About the Role
The Investment Manager Services Division (IMS) at S. Corp is growing rapidly and seeking new members on our Alternative Investment Funds team. As a Fund Accounting Supervisor, you will act as intermediary between funds and investment managers, serve as official record keeper, and train/supervise accounting analysts.

## 💼 Key Responsibilities
### Fund Accounting & Compliance
- Price and maintain timely records for hedge and private equity holdings using external pricing resources
- Perform timely reconciliations regarding Net Asset Values and provide accounting reports
- Support year-end audit engagements in accordance with GAAP accounting standards

### Team Leadership
- Train and supervise accounting analysts on systems, processing, procedures, and responsibilities
- Conduct performance appraisals and monthly one-on-ones with team analysts
- Participate in analyst interviews and foster team environment for development

## 🎓 Required Qualifications
- **Education:** BA/BS in Business, Accounting, Finance, Economics, Mathematics or equivalent
- **Experience:** Minimum 2 years in fund services industry (alternatives experience preferred)
- **Technical:** Intermediate Microsoft Excel skills
- **Communication:** Strong written/verbal skills for client support and service

## 💰 Benefits
Comprehensive benefits including healthcare, 401(k) match, up to 11 paid holidays/year, 21 days PTO/year (increases over time), hybrid working environment, tuition reimbursement, and access to employee networks.

---
**Values:** Embody S. Corp Values of courage, integrity, collaboration, inclusion, connection and fun.$desc_285$,
    'The Investment Manager Services Division (IMS) at S. Corp is growing rapidly and seeking new members on our Alternative Investment Funds team. As a Fund Accounting Supervisor, you will act as intermediary between funds and investment managers, serve as official record keeper, and train/supervise accounting analysts.',
    ARRAY['Education: BA/BS in Business, Accounting, Finance, Economics, Mathematics or equivalent', 'Experience: Minimum 2 years in fund services industry (alternatives experience preferred)', 'Technical: Intermediate Microsoft Excel skills', 'Communication: Strong written/verbal skills for client support and service'],
    NULL,
    ARRAY['Fund Accounting', 'Excel', 'Compliance', 'Data Privacy', 'Risk Management', 'GAAP'],
    NULL,
    NULL,
    'USD',
    FALSE,
    '2025-05-28T00:00:00+00:00',
    TRUE
);
INSERT INTO job_agent.jobs (
    title, company, location, job_type, category, remote,
    description, short_description, requirements, benefits, skills_required, 
    salary_min, salary_max, salary_currency, is_featured, 
    posted_date, is_active
) VALUES (
    'Privacy Analyst - Data Governance & Compliance',
    'S. Corp',
    'Oaks, Pennsylvania, United States of America',
    'Full-time',
    'Operations',
    FALSE,
    $desc_409$## 🎯 About the Role

As a Data Privacy Analyst, you will be a member of the S. Corp Legal, Compliance, and Corporate Development Department, working with legal and compliance professionals while partnering with business unit, operational, and technical colleagues.

S. Corp's Privacy Office is responsible for the governance of personal, confidential, and proprietary data processed by S. Corp. You will help implement and promote that governance by applying the S. Corp Privacy Program Framework across assigned business areas or technical domains.

## 💼 What You Will Do

### Strategic Governance & Legal Oversight
- **Data Governance:** Support activities by defining and enforcing controls related to data access, classification, retention, and minimization
- **Compliance Framework:** Ensure personal, confidential, and proprietary data processing aligns with S. Corp's Privacy Program Framework
- **Regulatory Analysis:** Analyze and implement governance controls for data processing in accordance with contractual obligations and public interest

### Legal & Regulatory Expertise
Apply knowledge and understanding of comprehensive privacy laws:

#### U.S. Privacy Laws
- California Consumer Privacy Act (CCPA) and California Privacy Rights Act (CPRA)
- Gramm-Leach-Bliley Act (GLBA)
- SEC Regulation S-P

#### International Frameworks
- EU's General Data Protection Regulation (GDPR)
- Canada's Personal Information Protection and Electronic Documents Act (PIPEDA)

#### Emerging AI Governance
- European Union's Artificial Intelligence Act (AI Act)
- Colorado Artificial Intelligence Act (SB24-205)
- Requirements for transparency, risk management, and accountability in high-risk AI systems

### Operational Execution & Documentation
- **Research & Assessment:** Critically assess and document processing activities in records of processing
- **Impact Assessments:** Conduct data protection impact assessments (DPIAs) and privacy impact assessments (PIAs)
- **Platform Management:** Record findings and technical/organizational measures in OneTrust enterprise privacy platform
- **Vendor Assessment:** Complete vendor assessment questionnaires

### Collaboration & Program Leadership
- **Cross-functional Collaboration:** Work with Information Security and Third Party Vendor Management teams
- **Executive Support:** Support the Chief Privacy Officer (CPO) in discussions with subject matter experts
- **Initiative Leadership:** Take ownership of assigned privacy initiatives and lead specific workstreams independently
- **Process Improvement:** Document recommendations for data privacy compliance improvements
- **Stakeholder Engagement:** Lead group discussions and working groups promoting data privacy governance

## 🎓 Required Qualifications

### Professional Experience
- **Data Governance:** Proven experience in data processing analysis through large-scale governance, compliance and regulatory initiatives
- **Process Management:** Demonstrated ability to produce standardized process mapping ("As Is" vs "To Be")
- **Enterprise Programs:** Experience building, deploying and managing data privacy programs in global enterprises
- **Privacy Platforms:** Experience using enterprise data privacy platforms such as OneTrust

### Technical & Project Management Skills
- **Privacy & Security:** Proven ability to understand and apply data privacy and information security knowledge
- **Project Management:** Knowledge of Agile, PPM and/or Prince II methodologies
- **Facilitation:** Strong meeting and large group facilitation skills for multi-disciplined workshops
- **Microsoft Office:** Proficiency including Visio

### Core Competencies
- **Organization:** Excellent organizational skills
- **Adaptability:** Quick learner able to thrive in fast-paced, ever-changing business services environment
- **Self-Direction:** Self-starter with ability to prioritize and multitask under pressure with tight deadlines
- **Communication:** Strong writing and communication skills
- **Interpersonal:** Exceptional skills including ability to collaborate and influence at various organizational levels
- **Confidentiality:** Ability to maintain confidentiality and data accuracy when handling sensitive information

## 🌟 Career Growth Opportunities

This role offers a strong foundation for advancement within S. Corp's privacy and compliance functions:

### Advancement Paths
- **Senior Privacy Roles:** Progress to senior privacy analyst or specialist positions
- **Leadership Opportunities:** Lead cross-functional initiatives and strategic programs
- **Specialization Areas:**
  - Regulatory strategy development
  - Privacy engineering and technical implementation
  - Global compliance leadership

## 🎯 Attributes We Value

### Professional Qualities
- **Dedicated to Self-improvement** | **Effective** | **Good Communicator/Listener**
- **Hardworking** | **High Integrity/Ethics** | **Open-Minded**
- **Self-Aware** | **Smart** | **Solution-Oriented**
- **Sound Judgment** | **Team Player** | **Thoughtful**

## 💰 Benefits & Compensation

### Comprehensive Benefits Package
- **Healthcare:** Medical, dental, vision, prescription, wellness, EAP, FSA
- **Insurance:** Life and disability insurance (premiums paid for base coverage)
- **Retirement:** 401(k) match, discounted stock purchase plan, investment options
- **Time Off:** Up to 11 paid holidays/year, 21 days PTO/year (increases over time), paid parental leave
- **Work-Life Balance:** Hybrid working environment, flexible PTO, back-up childcare arrangements
- **Professional Development:** Tuition reimbursement, education assistance
- **Additional Perks:** Commuter benefits, paid volunteer days, access to employee networks

## 🏢 About S. Corp

We are a technology and asset management company delivering on our promise of building brave futures—for our clients, our communities, and ourselves. After over 50 years in business, S. Corp remains a leading global provider of investment processing, investment management, and investment operations solutions.

### Our Work Environment
- Open floor plan offices with numerous art installations designed to encourage innovation and creativity
- Recognition that our people are our most valuable asset
- Investment in employee success through comprehensive support programs
- Focus on healthy, happy, and motivated workforce for continued growth

---

**Equal Opportunity:** S. Corp is an equal opportunity employer and all qualified applicants will receive consideration for employment without regard to race, color, religion, sex, sexual orientation, gender identity, national origin, age, disability status, protected veteran status, or any other characteristic protected by law.$desc_409$,
    'As a Data Privacy Analyst, you will be a member of the S. Corp Legal, Compliance, and Corporate Development Department, working with legal and compliance professionals while partnering with business unit, operational, and technical colleagues. S. Corp''s Privacy Office is responsible for the governance of personal, confidential, and proprietary data processed by S. Corp. You will help implement and promote that governance by applying the S. Corp Privacy Program Framework across assigned',
    ARRAY['Data Governance: Proven experience in data processing analysis through large-scale governance, compliance and regulatory initiatives', 'Process Management: Demonstrated ability to produce standardized process mapping ("As Is" vs "To Be")', 'Enterprise Programs: Experience building, deploying and managing data privacy programs in global enterprises', 'Privacy Platforms: Experience using enterprise data privacy platforms such as OneTrust', 'Privacy & Security: Proven ability to understand and apply data privacy and information security knowledge', 'Project Management: Knowledge of Agile, PPM and/or Prince II methodologies', 'Facilitation: Strong meeting and large group facilitation skills for multi-disciplined workshops', 'Microsoft Office: Proficiency including Visio'],
    ARRAY['Healthcare: Medical, dental, vision, prescription, wellness, EAP, FSA', 'Insurance: Life and disability insurance (premiums paid for base coverage)', 'Retirement: 401(k) match, discounted stock purchase plan, investment options', 'Time Off: Up to 11 paid holidays/year, 21 days PTO/year (increases over time), paid parental leave', 'Work-Life Balance: Hybrid working environment, flexible PTO, back-up childcare arrangements', 'Professional Development: Tuition reimbursement, education assistance', 'Additional Perks: Commuter benefits, paid volunteer days, access to employee networks'],
    ARRAY['SSIS', 'Excel', 'Compliance', 'Data Privacy', 'Agile', 'CCPA'],
    NULL,
    NULL,
    'USD',
    FALSE,
    '2025-07-10T00:00:00+00:00',
    TRUE
);
INSERT INTO job_agent.jobs (
    title, company, location, job_type, category, remote,
    description, short_description, requirements, benefits, skills_required, 
    salary_min, salary_max, salary_currency, is_featured, 
    posted_date, is_active
) VALUES (
    'SIPP Pension Product Analyst',
    'S. Corp',
    'London, United Kingdom',
    'Full-time',
    'Operations',
    FALSE,
    $desc_610$## 🎯 About the Role
We are seeking a highly motivated SIPP Pension Business Analyst with significant experience in pension administration, SIPP (Self-Invested Personal Pension) schemes, and pension business analysis processes. You will work with key stakeholders to define business requirements, ensure compliance, and optimize business processes related to pension products.

## 💼 Key Responsibilities
### Project Management & Stakeholder Relations
- Support SIPP-related project management activities ensuring on-time, compliant delivery
- Work with SIPP Project and pension administration teams to resolve issues
- Develop strong relationships with product managers, legal teams, US development teams, and customer service

### Business Analysis & Process Improvement
- Gather and document business requirements for SIPP pension products and services
- Analyze business processes and provide recommendations for efficiency improvements
- Translate business requirements into technical specifications for US development teams
- Assist in design and implementation of new SIPP platform features/enhancements

### Testing & Compliance
- Conduct user acceptance testing (UAT) ensuring changes meet business requirements
- Maintain knowledge of industry regulations ensuring SIPP solutions comply with current legislation
- Provide ongoing analysis and reporting on SIPP products for management insights

## 🎓 Required Qualifications
- **Industry Expertise:** In-depth understanding of SIPP products, pension regulations, and financial services sector
- **Experience:** Proven significant experience as Business Analyst in pensions industry with SIPP focus
- **Technical Skills:** Proficiency in Microsoft Office (Excel, Visio), business analysis tools (JIRA, Confluence)
- **Project Management:** Experience with project management methodologies

## 🌟 What We're Looking For
- Strong communication skills for technical and non-technical stakeholders
- Ability to prioritize tasks, manage time efficiently, and work under pressure
- Values alignment with S. Corp Values of courage, integrity, collaboration, inclusion, connection and fun

## 💰 Benefits
UK-specific benefits including comprehensive physical/mental well-being care, strong pension plan, hybrid working environment, private medical care, enhanced family leave, and access to employee networks.

---
**Regulatory:** S. Corp Investments (Europe) Ltd is authorised and regulated by the Financial Conduct Authority (FRN 191713).$desc_610$,
    'Join S. Corp''s growing team. We are seeking a highly motivated SIPP Pension Business Analyst with significant experience in pension administration, SIPP (SelfInvested Personal Pension) schemes, and pension business analysis processes. You will work with key stakeholders to define business requirements, ensure compliance, and optimize business processes related to pension products.',
    ARRAY['Industry Expertise: In-depth understanding of SIPP products, pension regulations, and financial services sector', 'Experience: Proven significant experience as Business Analyst in pensions industry with SIPP focus', 'Technical Skills: Proficiency in Microsoft Office (Excel, Visio), business analysis tools (JIRA, Confluence)', 'Project Management: Experience with project management methodologies'],
    NULL,
    ARRAY['SSIS', 'Excel', 'JIRA', 'Compliance', 'Data Privacy', 'Risk Management'],
    NULL,
    NULL,
    'USD',
    TRUE,
    '2025-06-10T00:00:00+00:00',
    TRUE
);
INSERT INTO job_agent.jobs (
    title, company, location, job_type, category, remote,
    description, short_description, requirements, benefits, skills_required, 
    salary_min, salary_max, salary_currency, is_featured, 
    posted_date, is_active
) VALUES (
    'Programme Manager - Wealth Platform Implementation',
    'S. Corp',
    'London, United Kingdom',
    'Full-time',
    'Other',
    FALSE,
    $desc_506$## 🎯 About the Role
The SWP Change Team (UK) Programme Manager is responsible for delivering complex, multi-threaded, multi-disciplinary implementations of the SWP Solution. This role requires effective coordination of programme projects, managing inter-dependencies, and maintaining stakeholder management for both internal and client-side relationships.

## 💼 What You Will Do

### Programme Management
- Implement appropriate internal programme structure following standard SWP implementation framework
- Monitor progress, resolve issues, and initiate corrective action
- Define programme governance arrangements with firms and ensure internal/external synchronization
- Manage programme budget, monitor expenditure against delivered benefits
- Ensure quality assurance and overall programme integrity

### Stakeholder & Team Management
- Facilitate appointment of individuals to project teams
- Manage effective, timely communication with all stakeholders
- Coordinate dependencies and interfaces between projects
- Lead intervention activities where gaps or issues arise
- Build effective client relationships during programme phase

### Strategic Coordination
- Coordinate with market unit solution leads for solution development requirements
- Partner with S. Corp relationship management and client service teams
- Design and communicate effective programme, communications and stakeholder plans
- Represent Change team in meetings with prospective clients

## 🎓 Required Qualifications
### Experience & Education
- **Education:** Ideally degree educated (or equivalent) with Wealth Management or Private Banking experience
- **Industry Knowledge:** Working knowledge of industry dynamics, business strategies, products and operating platforms
- **Project Experience:** Significant experience delivering variety of projects within financial services
- **Environment:** Comfortable working in ambiguous environments with proactive/self-starter mentality
- **Technical:** Experience with agile software environment, platform technology (advantageous)

### Skills & Certifications
- **Relationship Management:** Strong ability to build/maintain relationships within large-scale organizations
- **Communication:** Good presentation and facilitation skills, credible communications with senior personnel
- **Certifications:** Prince 2, Agile PM or similar qualification (advantageous)
- **Technical Proficiency:** Microsoft Office products, ability to learn new systems/databases

## 🌟 What We Value
- **Attention to Detail** | **Teamwork** | **Tenacity and Perseverance**
- **Innovation:** Drive change and improvement at all levels
- **Values Alignment:** S. Corp Values of courage, integrity, collaboration, inclusion, connection and fun

## 💰 Benefits
Comprehensive UK benefits including physical/mental well-being care, strong pension plan, tuition reimbursement, hybrid working environment, private medical care, enhanced family leave, volunteer days, and access to thriving employee networks.

---
**Regulatory:** S. Corp Investments (Europe) Ltd ('SIEL') is authorised and regulated by the Financial Conduct Authority (FRN 191713).

**Equal Opportunity:** S. Corp is an Equal Opportunity Employer committed to diversity and inclusion.$desc_506$,
    'Join S. Corp''s growing team. The SWP Change Team (UK) Programme Manager is responsible for delivering complex, multithreaded, multidisciplinary implementations of the SWP Solution. This role requires effective coordination of programme projects, managing interdependencies, and maintaining stakeholder management for both internal and clientside relationships.',
    ARRAY['Education: Ideally degree educated (or equivalent) with Wealth Management or Private Banking experience', 'Industry Knowledge: Working knowledge of industry dynamics, business strategies, products and operating platforms', 'Project Experience: Significant experience delivering variety of projects within financial services', 'Environment: Comfortable working in ambiguous environments with proactive/self-starter mentality', 'Technical: Experience with agile software environment, platform technology (advantageous)', 'Relationship Management: Strong ability to build/maintain relationships within large-scale organizations', 'Communication: Good presentation and facilitation skills, credible communications with senior personnel', 'Certifications: Prince 2, Agile PM or similar qualification (advantageous)'],
    NULL,
    ARRAY['Agile'],
    NULL,
    NULL,
    'USD',
    TRUE,
    '2025-06-19T00:00:00+00:00',
    TRUE
);

-- Update created_at and updated_at to match posted dates
UPDATE job_agent.jobs SET created_at = posted_date, updated_at = posted_date WHERE company = 'S. Corp';
