# AI Interviewer Terraform Infrastructure

This Terraform configuration manages the complete AI Interviewer platform infrastructure including:
- Minikube cluster setup with configurable resources
- MetalLB load balancer
- Database services (PostgreSQL, Redis, MinIO)
- MCP agents and mesh registry
- Observability stack (Grafana, Tempo)
- Nginx gateway with OAuth authentication
- **IPTables configuration for external access** (automatic public IP detection and port forwarding)

## Prerequisites

1. **Install required tools:**
   ```bash
   # Install Terraform
   curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
   sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
   sudo apt-get update && sudo apt-get install terraform

   # Install kubectl, minikube, docker (if not already installed)
   ```

2. **Build Docker images:**
   ```bash
   # Build all application images first
   cd ..
   make build-all  # or individual build commands
   ```

## Quick Start

1. **Copy and configure variables:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your OAuth credentials
   ```

2. **Initialize and deploy:**
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

3. **Access the application:**
   ```bash
   # Get external access URLs (configured automatically)
   terraform output external_urls
   
   # Or check LoadBalancer IP directly
   kubectl get svc ai-interviewer-nginx-gateway -n ai-interviewer
   ```

## Configuration

### Memory and CPU
- Default: 16GB RAM, 8 CPUs
- Modify in `terraform.tfvars`:
  ```hcl
  minikube_memory = 32768  # 32 GB
  minikube_cpus   = 16
  ```

### OAuth Setup
Configure OAuth providers in `terraform.tfvars`:
```hcl
oauth_config = {
  google_client_id     = "your-google-client-id"
  google_client_secret = "your-google-client-secret"
  # ... other providers
}
```

## Commands

```bash
# Deploy everything
terraform apply

# Update configuration
terraform plan
terraform apply

# Destroy everything
terraform destroy

# View outputs
terraform output

# Access services
terraform output -raw minikube_ip
```

## Architecture

- **Minikube**: Local Kubernetes cluster with Docker driver
- **MetalLB**: LoadBalancer implementation for internal load balancing
- **IPTables**: Automatic port forwarding from public IP to MetalLB (with backup/restore)
- **Databases**: PostgreSQL, Redis, MinIO for storage
- **MCP Mesh**: Agent registry and communication
- **Observability**: Grafana + Tempo for monitoring
- **Gateway**: Nginx with OAuth authentication

## Troubleshooting

- Check minikube status: `minikube status`
- View logs: `kubectl logs -n ai-interviewer -l app=<component>`
- Port forward for debugging: `kubectl port-forward -n ai-interviewer svc/<service> <port>`
- Access Grafana: `https://<EXTERNAL-IP>/grafana/`