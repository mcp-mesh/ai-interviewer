# AI Interviewer System

Enterprise-grade technical screening system built on MCP Mesh architecture, designed for large organizations to efficiently screen entry and mid-level engineers.

## 📋 Quick Overview

The AI Interviewer is a distributed system that uses multiple specialized AI agents to conduct technical interviews. It features secure OAuth authentication, intelligent document processing, real-time interview chat, and comprehensive evaluation.

## 🏗️ System Architecture

- **Server-Side OAuth**: Secure authentication with Google, GitHub, Microsoft, Apple
- **Document Processing**: PDF/Word resume parsing with Claude AI
- **MCP Mesh Services**: Distributed microservices for scalability
- **Real-Time Chat**: WebSocket-based interview interface
- **Fraud Prevention**: Foundation for tab/window switching detection

## 📁 Documentation Structure

| Document | Description |
|----------|-------------|
| [`AI_INTERVIEWER_ARCHITECTURE.md`](./AI_INTERVIEWER_ARCHITECTURE.md) | **Main architecture document** - Complete system design, components, and technical implementation |
| [`DEVELOPMENT_GUIDE.md`](./DEVELOPMENT_GUIDE.md) | **Development setup guide** - OAuth testing options, local HTTPS, mock auth, and workflows |
| [`AI_INTERVIEWER_ARCHITECTURE_UPDATE.md`](./AI_INTERVIEWER_ARCHITECTURE_UPDATE.md) | **Recent updates** - DEV_MODE environment variable changes |

## 🚀 Quick Start (Production)

```bash
# 1. Set your API keys
export TF_VAR_anthropic_api_key="your-claude-api-key"
export TF_VAR_openai_api_key="your-openai-api-key"
export TF_VAR_google_client_secret="your-google-oauth-secret"

# 2. Deploy complete system
cd terraform && terraform init && terraform apply

# 3. Access your application
curl -k https://interviews.ink/health
# 🎉 Production ready with SSL certificates!
```

**One command deployment** - Complete Kubernetes infrastructure with SSL, OAuth, and observability.

## 🔐 Authentication Modes

### Development Mode
- **Environment**: `DEV_MODE=true`  
- **Authentication**: Auto-created dev user session
- **Use Case**: Local development and testing

### Production Mode  
- **Environment**: `DEV_MODE=false`
- **Authentication**: OAuth with Google, GitHub, Microsoft, Apple
- **Requirements**: HTTPS domain with valid SSL certificates

## 🎯 Target Use Case

**Enterprise Technical Screening**
- Large organizations receiving high-volume resumes
- Screening entry to mid-level engineering candidates
- Structured technical interviews with AI evaluation
- Fraud prevention and security measures

## 🛠️ Technology Stack

- **Backend**: FastAPI + MCP Mesh + Redis sessions
- **Frontend**: Static HTML/CSS/JavaScript (no complex frameworks)
- **AI Processing**: Claude API for resume parsing and question generation
- **Authentication**: Server-side OAuth2 Authorization Code flow
- **Storage**: Redis for sessions, PostgreSQL for registry
- **Deployment**: Kubernetes with SSL/HTTPS

## 📖 Getting Started

### 🚀 One-Step Installation (Production Ready)

Deploy the complete AI Interviewer system with SSL certificates to Kubernetes:

```bash
# 1. Set your API keys (required)
export TF_VAR_anthropic_api_key="your-claude-api-key"
export TF_VAR_openai_api_key="your-openai-api-key"
export TF_VAR_google_client_secret="your-google-oauth-secret"

# 2. Deploy everything
cd terraform
terraform init
terraform apply

# 3. Access your application
echo "🎉 Application ready at: https://interviews.ink"
echo "📊 Grafana available at: https://interviews.ink/grafana (admin/admin)"
```

**Result**: Complete production deployment with:
- ✅ SSL certificates for interviews.ink
- ✅ OAuth authentication 
- ✅ All microservices running
- ✅ Grafana observability dashboard
- ✅ Distributed tracing with Tempo

### 🛠️ Step-by-Step Installation (Recommended for Learning)

For better understanding and troubleshooting:

```bash
# 1. Environment Setup
cd terraform
cp .env.example .bashrc_additions
# Edit .bashrc_additions with your API keys, then:
source .bashrc_additions

# 2. Initialize Terraform
terraform init

# 3. Deploy Infrastructure Only
terraform apply \
  -target=kubernetes_namespace.ai_interviewer \
  -target=kubernetes_deployment.postgres \
  -target=kubernetes_deployment.redis \
  -target=kubernetes_deployment.minio \
  -target=null_resource.metallb_setup

# 4. Deploy Application Services  
terraform apply \
  -target=kubernetes_deployment.backend \
  -target=kubernetes_deployment.registry \
  -target=kubernetes_deployment.pdf_extractor \
  -target=kubernetes_deployment.interview_agent \
  -target=kubernetes_deployment.llm_agent \
  -target=kubernetes_deployment.openai_llm_agent

# 5. Deploy Gateway and Observability
terraform apply \
  -target=kubernetes_deployment.nginx_gateway \
  -target=kubernetes_deployment.grafana \
  -target=kubernetes_deployment.tempo

# 6. Complete Deployment
terraform apply
```

### 🔍 Verification Steps

After deployment, verify everything is working:

```bash
# 1. Check all pods are running
kubectl get pods -n ai-interviewer

# 2. Test health endpoint
curl -k https://interviews.ink/health
# Expected: "healthy"

# 3. Test SSL certificate
openssl s_client -connect interviews.ink:443 -servername interviews.ink < /dev/null 2>/dev/null | openssl x509 -noout -dates
# Expected: Valid Let's Encrypt certificate

# 4. Test application access
curl -I https://interviews.ink/
# Expected: HTTP/2 200 with redirect to login

# 5. Verify Grafana dashboard
curl -I https://interviews.ink/grafana/
# Expected: HTTP/2 302 (redirect to login)

# 6. Check distributed tracing
kubectl exec -n ai-interviewer deployment/ai-interviewer-backend -- curl -s http://ai-interviewer-tempo:3200/api/search | grep -o '"traceID"' | wc -l
# Expected: Number > 0 (traces found)

# 7. Verify all services
kubectl get services -n ai-interviewer
# Expected: All services with ClusterIP or LoadBalancer

# 8. Check external access
terraform output external_urls
# Expected: URLs for main app, Grafana, and health check
```

### 🐛 Troubleshooting

Common issues and solutions:

```bash
# Pods not starting
kubectl describe pods -n ai-interviewer | grep -A 5 "Events:"

# SSL certificate issues  
kubectl get secret interviews-ink-tls -n ai-interviewer -o yaml

# External access problems
kubectl get service ai-interviewer-nginx-gateway -n ai-interviewer

# Grafana not loading
kubectl logs -n ai-interviewer deployment/ai-interviewer-grafana

# Tracing not working
kubectl logs -n ai-interviewer deployment/ai-interviewer-registry | grep -i trace
```

### 📋 Prerequisites

- **Kubernetes**: minikube or any Kubernetes cluster  
- **Terraform**: v1.5+ with Kubernetes provider
- **Domain**: interviews.ink and www.interviews.ink pointing to your server
- **SSL Certificates**: Let's Encrypt certificates (see [SSL-README.md](./SSL-README.md))
- **API Keys**: Anthropic (Claude) and OpenAI API keys
- **OAuth**: Google OAuth client ID and secret

### 📚 Additional Documentation

1. **Architecture**: Read [`AI_INTERVIEWER_ARCHITECTURE.md`](./AI_INTERVIEWER_ARCHITECTURE.md)
2. **Development**: Follow [`DEVELOPMENT_GUIDE.md`](./DEVELOPMENT_GUIDE.md)  
3. **SSL Management**: See [`SSL-README.md`](./SSL-README.md)
4. **Terraform Details**: Check `terraform/README.md`

## 🔄 Latest Updates

- **DEV_MODE Environment Variable**: Simplified development authentication bypass
- **Server-Side Sessions**: Secure OAuth implementation with httpOnly cookies  
- **Static Frontend**: Lightweight HTML/JS instead of complex React setup
- **Enterprise Focus**: Registered users only, fraud prevention foundation

## 📞 Support

For questions about the AI Interviewer system architecture, refer to the documentation or create an issue in the repository.

---

**Note**: This system is designed for legitimate technical screening purposes. It includes security measures and is intended for authorized use by organizations conducting interviews with candidate consent.