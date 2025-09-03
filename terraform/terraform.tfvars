# AI Interviewer Terraform Configuration
# Copy this file to terraform.tfvars and customize as needed

# Minikube Configuration  
minikube_memory = 28672 # 28 GB RAM (leaving ~4GB for host OS)
minikube_cpus   = 8     # 8 CPU cores

# Kubernetes Configuration
namespace        = "ai-interviewer"
metallb_ip_range = "192.168.49.100-192.168.49.200"

# Environment (dev, staging, prod)
environment = "dev"

# Feature Toggles
enable_observability = true
enable_debug         = false

# Docker Images (built locally)
docker_images = {
  backend          = "ai-interviewer/backend:latest"
  frontend         = "ai-interviewer/nginx-gateway:latest"
  pdf_extractor    = "ai-interviewer/pdf-extractor:latest"
  interview_agent  = "ai-interviewer/interview-agent:latest"
  llm_agent        = "ai-interviewer/llm-agent:latest"
  openai_llm_agent = "ai-interviewer/openai-llm-agent:latest"
}

# OAuth Configuration and API Keys are read from environment variables
# Set these in your shell before running terraform:
#   export TF_VAR_google_client_id="your-google-client-id"
#   export TF_VAR_google_client_secret="your-google-client-secret"
#   export TF_VAR_github_client_id="your-github-client-id"
#   export TF_VAR_github_client_secret="your-github-client-secret"
#   export TF_VAR_microsoft_client_id="your-microsoft-client-id"
#   export TF_VAR_microsoft_client_secret="your-microsoft-client-secret"
#   export TF_VAR_apple_client_id="your-apple-client-id"
#   export TF_VAR_apple_client_secret="your-apple-client-secret"
#   export TF_VAR_anthropic_api_key="your-anthropic-api-key"
#   export TF_VAR_openai_api_key="your-openai-api-key"

# If no environment variables are set, dummy values will be used as fallbacks.