from datetime import datetime, timezone

def get_job_data():
    return {
        'title': 'Senior AI Solutions Architect - Distributed Systems',
        'company': 'S. Corp',
        'location': 'Charlotte, North Carolina, United States of America',  # Keep for display
        'city': 'Charlotte',
        'state': 'North Carolina', 
        'country': 'United States of America',
        'job_type': 'Full-time',
        'category': 'Engineering',
        'remote': True,
        'short_description': 'Lead the design and implementation of cutting-edge AI solutions for enterprise clients. Build distributed AI agent systems, integrate LLMs, and architect scalable AI infrastructure on cloud platforms.',
        'description': "## 🎯 About the Role\n\nS. Corp is seeking a Senior AI Solutions Architect to lead the design and implementation of next-generation AI solutions for our enterprise clients. You'll work with distributed AI agent systems, large language models, and cloud-native architectures to build scalable, production-ready AI platforms.\n\n## 💼 Key Responsibilities\n\n### AI Architecture & Design\n- Architect and implement distributed AI agent systems using frameworks like MCP (Model Context Protocol)\n- Design scalable AI infrastructure on Azure, AWS, or GCP with focus on Kubernetes orchestration\n- Integrate LLMs (GPT, Claude, etc.) into enterprise applications with proper security and governance\n- Build event-driven architectures for real-time AI processing and agent coordination\n\n### Technical Leadership\n- Lead technical teams in developing AI-powered solutions from concept to production\n- Create architectural patterns and frameworks for AI/ML integration across the organization\n- Collaborate with data scientists and ML engineers to productionize AI models\n- Establish best practices for AI system monitoring, observability, and performance optimization\n\n### Enterprise Integration\n- Design APIs and SDKs for AI service integration with existing enterprise systems\n- Implement proper security patterns for AI systems including data privacy and model governance\n- Work with stakeholders to translate business requirements into technical AI solutions\n- Ensure AI solutions meet enterprise standards for scalability, reliability, and compliance\n\n## 🎓 Required Qualifications\n\n### Core Requirements\n- **Education:** MS/BS in Computer Science, AI/ML, or equivalent experience\n- **Experience:** 15+ years in software architecture with 5+ years focused on AI/ML systems\n- **AI/ML Expertise:** Hands-on experience with TensorFlow, PyTorch, LangChain, OpenAI APIs\n- **Cloud Platforms:** Expert-level experience with Azure (preferred), AWS, or GCP\n- **Orchestration:** Production experience with Kubernetes, Docker, and service mesh architectures\n\n### Technical Skills\n- **Languages:** Python, Java, Go, JavaScript/TypeScript\n- **AI Frameworks:** TensorFlow, Keras, PyTorch, LangChain, Vector Databases, RAG architectures\n- **Cloud Services:** Azure OpenAI Service, Cognitive Services, AKS, or equivalent AWS/GCP services\n- **Architecture:** Distributed systems, microservices, event-driven design, RESTful APIs, gRPC\n- **DevOps:** CI/CD pipelines, Infrastructure as Code (Terraform, Helm), monitoring and observability\n\n### Preferred Qualifications\n- Experience with Model Context Protocol (MCP) or similar AI agent frameworks\n- Open-source contributions to AI/ML projects (GitHub portfolio preferred)\n- Previous work with financial services or highly regulated industries\n- Experience building AI platforms that serve millions of requests\n- Knowledge of AI ethics, bias detection, and responsible AI practices\n\n## 🌟 What Makes You Stand Out\n\n- **Innovation:** Track record of creating novel AI solutions or contributing to open-source AI projects\n- **Scale:** Experience building AI systems that handle enterprise-level traffic and data volumes\n- **Leadership:** History of mentoring teams and driving technical decision-making\n- **Business Acumen:** Ability to translate complex AI concepts into business value and ROI\n\n## 💰 Compensation & Benefits\n\n### Comprehensive Package\n- **Salary Range:** $180,000 - $250,000 annually\n- **Bonus:** Performance-based annual bonus up to 25% of base salary\n- **Equity:** Stock options in a growing technology company\n- **Remote Work:** Fully remote or hybrid options available\n- **Professional Development:** $5,000 annual learning budget for conferences, courses, certifications\n\n### Benefits\n- **Healthcare:** Premium medical, dental, vision with 100% company-paid premiums\n- **Retirement:** 401(k) with 6% company match, immediate vesting\n- **Time Off:** Unlimited PTO policy with 3-week minimum requirement\n- **Equipment:** Top-tier MacBook Pro, cloud credits, and home office stipend\n- **Innovation Time:** 20% time for research, open-source contributions, or internal innovation projects\n\n## 🏢 About S. Corp\n\nS. Corp is a leading technology company at the forefront of AI innovation. We build brave futures for our clients through cutting-edge AI solutions that transform how businesses operate. Our team of world-class engineers and researchers work on challenging problems in distributed AI, financial technology, and enterprise software.\n\n### Our Culture\n- **Innovation-First:** We encourage experimentation, open-source contributions, and technical excellence\n- **Remote-Friendly:** Global team with flexible work arrangements and strong async communication\n- **Growth-Oriented:** Clear career progression paths with mentorship and leadership opportunities\n- **Impact-Driven:** Work directly affects millions of users and billions in transaction volume\n\n---\n\n**Application Process:** Please include your GitHub profile, links to AI projects you've built, and any open-source contributions. We're particularly interested in your experience with distributed AI systems and production ML deployments.\n\n**Equal Opportunity:** S. Corp is committed to diversity and inclusion. All qualified applicants receive equal consideration regardless of race, gender, age, religion, sexual orientation, or disability status.",
        'requirements': [
            'MS/BS in Computer Science, AI/ML, or equivalent experience',
            '15+ years in software architecture with 5+ years focused on AI/ML systems',
            'Hands-on experience with TensorFlow, PyTorch, LangChain, OpenAI APIs',
            'Expert-level experience with Azure (preferred), AWS, or GCP',
            'Production experience with Kubernetes, Docker, and service mesh architectures',
            'Strong programming skills in Python, Java, Go, JavaScript/TypeScript',
            'Experience with distributed systems, microservices, event-driven design',
            'Knowledge of CI/CD pipelines, Infrastructure as Code (Terraform, Helm)',
            'Previous work with financial services or highly regulated industries preferred'
        ],
        'benefits': [
            'Salary Range: $180,000 - $250,000 annually',
            'Performance-based annual bonus up to 25% of base salary', 
            'Stock options in a growing technology company',
            'Fully remote or hybrid work options available',
            '$5,000 annual learning budget for professional development',
            'Premium healthcare with 100% company-paid premiums',
            '401(k) with 6% company match, immediate vesting',
            'Unlimited PTO policy with 3-week minimum requirement',
            'Top-tier equipment and home office stipend',
            '20% innovation time for research and open-source work'
        ],
        'skills_required': [
            'TensorFlow', 'PyTorch', 'LangChain', 'OpenAI APIs', 'Model Context Protocol',
            'Azure OpenAI Service', 'Kubernetes', 'Docker', 'Python', 'Java',
            'Distributed AI Systems', 'Vector Databases', 'RAG Architectures',
            'Microservices', 'RESTful APIs', 'gRPC', 'Event-driven Architecture',
            'Terraform', 'Helm', 'CI/CD', 'Azure', 'AWS', 'GCP'
        ],
        'salary_min': 180000,
        'salary_max': 250000,
        'salary_currency': 'USD',
        'interview_duration_minutes': 10,
        'posted_date': datetime.fromisoformat('2025-08-25T00:00:00+00:00'),
        'is_active': True,
        # Admin fields
        'created_by': 'system',
        'updated_by': None,
        'status': 'open',
        'interview_count': 0
    }
