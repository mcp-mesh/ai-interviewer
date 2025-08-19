#!/bin/bash
# Deploy AI Interviewer with environment secrets

set -e

echo "🚀 AI Interviewer Terraform Deployment"
echo "======================================="

# Check for required environment variables
check_env_var() {
    if [ -z "${!1}" ]; then
        echo "⚠️  Warning: $1 is not set. Using default/dummy value."
        return 1
    else
        echo "✅ $1 is set"
        return 0
    fi
}

echo ""
echo "📋 Checking environment variables..."
check_env_var "GOOGLE_CLIENT_ID"
check_env_var "GOOGLE_CLIENT_SECRET"
check_env_var "ANTHROPIC_API_KEY" || check_env_var "CLAUDE_API_KEY"
check_env_var "OPENAI_API_KEY"

# Build the env_secrets JSON from environment variables
echo ""
echo "🔧 Building secrets configuration..."
ENV_SECRETS='{'

# OAuth secrets
[ -n "$GOOGLE_CLIENT_ID" ] && ENV_SECRETS+='"GOOGLE_CLIENT_ID":"'$GOOGLE_CLIENT_ID'",'
[ -n "$GOOGLE_CLIENT_SECRET" ] && ENV_SECRETS+='"GOOGLE_CLIENT_SECRET":"'$GOOGLE_CLIENT_SECRET'",'
[ -n "$GITHUB_CLIENT_ID" ] && ENV_SECRETS+='"GITHUB_CLIENT_ID":"'$GITHUB_CLIENT_ID'",'
[ -n "$GITHUB_CLIENT_SECRET" ] && ENV_SECRETS+='"GITHUB_CLIENT_SECRET":"'$GITHUB_CLIENT_SECRET'",'
[ -n "$MICROSOFT_CLIENT_ID" ] && ENV_SECRETS+='"MICROSOFT_CLIENT_ID":"'$MICROSOFT_CLIENT_ID'",'
[ -n "$MICROSOFT_CLIENT_SECRET" ] && ENV_SECRETS+='"MICROSOFT_CLIENT_SECRET":"'$MICROSOFT_CLIENT_SECRET'",'
[ -n "$APPLE_CLIENT_ID" ] && ENV_SECRETS+='"APPLE_CLIENT_ID":"'$APPLE_CLIENT_ID'",'
[ -n "$APPLE_CLIENT_SECRET" ] && ENV_SECRETS+='"APPLE_CLIENT_SECRET":"'$APPLE_CLIENT_SECRET'",'

# API Keys
[ -n "$ANTHROPIC_API_KEY" ] && ENV_SECRETS+='"ANTHROPIC_API_KEY":"'$ANTHROPIC_API_KEY'",'
[ -n "$CLAUDE_API_KEY" ] && ENV_SECRETS+='"ANTHROPIC_API_KEY":"'$CLAUDE_API_KEY'",'
[ -n "$OPENAI_API_KEY" ] && ENV_SECRETS+='"OPENAI_API_KEY":"'$OPENAI_API_KEY'",'

# Database credentials (optional)
[ -n "$POSTGRES_USER" ] && ENV_SECRETS+='"POSTGRES_USER":"'$POSTGRES_USER'",'
[ -n "$POSTGRES_PASSWORD" ] && ENV_SECRETS+='"POSTGRES_PASSWORD":"'$POSTGRES_PASSWORD'",'
[ -n "$POSTGRES_DB" ] && ENV_SECRETS+='"POSTGRES_DB":"'$POSTGRES_DB'",'
[ -n "$MINIO_ACCESS_KEY" ] && ENV_SECRETS+='"MINIO_ACCESS_KEY":"'$MINIO_ACCESS_KEY'",'
[ -n "$MINIO_SECRET_KEY" ] && ENV_SECRETS+='"MINIO_SECRET_KEY":"'$MINIO_SECRET_KEY'",'

# Remove trailing comma and close JSON
ENV_SECRETS=${ENV_SECRETS%,}
ENV_SECRETS+='}'

# Export for Terraform
export TF_VAR_env_secrets="$ENV_SECRETS"

# Initialize Terraform if needed
if [ ! -d ".terraform" ]; then
    echo ""
    echo "📦 Initializing Terraform..."
    terraform init
fi

# Plan or Apply based on argument
if [ "$1" = "plan" ]; then
    echo ""
    echo "📝 Running Terraform plan..."
    terraform plan
elif [ "$1" = "destroy" ]; then
    echo ""
    echo "🗑️  Running Terraform destroy..."
    terraform destroy
else
    echo ""
    echo "🏗️  Running Terraform apply..."
    terraform apply
fi

echo ""
echo "✨ Deployment script completed!"