# Additional environment variables that might be needed
variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "enable_observability" {
  description = "Enable Grafana and Tempo observability stack"
  type        = bool
  default     = true
}

variable "enable_debug" {
  description = "Enable debug mode for containers"
  type        = bool
  default     = false
}