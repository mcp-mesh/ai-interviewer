# AI Interviewer Terraform Configuration
# Copy this file to terraform.tfvars and customize as needed

# Minikube Configuration  
minikube_memory = 28672  # 28 GB RAM (leaving ~4GB for host OS)
minikube_cpus   = 8      # 8 CPU cores

# Kubernetes Configuration
namespace = "ai-interviewer"
metallb_ip_range = "192.168.49.100-192.168.49.200"

# Environment (dev, staging, prod)
environment = "dev"

# Feature Toggles
enable_observability = true
enable_debug = false

# Docker Images (built locally)
docker_images = {
  backend           = "ai-interviewer/backend:latest"
  frontend          = "ai-interviewer/nginx-gateway:latest"
  pdf_extractor     = "ai-interviewer/pdf-extractor:latest"
  interview_agent   = "ai-interviewer/interview-agent:latest"
  llm_agent         = "ai-interviewer/llm-agent:latest"
  openai_llm_agent  = "ai-interviewer/openai-llm-agent:latest"
}

# OAuth Configuration (required for nginx to start)
oauth_config = {
  google_client_id     = "dummy-google-client-id"
  google_client_secret = "dummy-google-client-secret"
  github_client_id     = "dummy-github-client-id"
  github_client_secret = "dummy-github-client-secret"
  microsoft_client_id  = "dummy-microsoft-client-id"
  microsoft_client_secret = "dummy-microsoft-client-secret"
  apple_client_id      = "dummy-apple-client-id"
  apple_client_secret  = "dummy-apple-client-secret"
}

# API Keys (can be set later via environment variables)
anthropic_api_key = "dummy-anthropic-key"
openai_api_key = "dummy-openai-key"

# NOTE: You can override these with environment variables!
# Set these in your shell before running terraform:
#
# export GOOGLE_CLIENT_ID="943290783081-54r9ivge76l0sot8j2h2jpkiccrsf7oj.apps.googleusercontent.com"
# export GOOGLE_CLIENT_SECRET="your-google-client-secret"
# export GITHUB_CLIENT_ID="your-github-client-id"
# export GITHUB_CLIENT_SECRET="your-github-client-secret"
# export MICROSOFT_CLIENT_ID="your-microsoft-client-id"
# export MICROSOFT_CLIENT_SECRET="your-microsoft-client-secret"
# export APPLE_CLIENT_ID="your-apple-client-id"
# export APPLE_CLIENT_SECRET="your-apple-client-secret"
# export ANTHROPIC_API_KEY="your-anthropic-api-key"
# export OPENAI_API_KEY="your-openai-api-key"
#
# Optional database overrides:
# export POSTGRES_USER="custom_user"
# export POSTGRES_PASSWORD="custom_password"
# export POSTGRES_DB="custom_db"
# export MINIO_ACCESS_KEY="custom_access_key"
# export MINIO_SECRET_KEY="custom_secret_key"