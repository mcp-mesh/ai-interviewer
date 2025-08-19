# AI Interviewer Terraform Makefile
.PHONY: help init plan apply destroy status clean rebuild

# Default target
help:
	@echo "AI Interviewer Infrastructure Management"
	@echo ""
	@echo "Available targets:"
	@echo "  init      - Initialize Terraform"
	@echo "  plan      - Plan infrastructure changes"
	@echo "  apply     - Apply infrastructure changes"
	@echo "  destroy   - Destroy all infrastructure"
	@echo "  status    - Check infrastructure status"
	@echo "  rebuild   - Destroy and rebuild everything"
	@echo "  clean     - Clean Terraform state and cache"
	@echo ""
	@echo "Quick commands:"
	@echo "  make init apply    - Deploy everything"
	@echo "  make rebuild       - Fresh deployment"

# Initialize Terraform
init:
	@echo "🚀 Initializing Terraform..."
	terraform init
	@echo "✅ Terraform initialized"

# Plan infrastructure changes
plan:
	@echo "📋 Planning infrastructure changes..."
	terraform plan -out=tfplan
	@echo "✅ Plan complete - review above"

# Apply infrastructure changes
apply:
	@echo "🔨 Applying infrastructure changes..."
	terraform apply -auto-approve
	@echo "✅ Infrastructure deployed!"
	@echo ""
	@echo "🌐 Application URLs:"
	@terraform output -raw application_url
	@echo "/grafana/ - Grafana Dashboard"
	@echo "/registry/ - MCP Registry"
	@echo ""
	@echo "📊 Check status with: make status"

# Destroy all infrastructure
destroy:
	@echo "💥 Destroying all infrastructure..."
	@read -p "Are you sure? This will delete everything! [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		terraform destroy -auto-approve; \
		echo "✅ Infrastructure destroyed"; \
	else \
		echo "❌ Cancelled"; \
	fi

# Check infrastructure status
status:
	@echo "📊 Infrastructure Status"
	@echo "========================"
	@echo "Minikube Status:"
	@minikube status || echo "❌ Minikube not running"
	@echo ""
	@echo "Kubernetes Pods:"
	@kubectl get pods -n ai-interviewer 2>/dev/null || echo "❌ No pods found"
	@echo ""
	@echo "Services:"
	@kubectl get services -n ai-interviewer 2>/dev/null || echo "❌ No services found"
	@echo ""
	@echo "External Access:"
	@kubectl get service ai-interviewer-nginx-gateway -n ai-interviewer 2>/dev/null || echo "❌ Gateway not found"

# Rebuild everything
rebuild: destroy apply

# Clean Terraform cache and state
clean:
	@echo "🧹 Cleaning Terraform cache..."
	rm -rf .terraform/
	rm -f .terraform.lock.hcl
	rm -f tfplan
	rm -f terraform.tfstate.backup
	@echo "✅ Terraform cache cleaned"
	@echo "⚠️  Note: terraform.tfstate preserved"

# Development helpers
dev-logs:
	@echo "📋 Showing recent logs from all pods..."
	kubectl logs -n ai-interviewer -l app.kubernetes.io/part-of=ai-interviewer --tail=100

dev-shell:
	@echo "🐚 Opening shell in backend pod..."
	kubectl exec -n ai-interviewer -it deployment/ai-interviewer-backend -- /bin/bash

dev-port-forward:
	@echo "🔗 Port forwarding backend to localhost:8080..."
	kubectl port-forward -n ai-interviewer service/ai-interviewer-backend 8080:8080

# Build Docker images before deployment
build-images:
	@echo "🐳 Building Docker images..."
	cd .. && make build-all
	@echo "✅ Docker images built"

# Full deployment with image building
deploy: build-images init apply

# Quick development cycle
dev: build-images
	@echo "🔄 Updating running deployment with new images..."
	@./scripts/update-images.sh

# Validate configuration
validate:
	@echo "✅ Validating Terraform configuration..."
	terraform validate
	@echo "✅ Configuration is valid"