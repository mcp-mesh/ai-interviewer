# AI-Interviewer Kubernetes Deployment Guide

This guide provides step-by-step instructions to deploy the complete AI-interviewer stack in Kubernetes with MetalLB LoadBalancer, SSL termination, distributed tracing, and observability.

## Prerequisites

- Kubernetes cluster (tested with minikube)
- kubectl configured
- Docker registry access for building images
- API keys for Claude and OpenAI
- OAuth credentials (Google, GitHub, Microsoft, Apple)

## Architecture Overview

The AI-interviewer stack consists of:

- **NGINX Gateway**: OpenResty with Lua scripts for OAuth authentication and SSL termination
- **Backend API**: FastAPI service for interview management
- **MCP Agents**: AI agents for different LLM providers and PDF processing
- **Registry**: MCP Mesh service discovery and coordination
- **Databases**: PostgreSQL (registry) and Redis (sessions/caching)
- **Storage**: MinIO for file uploads
- **Observability**: Grafana and Tempo for monitoring and distributed tracing

## Step 1: Cluster Setup

### 1.1 Start Minikube with Required Resources

```bash
minikube start --cpus=4 --memory=8192 --disk-size=20g
```

### 1.2 Install MetalLB LoadBalancer

```bash
# Install MetalLB
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.13.7/config/manifests/metallb-native.yaml

# Wait for MetalLB to be ready
kubectl wait --namespace metallb-system \
  --for=condition=ready pod \
  --selector=app=metallb \
  --timeout=90s

# Get minikube IP range
minikube ip
# Example output: 192.168.49.2

# Configure MetalLB IP pool (adjust IP range based on your minikube IP)
cat <<EOF | kubectl apply -f -
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: default-pool
  namespace: metallb-system
spec:
  addresses:
  - 192.168.49.100-192.168.49.200
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: default
  namespace: metallb-system
spec:
  ipAddressPools:
  - default-pool
EOF
```

### 1.3 Fix Docker Build Issues (if using minikube)

```bash
# MetalLB can interfere with Docker builds, fix with iptables rules
sudo iptables -I FORWARD -s 172.17.0.0/16 -j ACCEPT
sudo iptables -I FORWARD -d 172.17.0.0/16 -j ACCEPT
sudo iptables -t nat -A POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE
```

## Step 2: Build Docker Images

```bash
# Set Docker environment to minikube
eval $(minikube docker-env)

# Build all images
cd /path/to/mcp-mesh/ai-interviewer

# Build backend
docker build -t ai-interviewer/backend:latest -f backend/Dockerfile .

# Build agents
docker build -t ai-interviewer/claude-llm-agent:latest -f agents/claude-llm-agent/Dockerfile .
docker build -t ai-interviewer/openai-llm-agent:latest -f agents/openai-llm-agent/Dockerfile .
docker build -t ai-interviewer/pdf-extractor:latest -f agents/pdf-extractor/Dockerfile .
docker build -t ai-interviewer/interview-agent:latest -f agents/interview-agent/Dockerfile .

# Build nginx gateway
docker build -t ai-interviewer/nginx-gateway:latest -f nginx/Dockerfile .
```

## Step 3: Create Namespace and Secrets

### 3.1 Create Namespace

```bash
kubectl create namespace ai-interviewer
```

### 3.2 Create API Keys Secret

```bash
# Ensure your environment variables are set
source ~/.bashrc  # or wherever your API keys are defined

# Create secret from environment variables
kubectl create secret generic ai-interviewer-api-keys \
  --from-literal=CLAUDE_API_KEY="$CLAUDE_API_KEY" \
  --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY" \
  -n ai-interviewer
```

### 3.3 Create OAuth Credentials Secret

```bash
kubectl create secret generic ai-interviewer-oauth-keys \
  --from-literal=GOOGLE_CLIENT_ID="$GOOGLE_CLIENT_ID" \
  --from-literal=GOOGLE_CLIENT_SECRET="$GOOGLE_CLIENT_SECRET" \
  -n ai-interviewer
```

## Step 4: Deploy Infrastructure Services

### 4.1 Deploy PostgreSQL

```bash
kubectl apply -f k8s/base/postgres/
```

### 4.2 Deploy Redis

```bash
kubectl apply -f k8s/base/redis/
```

### 4.3 Deploy MinIO

```bash
kubectl apply -f k8s/base/minio/
```

### 4.4 Wait for Infrastructure to be Ready

```bash
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=ai-interviewer-postgres -n ai-interviewer --timeout=300s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=ai-interviewer-redis -n ai-interviewer --timeout=300s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=ai-interviewer-minio -n ai-interviewer --timeout=300s
```

## Step 5: Deploy Observability Stack

### 5.1 Deploy Tempo (Distributed Tracing)

```bash
kubectl apply -f k8s/base/observability/tempo-config-configmap.yaml
kubectl apply -f k8s/base/observability/tempo-deployment.yaml
kubectl apply -f k8s/base/observability/tempo-service.yaml
```

### 5.2 Deploy Grafana (Monitoring)

```bash
kubectl apply -f k8s/base/observability/grafana-config-configmap.yaml
kubectl apply -f k8s/base/observability/grafana-deployment.yaml
kubectl apply -f k8s/base/observability/grafana-service.yaml
```

## Step 6: Deploy MCP Mesh Services

### 6.1 Deploy Registry

```bash
kubectl apply -f k8s/base/registry/
```

### 6.2 Deploy Backend

```bash
kubectl apply -f k8s/base/backend/
```

### 6.3 Deploy MCP Agents

```bash
kubectl apply -f k8s/base/agents/
```

## Step 7: Deploy Gateway and Ingress

### 7.1 Deploy NGINX Gateway with ConfigMaps

```bash
kubectl apply -f k8s/gateway/
```

### 7.2 Create LoadBalancer Service

```bash
kubectl apply -f k8s/loadbalancer/ai-interviewer-loadbalancer.yaml
```

## Step 8: Scale Services (Optional)

```bash
# Scale backend for high availability
kubectl scale deployment ai-interviewer-backend --replicas=3 -n ai-interviewer
```

## Step 9: Verify Deployment

### 9.1 Check All Pods are Running

```bash
kubectl get pods -n ai-interviewer
```

### 9.2 Get LoadBalancer IP

```bash
kubectl get svc ai-interviewer-loadbalancer -n ai-interviewer
# Note the EXTERNAL-IP
```

### 9.3 Check Service Health

```bash
# Get the external IP from the LoadBalancer
EXTERNAL_IP=$(kubectl get svc ai-interviewer-loadbalancer -n ai-interviewer -o jsonpath='{.status.loadBalancer.ingress[0].ip}')

# Test health endpoint
curl -k https://$EXTERNAL_IP:30483/health
```

## Step 10: Configure DNS (Optional)

Add the following to your `/etc/hosts` file for local development:

```bash
# Replace with your actual LoadBalancer IP
192.168.49.100 interviewes.ai
```

## Access URLs

- **Main Application**: https://interviewes.ai:30483/ or https://EXTERNAL_IP:30483/
- **Grafana**: https://interviewes.ai:30483/grafana/ (admin/admin)
- **Registry API**: http://EXTERNAL_IP:8000 (via port-forward)

## Port Forwarding for Development

```bash
# Registry API
kubectl port-forward -n ai-interviewer svc/ai-interviewer-registry 8000:8000

# Grafana (alternative access)
kubectl port-forward -n ai-interviewer svc/ai-interviewer-grafana 3000:3000

# MinIO Console
kubectl port-forward -n ai-interviewer svc/ai-interviewer-minio 9001:9001
```

## Key Configuration Changes Made

### 1. Distributed Tracing Environment Variables

All services include these environment variables for distributed tracing:

```yaml
- name: MCP_MESH_DISTRIBUTED_TRACING_ENABLED
  value: "true"
- name: MCP_MESH_TELEMETRY_ENABLED
  value: "true"
- name: MCP_MESH_REDIS_TRACE_PUBLISHING
  value: "true"
```

### 2. Registry Configuration

The registry includes all docker-compose environment variables:

```yaml
- name: HOST
  value: "0.0.0.0"
- name: PORT
  value: "8000"
- name: MCP_MESH_LOG_LEVEL
  value: "INFO"
- name: MCP_MESH_DEBUG_MODE
  value: "false"
- name: TRACE_EXPORTER_TYPE
  value: "otlp"
- name: TELEMETRY_ENDPOINT
  value: "ai-interviewer-tempo:4317"
- name: TELEMETRY_PROTOCOL
  value: "grpc"
```

### 3. Grafana Subpath Configuration

Grafana is configured to work with nginx subpath routing:

```ini
[server]
domain = localhost
root_url = /grafana/
serve_from_sub_path = true
enforce_domain = false
```

### 4. MinIO Integration

All services include MinIO configuration for file storage:

```yaml
- name: S3_ENDPOINT
  value: "http://ai-interviewer-minio:9000"
- name: S3_ACCESS_KEY
  value: "minioadmin"
- name: S3_SECRET_KEY
  value: "minioadmin123"
- name: S3_BUCKET_NAME
  value: "ai-interviewer-uploads"
```

### 5. Backend Code Fix

Fixed hardcoded MinIO URLs in backend to use environment variables:

```python
# Before: "minio_url": f"http://minio:9000/{BUCKET_NAME}/{unique_filename}"
# After: "minio_url": f"http://{MINIO_HOST}/{BUCKET_NAME}/{unique_filename}"
```

## Troubleshooting

### Common Issues

1. **DNS Resolution Errors**: Ensure full FQDNs are used for inter-service communication
2. **MetalLB IP Pool**: Adjust IP range to match your cluster's network
3. **Docker Build Failures**: Run the iptables commands to fix MetalLB interference
4. **Pod CrashLoopBackOff**: Check logs with `kubectl logs -n ai-interviewer <pod-name>`
5. **Grafana Redirect Loops**: Ensure nginx proxy_pass configuration preserves paths correctly

### Useful Commands

```bash
# Check all resources
kubectl get all -n ai-interviewer

# Check pod logs
kubectl logs -n ai-interviewer -l app.kubernetes.io/name=ai-interviewer-backend

# Describe service for troubleshooting
kubectl describe svc ai-interviewer-loadbalancer -n ai-interviewer

# Check Redis collections
kubectl exec -n ai-interviewer deployment/ai-interviewer-redis -- redis-cli KEYS "*"

# Restart a deployment
kubectl rollout restart deployment/ai-interviewer-grafana -n ai-interviewer
```

## Production Considerations

1. **Secrets Management**: Use external secret management (e.g., Kubernetes secrets with encryption at rest)
2. **Persistent Volumes**: Configure persistent storage for PostgreSQL, Redis, and MinIO
3. **Resource Limits**: Adjust CPU/memory limits based on actual usage
4. **Ingress Controller**: Consider using a production ingress controller instead of LoadBalancer
5. **TLS Certificates**: Use cert-manager for automatic SSL certificate management
6. **Monitoring**: Set up proper alerting rules in Grafana
7. **Backup Strategy**: Implement backup for PostgreSQL and MinIO data

## Next Steps

1. Set up persistent volumes for stateful services
2. Configure horizontal pod autoscaling
3. Implement proper monitoring and alerting
4. Set up CI/CD pipelines for automated deployments
5. Configure network policies for security