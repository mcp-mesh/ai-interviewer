#!/bin/bash
# load-env.sh - Load environment variables for Terraform

# Set script to exit on any error
set -euo pipefail

echo "🔐 Loading environment variables for AI Interviewer deployment..."

# Check if .env file exists
if [[ -f .env ]]; then
    echo "📄 Loading variables from .env file..."
    set -a  # automatically export all variables
    source .env
    set +a  # turn off auto-export
else
    echo "📝 No .env file found. Create one with your secrets:"
    echo "   cp .env.example .env"
    echo "   # Edit .env with your actual values"
    echo ""
fi

# Function to check if variable is set
check_var() {
    local var_name=$1
    local var_value=${!var_name:-}
    
    if [[ -z "$var_value" ]]; then
        echo "⚠️  $var_name is not set"
        return 1
    else
        echo "✅ $var_name is set"
        return 0
    fi
}

# Function to mask secret values for display
mask_secret() {
    local value=$1
    local length=${#value}
    if [[ $length -gt 8 ]]; then
        echo "${value:0:4}****${value: -4}"
    else
        echo "****"
    fi
}

echo ""
echo "🔍 Checking required environment variables:"

# OAuth Configuration
OAUTH_VARS=(
    "GOOGLE_CLIENT_ID"
    "GOOGLE_CLIENT_SECRET"
)

# API Keys
API_VARS=(
    "ANTHROPIC_API_KEY"
    "OPENAI_API_KEY"
)

# Optional OAuth (can be empty)
OPTIONAL_OAUTH_VARS=(
    "GITHUB_CLIENT_ID"
    "GITHUB_CLIENT_SECRET"
    "MICROSOFT_CLIENT_ID"
    "MICROSOFT_CLIENT_SECRET"
    "APPLE_CLIENT_ID"
    "APPLE_CLIENT_SECRET"
)

# Check required variables
all_good=true
for var in "${OAUTH_VARS[@]}" "${API_VARS[@]}"; do
    if ! check_var "$var"; then
        all_good=false
    fi
done

# Show optional variables status
echo ""
echo "📋 Optional OAuth providers:"
for var in "${OPTIONAL_OAUTH_VARS[@]}"; do
    if [[ -n "${!var:-}" ]]; then
        echo "✅ $var is set"
    else
        echo "⚪ $var is not set (optional)"
    fi
done

# Show what will be used
echo ""
echo "🚀 Environment variables that will be used:"
echo "GOOGLE_CLIENT_ID=$(mask_secret "${GOOGLE_CLIENT_ID:-}")"
echo "GOOGLE_CLIENT_SECRET=$(mask_secret "${GOOGLE_CLIENT_SECRET:-}")"
echo "ANTHROPIC_API_KEY=$(mask_secret "${ANTHROPIC_API_KEY:-}")"
echo "OPENAI_API_KEY=$(mask_secret "${OPENAI_API_KEY:-}")"

# Export variables for Terraform to use
export TF_VAR_env_secrets=$(cat <<EOF
{
  "GOOGLE_CLIENT_ID": "${GOOGLE_CLIENT_ID:-}",
  "GOOGLE_CLIENT_SECRET": "${GOOGLE_CLIENT_SECRET:-}",
  "GITHUB_CLIENT_ID": "${GITHUB_CLIENT_ID:-}",
  "GITHUB_CLIENT_SECRET": "${GITHUB_CLIENT_SECRET:-}",
  "MICROSOFT_CLIENT_ID": "${MICROSOFT_CLIENT_ID:-}",
  "MICROSOFT_CLIENT_SECRET": "${MICROSOFT_CLIENT_SECRET:-}",
  "APPLE_CLIENT_ID": "${APPLE_CLIENT_ID:-}",
  "APPLE_CLIENT_SECRET": "${APPLE_CLIENT_SECRET:-}",
  "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY:-}",
  "OPENAI_API_KEY": "${OPENAI_API_KEY:-}",
  "POSTGRES_USER": "${POSTGRES_USER:-ai_user}",
  "POSTGRES_PASSWORD": "${POSTGRES_PASSWORD:-ai_password}",
  "POSTGRES_DB": "${POSTGRES_DB:-ai_interviewer}",
  "REDIS_PASSWORD": "${REDIS_PASSWORD:-}",
  "MINIO_ACCESS_KEY": "${MINIO_ACCESS_KEY:-minioadmin}",
  "MINIO_SECRET_KEY": "${MINIO_SECRET_KEY:-minioadmin}"
}
EOF
)

if [[ "$all_good" == true ]]; then
    echo ""
    echo "✅ All required environment variables are set!"
    echo "🚀 Ready to run: terraform apply"
else
    echo ""
    echo "❌ Missing required environment variables. Please set them first."
    echo "💡 Tip: Create a .env file with your secrets and source it."
    exit 1
fi