# Extract secrets from environment variables
locals {
  # OAuth secrets from Terraform variables (which read from TF_VAR_* environment variables)
  oauth_secrets = {
    GOOGLE_CLIENT_ID        = var.google_client_id != "" ? var.google_client_id : "dummy-google-client-id"
    GOOGLE_CLIENT_SECRET    = var.google_client_secret != "" ? var.google_client_secret : "dummy-google-client-secret"
    GITHUB_CLIENT_ID        = var.github_client_id != "" ? var.github_client_id : "dummy-github-client-id"
    GITHUB_CLIENT_SECRET    = var.github_client_secret != "" ? var.github_client_secret : "dummy-github-client-secret"
    MICROSOFT_CLIENT_ID     = var.microsoft_client_id != "" ? var.microsoft_client_id : "dummy-microsoft-client-id"
    MICROSOFT_CLIENT_SECRET = var.microsoft_client_secret != "" ? var.microsoft_client_secret : "dummy-microsoft-client-secret"
    APPLE_CLIENT_ID         = var.apple_client_id != "" ? var.apple_client_id : "dummy-apple-client-id"
    APPLE_CLIENT_SECRET     = var.apple_client_secret != "" ? var.apple_client_secret : "dummy-apple-client-secret"
  }

  # API keys from Terraform variables (which read from TF_VAR_* environment variables)
  api_keys = {
    ANTHROPIC_API_KEY = var.anthropic_api_key != "" ? var.anthropic_api_key : "dummy-anthropic-key"
    OPENAI_API_KEY    = var.openai_api_key != "" ? var.openai_api_key : "dummy-openai-key"
  }

  # Database credentials with defaults
  database_secrets = {
    POSTGRES_USER     = "ai_user"
    POSTGRES_PASSWORD = "ai_password"
    POSTGRES_DB       = "ai_interviewer"
    REDIS_PASSWORD    = ""
    MINIO_ACCESS_KEY  = "minioadmin"
    MINIO_SECRET_KEY  = "minioadmin"
  }

  # All secrets combined
  all_secrets = merge(local.oauth_secrets, local.api_keys, local.database_secrets)
}

# OAuth Configuration Secret (from environment)
resource "kubernetes_secret" "oauth_config" {
  depends_on = [kubernetes_namespace.ai_interviewer]

  metadata {
    name      = "oauth-credentials"
    namespace = var.namespace
  }

  type = "Opaque"

  data = {
    for key, value in local.oauth_secrets : key => value
  }
}

# API Keys Secret (from environment)
resource "kubernetes_secret" "api_keys" {
  depends_on = [kubernetes_namespace.ai_interviewer]

  metadata {
    name      = "api-keys"
    namespace = var.namespace
  }

  type = "Opaque"

  data = {
    for key, value in local.api_keys : key => value
  }
}

# Database Credentials Secret (from environment)
resource "kubernetes_secret" "database_credentials" {
  depends_on = [kubernetes_namespace.ai_interviewer]

  metadata {
    name      = "database-credentials"
    namespace = var.namespace
  }

  type = "Opaque"

  data = {
    for key, value in local.database_secrets : key => value
  }
}