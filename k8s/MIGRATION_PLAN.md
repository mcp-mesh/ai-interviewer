# AI Interviewer Kubernetes Migration Plan

## Overview

This document outlines the migration strategy to move the AI Interviewer application from Docker Compose to Kubernetes, following MCP Mesh best practices and patterns.

## Architecture Analysis

### Current Docker Compose Components

| Component | Type | Purpose | Docker Image | Dependencies |
|-----------|------|---------|--------------|--------------|
| **Backend (FastAPI)** | API Server | REST API & Auth | `ai-interviewer-fastapi` | Redis, Postgres, Registry |
| **PDF Extractor** | MCP Agent | Document processing | `ai-interviewer-pdf-extractor` | Registry, MinIO |
| **Interview Agent** | MCP Agent | Interview orchestration | `ai-interviewer-interview-agent` | Registry, LLM Agent |
| **Claude LLM Agent** | MCP Agent | Claude AI language processing | `ai-interviewer-claude-llm-agent` | Registry, OpenAI LLM |
| **OpenAI LLM Agent** | MCP Agent | OpenAI integration | `ai-interviewer-openai-llm-agent` | Registry |
| **Registry** | MCP Service | Service discovery | `mcpmesh/registry:0.5` | Postgres, Redis |
| **Postgres** | Database | Persistent storage | `postgres:15-alpine` | - |
| **Redis** | Cache/Queue | Session storage | `redis:7-alpine` | - |
| **MinIO** | Object Storage | File storage | `minio/minio:latest` | - |
| **Nginx Gateway** | Reverse Proxy | Request routing | `openresty/openresty` | All services |
| **Grafana** | Observability | Monitoring dashboard | `grafana/grafana:11.4.0` | Tempo |
| **Tempo** | Observability | Distributed tracing | `grafana/tempo:2.8.1` | - |

## Migration Strategy

### Phase 1: Foundation Services
- **Namespace**: `ai-interviewer`
- **PostgreSQL**: StatefulSet with persistent storage
- **Redis**: Deployment with service
- **MinIO**: StatefulSet with persistent storage
- **Tempo**: Deployment for distributed tracing

### Phase 2: MCP Mesh Services
- **Registry**: Official `mcpmesh/registry:0.5` image
- **Use existing MCP runtime patterns** from examples/k8s

### Phase 3: AI Interviewer Services
- **Backend**: Use `mcpmesh/python-runtime:0.5.3` + source code volume
- **Agents**: Use `mcpmesh/python-runtime:0.5.3` + source code volumes
- **All agents**: Follow MCP Mesh deployment patterns

### Phase 4: Gateway & Observability
- **Nginx Gateway**: OpenResty deployment 
- **Ingress**: Route to Nginx (single entry point)
- **Grafana**: Enhanced with AI Interviewer dashboards

## Directory Structure

```
ai-interviewer/k8s/
├── base/
│   ├── kustomization.yaml
│   ├── namespace.yaml
│   ├── database/
│   │   ├── postgres-statefulset.yaml
│   │   ├── postgres-service.yaml
│   │   └── postgres-configmap.yaml
│   ├── storage/
│   │   ├── redis-deployment.yaml
│   │   ├── redis-service.yaml
│   │   ├── minio-statefulset.yaml
│   │   ├── minio-service.yaml
│   │   └── minio-configmap.yaml
│   ├── backend/
│   │   ├── configmap.yaml
│   │   ├── secret.yaml
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   ├── agents/
│   │   ├── source-code-configmap.yaml
│   │   ├── agent-config-configmap.yaml
│   │   ├── secret.yaml
│   │   ├── pdf-extractor-deployment.yaml
│   │   ├── interview-agent-deployment.yaml
│   │   ├── claude-llm-agent-deployment.yaml
│   │   └── openai-llm-agent-deployment.yaml
│   ├── gateway/
│   │   ├── configmap.yaml
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   ├── observability/
│   │   ├── tempo/
│   │   ├── grafana/
│   │   └── registry/
│   └── ingress.yaml
├── overlays/
│   ├── dev/
│   │   ├── kustomization.yaml
│   │   └── patches/
│   └── prod/
│       ├── kustomization.yaml
│       └── patches/
└── MIGRATION_PLAN.md
```

## Key Migration Decisions

### 1. **Custom Docker Images (Not ConfigMaps)**
- **Base Image**: `mcpmesh/python-runtime:0.5.3`
- **Build Strategy**: Custom Docker images with embedded application code
- **Rationale**: AI Interviewer has complex multi-file applications (not simple single-file agents)
- **Benefits**: Proper dependency management, faster startup, production-ready

### 2. **K8s-Specific Build System**
- **Build Tool**: Dedicated `k8s/Makefile` for image building and deployment
- **Image Strategy**: Build all components as separate Docker images
- **Development**: Use existing Dockerfiles with MCP Mesh runtime base
- **Pattern**: `make k8s-build-all` → `make k8s-deploy-dev`

### 3. **Ingress Architecture**
- **Single Entry Point**: Ingress → Nginx Gateway → Internal Services
- **Host-based Routing**: `ai-interviewer.local` with path-based routing
- **SSL Termination**: At ingress level for production

### 4. **Storage Strategy**
- **PostgreSQL**: PVC with ReadWriteOnce (StatefulSet)
- **Redis**: Deployment (stateless, can be scaled)
- **MinIO**: PVC with ReadWriteOnce (StatefulSet)
- **Agent Logs**: EmptyDir volumes (ephemeral)

### 5. **Security & Best Practices**
- **Non-root containers**: All services run as non-root users
- **Network Policies**: Restrict inter-pod communication
- **Secrets Management**: Kubernetes secrets for sensitive data
- **Resource Limits**: CPU/Memory limits for all containers
- **Health Checks**: Comprehensive liveness/readiness probes

## Service Configuration

### Backend FastAPI Service
```yaml
name: ai-interviewer-backend
image: mcpmesh/python-runtime:0.5.3
port: 8080
replicas: 2
resources:
  requests: { cpu: 200m, memory: 256Mi }
  limits: { cpu: 1000m, memory: 1Gi }
```

### MCP Agents
```yaml
base_image: mcpmesh/python-runtime:0.5.3
port: 8090
replicas: 1
resources:
  requests: { cpu: 100m, memory: 128Mi }
  limits: { cpu: 500m, memory: 512Mi }
```

### Database Services
```yaml
postgres:
  image: postgres:15-alpine
  storage: 10Gi
  replicas: 1

redis:
  image: redis:7-alpine
  replicas: 1

minio:
  image: minio/minio:latest
  storage: 20Gi
  replicas: 1
```

## Environment Variables & Configuration

### Backend Environment
```yaml
MCP_MESH_REGISTRY_HOST: ai-interviewer-registry
MCP_MESH_REGISTRY_PORT: "8000"
POSTGRES_HOST: ai-interviewer-postgres
REDIS_HOST: ai-interviewer-redis
MINIO_ENDPOINT: ai-interviewer-minio:9000
```

### Agent Environment
```yaml
MCP_MESH_REGISTRY_HOST: ai-interviewer-registry
MCP_MESH_REGISTRY_PORT: "8000"
MCP_MESH_HTTP_PORT: "8090"
REDIS_URL: redis://ai-interviewer-redis:6379
```

## Ingress Routing Strategy

### Host-based Routing
```yaml
host: ai-interviewer.local
paths:
  /:           → nginx-gateway:80 → backend:8080
  /api/:       → nginx-gateway:80 → backend:8080  
  /static/:    → nginx-gateway:80 → backend:8080
  /health:     → nginx-gateway:80 → backend:8080
```

### Internal Service Mesh
```yaml
nginx-gateway → backend (FastAPI)
backend → agents (MCP calls via registry)
agents ↔ registry (service discovery)
all → postgres, redis, minio (storage)
```

## Deployment Commands

### Quick Development Deployment
```bash
# One-command deployment to K8s
cd ai-interviewer/
make k8s-quick-dev

# This will:
# 1. Set minikube context
# 2. Build all Docker images
# 3. Deploy to K8s development
# 4. Add ingress hosts to /etc/hosts
# 5. Show access URLs
```

### Manual Step-by-Step Deployment
```bash
# 1. Setup minikube context and build images
make k8s-context
make k8s-build-all

# 2. Deploy to K8s
make k8s-setup
make k8s-deploy-dev

# 3. Configure local access
make k8s-ingress-hosts

# 4. Access application
curl http://ai-interviewer.local/health
```

### Production Deployment
```bash
# Production deployment with optimized settings
make k8s-deploy-prod

# Monitor deployment
make k8s-status
make k8s-logs
```

### Development Workflow
```bash
# Make code changes, then quick update
make k8s-quick-update

# View logs
make k8s-logs-backend
make k8s-logs-agents

# Debug issues
make k8s-describe-failing
```

## Migration Checklist

### Prerequisites
- [ ] Minikube or Kubernetes cluster running
- [ ] kubectl configured
- [ ] Ingress controller installed
- [ ] Storage class available

### Phase 1: Foundation
- [ ] Create namespace and basic resources
- [ ] Deploy PostgreSQL with persistent storage
- [ ] Deploy Redis
- [ ] Deploy MinIO with persistent storage  
- [ ] Deploy Tempo for distributed tracing
- [ ] Verify foundation services health

### Phase 2: MCP Mesh
- [ ] Deploy Registry service
- [ ] Verify registry connectivity to PostgreSQL
- [ ] Test registry health endpoint
- [ ] Configure distributed tracing

### Phase 3: AI Interviewer Services
- [ ] Create source code ConfigMaps
- [ ] Deploy backend FastAPI service
- [ ] Deploy PDF extractor agent
- [ ] Deploy interview agent
- [ ] Deploy LLM agents
- [ ] Verify agent registration with registry
- [ ] Test inter-agent communication

### Phase 4: Gateway & Access
- [ ] Deploy Nginx gateway
- [ ] Configure ingress routing
- [ ] Test external access via ingress
- [ ] Deploy Grafana with AI Interviewer dashboards
- [ ] Verify end-to-end functionality

### Phase 5: Production Readiness
- [ ] Configure resource limits and requests
- [ ] Set up horizontal pod autoscaling
- [ ] Configure network policies
- [ ] Set up monitoring and alerting
- [ ] Configure backup strategies
- [ ] Load testing and performance tuning

## Rollback Strategy

### Emergency Rollback
1. **Scale down K8s deployments**: `kubectl scale deployment --replicas=0 -n ai-interviewer`
2. **Start Docker Compose**: `cd ai-interviewer && docker compose up -d`
3. **Verify service health**: Check all endpoints

### Data Migration Rollback
1. **Export K8s data**: 
   - PostgreSQL: `kubectl exec -n ai-interviewer postgres-0 -- pg_dump`
   - Redis: `kubectl exec -n ai-interviewer redis-pod -- redis-cli --rdb`
   - MinIO: Use mc client to sync data
2. **Import to Docker Compose**: Restore data to local volumes

## Testing Strategy

### Health Verification
```bash
# Check all pod status
kubectl get pods -n ai-interviewer

# Test backend health
curl -s http://ai-interviewer.local/health | jq

# Test agent registration
curl -s http://ai-interviewer.local/api/registry/agents | jq

# Test MCP tool discovery
curl -X POST http://ai-interviewer.local/mcp/pdf-extractor \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}'
```

### End-to-End Testing
1. **User Authentication**: Test Google OAuth flow
2. **Role Creation**: Create test interview roles
3. **Interview Flow**: Complete full interview process
4. **File Upload**: Test resume upload and processing
5. **Agent Communication**: Verify MCP agent interactions
6. **Data Persistence**: Verify data survives pod restarts

## Performance Considerations

### Resource Planning
```yaml
Small Cluster (Development):
  Total: 4 CPU, 8GB RAM
  Backend: 2 replicas × (200m CPU, 256Mi RAM)
  Agents: 4 × (100m CPU, 128Mi RAM)
  Storage: PostgreSQL (1 CPU, 1GB), Redis (100m, 256Mi), MinIO (500m, 512Mi)

Medium Cluster (Production):
  Total: 8 CPU, 16GB RAM  
  Backend: 3 replicas × (500m CPU, 512Mi RAM)
  Agents: 4 × (200m CPU, 256Mi RAM)
  Storage: PostgreSQL (2 CPU, 2GB), Redis (200m, 512Mi), MinIO (1 CPU, 1GB)
```

### Scaling Strategy
- **Backend**: Horizontal scaling (2-5 replicas)
- **Agents**: Vertical scaling (increase resource limits)
- **Storage**: Scale up storage volumes as needed
- **Registry**: Single replica (stateful)

## Monitoring & Observability

### Metrics Collection
- **Prometheus**: Collect K8s and application metrics
- **Grafana**: AI Interviewer specific dashboards
- **Distributed Tracing**: Tempo integration
- **Logging**: Centralized logging with structured logs

### Alert Configuration
- Pod crash loops or high restart counts
- Resource exhaustion (CPU, memory, storage)
- Agent registration failures
- Database connection issues
- Interview processing failures

## Security Considerations

### Network Security
- Network policies to restrict inter-pod communication
- TLS termination at ingress
- Internal service communication encryption

### Data Security
- Kubernetes secrets for sensitive configuration
- RBAC for service accounts
- Pod security policies
- Storage encryption at rest

### Container Security
- Non-root container execution
- Read-only root filesystems where possible
- Minimal base images
- Regular security scanning

## Conclusion

This migration plan provides a structured approach to move AI Interviewer from Docker Compose to Kubernetes while:

1. **Leveraging MCP Mesh ecosystem**: Using official runtime images
2. **Maintaining development velocity**: ConfigMap-based source deployment
3. **Ensuring production readiness**: Proper resource management, health checks, security
4. **Providing rollback options**: Clear fallback to Docker Compose
5. **Following best practices**: Security, observability, and scalability

The phased approach allows for incremental migration with testing at each stage, minimizing risk and ensuring system reliability throughout the transition.