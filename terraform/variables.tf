variable "minikube_memory" {
  description = "Memory allocation for minikube in MB"
  type        = number
  default     = 28672
}

variable "minikube_cpus" {
  description = "CPU allocation for minikube"
  type        = number
  default     = 8
}

variable "namespace" {
  description = "Kubernetes namespace for AI Interviewer"
  type        = string
  default     = "ai-interviewer"
}

variable "docker_images" {
  description = "Docker images to load into minikube"
  type = map(string)
  default = {
    backend           = "ai-interviewer/backend:latest"
    frontend          = "ai-interviewer/nginx-gateway:latest"
    pdf_extractor     = "ai-interviewer/pdf-extractor:latest"
    interview_agent   = "ai-interviewer/interview-agent:latest"
    claude_llm_agent  = "ai-interviewer/claude-llm-agent:latest"
    openai_llm_agent  = "ai-interviewer/openai-llm-agent:latest"
  }
}

# OAuth configuration from environment variables
variable "google_client_id" {
  description = "Google OAuth Client ID (set via TF_VAR_google_client_id)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "google_client_secret" {
  description = "Google OAuth Client Secret (set via TF_VAR_google_client_secret)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "github_client_id" {
  description = "GitHub OAuth Client ID (set via TF_VAR_github_client_id)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "github_client_secret" {
  description = "GitHub OAuth Client Secret (set via TF_VAR_github_client_secret)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "microsoft_client_id" {
  description = "Microsoft OAuth Client ID (set via TF_VAR_microsoft_client_id)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "microsoft_client_secret" {
  description = "Microsoft OAuth Client Secret (set via TF_VAR_microsoft_client_secret)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "apple_client_id" {
  description = "Apple OAuth Client ID (set via TF_VAR_apple_client_id)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "apple_client_secret" {
  description = "Apple OAuth Client Secret (set via TF_VAR_apple_client_secret)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "anthropic_api_key" {
  description = "Anthropic API Key (set via TF_VAR_anthropic_api_key)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API Key (set via TF_VAR_openai_api_key)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "metallb_ip_range" {
  description = "IP range for MetalLB"
  type        = string
  default     = "192.168.49.100-192.168.49.200"
}