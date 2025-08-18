# AI Interviewer Kubernetes Build & Deployment Makefile
# 🚫 NO PORT-FORWARD OR TUNNEL REQUIRED - Pure MetalLB Layer 2 LoadBalancer! 🚫
# Builds Docker images and deploys to Kubernetes

# Configuration
REGISTRY ?= ai-interviewer
TAG ?= latest
NAMESPACE ?= ai-interviewer
CONTEXT ?= minikube
MCP_MESH_VERSION ?= 0.5.3
UI_MODE ?= prod
INGRESS_MODE ?= host

# K8s Environment
K8S_BASE_DIR := k8s/base
K8S_DEV_DIR := k8s/overlays/dev
K8S_PROD_DIR := k8s/overlays/prod

.PHONY: help
help:
	@echo "AI Interviewer Kubernetes Build & Deployment"
	@echo ""
	@echo "🏗️  BUILD IMAGES:"
	@echo "  make k8s-build-all      - Build all K8s images"
	@echo "  make k8s-build-backend  - Build backend FastAPI image"
	@echo "  make k8s-build-agents   - Build all agent images"
	@echo "  make k8s-build-gateway  - Build nginx gateway image with UI"
	@echo "  make k8s-build-ui       - Build Next.js UI only"
	@echo "  make k8s-build-ui-prod  - Build UI (prod mode: copy/paste disabled)"
	@echo "  make k8s-build-ui-dev   - Build UI (dev mode: copy/paste enabled)"
	@echo ""
	@echo "🚀 DEPLOY TO K8S:"
	@echo "  make k8s-deploy-dev     - Deploy to K8s (development)"
	@echo "  make k8s-deploy-prod    - Deploy to K8s (production)"
	@echo "  make k8s-deploy-base    - Deploy base components only"
	@echo "  make k8s-quick-dev      - Quick dev deployment (prod UI)"
	@echo "  make k8s-quick-dev-ui-enabled - Quick dev (dev UI, copy/paste enabled)"
	@echo "  make k8s-quick-prod     - Quick production deployment"
	@echo "  make k8s-deploy-ip-access - Deploy with IP-based access"
	@echo "  make k8s-deploy-nginx-only - Deploy nginx gateway only (test LoadBalancer)"
	@echo ""
	@echo "🔧 K8S OPERATIONS:"
	@echo "  make k8s-setup          - Setup K8s environment (namespace, etc)"
	@echo "  make k8s-setup-metallb  - Setup MetalLB LoadBalancer addon"
	@echo "  make k8s-setup-iptables - Setup iptables for Mac access (requires sudo)"
	@echo "  make k8s-status         - Show K8s deployment status"
	@echo "  make k8s-logs           - Show logs from all pods"
	@echo "  make k8s-clean          - Clean up K8s resources"
	@echo "  make k8s-restart        - Restart all deployments"
	@echo "  make k8s-update-ui-only - Update UI only"
	@echo "  make k8s-update-backend-only - Update backend only"
	@echo ""
	@echo "🔍 UTILITIES:"
	@echo "  make k8s-context        - Setup minikube context"
	@echo "  make k8s-port-forward   - Port forward to nginx gateway"
	@echo "  make k8s-ingress-hosts  - Add ingress hosts to /etc/hosts"
	@echo "  make k8s-test-health    - Test all service health endpoints"
	@echo "  make k8s-test-mcp-tools - Test MCP tool discovery"
	@echo "  make k8s-show-ip-access - Show IP-based access URLs"
	@echo ""
	@echo "⚙️  CONFIGURATION:"
	@echo "  REGISTRY=$(REGISTRY)     - Docker registry prefix"
	@echo "  TAG=$(TAG)               - Docker image tag"
	@echo "  NAMESPACE=$(NAMESPACE)   - K8s namespace"
	@echo "  CONTEXT=$(CONTEXT)       - K8s context"
	@echo "  UI_MODE=$(UI_MODE)       - UI build mode (prod|dev)"
	@echo "  INGRESS_MODE=$(INGRESS_MODE) - Ingress mode (host|ip|both)"

# ==============================================================================
# BUILD TARGETS
# ==============================================================================

.PHONY: k8s-context
k8s-context:
	@echo "🔧 Setting up minikube Docker context..."
	eval $$(minikube docker-env)
	@echo "✅ Docker context set to minikube"

.PHONY: k8s-build-all
k8s-build-all: k8s-context k8s-build-backend k8s-build-agents k8s-build-gateway
	@echo "✅ All K8s images built successfully"

.PHONY: k8s-build-backend
k8s-build-backend: k8s-context
	@echo "🏗️ Building backend FastAPI image..."
	cd .. && docker build -f ai-interviewer/backend/Dockerfile \
		--build-arg MCP_MESH_VERSION=$(MCP_MESH_VERSION) \
		-t $(REGISTRY)/backend:$(TAG) \
		.
	@echo "✅ Backend image built: $(REGISTRY)/backend:$(TAG)"

.PHONY: k8s-build-agents
k8s-build-agents: k8s-context k8s-build-pdf-extractor k8s-build-interview-agent k8s-build-llm-agent k8s-build-openai-llm-agent
	@echo "✅ All agent images built successfully"

.PHONY: k8s-build-pdf-extractor
k8s-build-pdf-extractor: k8s-context
	@echo "🏗️ Building PDF Extractor agent image..."
	cd .. && docker build -f ai-interviewer/services/pdf_extractor_agent/Dockerfile \
		--build-arg MCP_MESH_VERSION=$(MCP_MESH_VERSION) \
		-t $(REGISTRY)/pdf-extractor:$(TAG) \
		.
	@echo "✅ PDF Extractor image built: $(REGISTRY)/pdf-extractor:$(TAG)"

.PHONY: k8s-build-interview-agent
k8s-build-interview-agent: k8s-context
	@echo "🏗️ Building Interview agent image..."
	cd .. && docker build -f ai-interviewer/services/interview_agent/Dockerfile \
		--build-arg MCP_MESH_VERSION=$(MCP_MESH_VERSION) \
		-t $(REGISTRY)/interview-agent:$(TAG) \
		.
	@echo "✅ Interview Agent image built: $(REGISTRY)/interview-agent:$(TAG)"

.PHONY: k8s-build-llm-agent
k8s-build-llm-agent: k8s-context
	@echo "🏗️ Building LLM agent image..."
	cd .. && docker build -f ai-interviewer/services/llm_agent/Dockerfile \
		--build-arg MCP_MESH_VERSION=$(MCP_MESH_VERSION) \
		-t $(REGISTRY)/llm-agent:$(TAG) \
		.
	@echo "✅ LLM Agent image built: $(REGISTRY)/llm-agent:$(TAG)"

.PHONY: k8s-build-openai-llm-agent
k8s-build-openai-llm-agent: k8s-context
	@echo "🏗️ Building OpenAI LLM agent image..."
	cd .. && docker build -f ai-interviewer/services/openai_llm_agent/Dockerfile \
		--build-arg MCP_MESH_VERSION=$(MCP_MESH_VERSION) \
		-t $(REGISTRY)/openai-llm-agent:$(TAG) \
		.
	@echo "✅ OpenAI LLM Agent image built: $(REGISTRY)/openai-llm-agent:$(TAG)"

.PHONY: k8s-build-gateway
k8s-build-gateway: k8s-context k8s-build-ui
	@echo "🏗️ Building Nginx Gateway image with UI..."
	cd .. && docker build -f k8s/gateway/Dockerfile \
		-t $(REGISTRY)/nginx-gateway:$(TAG) \
		.
	@echo "✅ Gateway image built: $(REGISTRY)/nginx-gateway:$(TAG)"

.PHONY: k8s-build-ui
k8s-build-ui:
ifeq ($(UI_MODE),dev)
	@$(MAKE) k8s-build-ui-dev
else
	@$(MAKE) k8s-build-ui-prod
endif

.PHONY: k8s-build-ui-prod
k8s-build-ui-prod:
	@echo "🎨 Building UI (PRODUCTION mode - security enabled)..."
	cd ../frontend && npm ci
	cd ../frontend && npm run build
	@echo "✅ UI built in production mode (copy/paste disabled)"

.PHONY: k8s-build-ui-dev
k8s-build-ui-dev:
	@echo "🎨 Building UI (DEVELOPMENT mode - security disabled)..."
	cd ../frontend && npm ci
	cd ../frontend && npm run build:dev
	@echo "✅ UI built in development mode (copy/paste enabled)"

# ==============================================================================
# DEPLOYMENT TARGETS
# ==============================================================================

.PHONY: k8s-setup
k8s-setup:
	@echo "🔧 Setting up K8s environment..."
	minikube kubectl -- create namespace $(NAMESPACE) --dry-run=client -o yaml | minikube kubectl -- apply -f -
	@echo "✅ K8s environment ready"

.PHONY: k8s-setup-metallb
k8s-setup-metallb:
	@echo "🔧 Setting up MetalLB LoadBalancer addon..."
	@echo ""
	@echo "🔧 Enabling MetalLB addon in minikube..."
	minikube addons enable metallb
	@echo ""
	@echo "🔧 Applying MetalLB configuration with minikube IP range..."
	minikube kubectl -- apply -f metallb-config.yaml
	@echo "🔄 Restarting MetalLB pods to pick up new configuration..."
	minikube kubectl -- delete pods -n metallb-system -l app=metallb
	@echo "🛤️  Adding route from minikube to host network..."
	minikube ssh 'sudo ip route add 10.211.55.0/24 via 192.168.49.1 || true'
	@echo ""
	@echo "✅ MetalLB setup complete!"
	@echo ""

.PHONY: k8s-setup-iptables
k8s-setup-iptables:
	@echo "🔧 Configuring iptables for Mac access..."
	@echo ""
	@echo "⚠️  WARNING: This will modify your iptables rules and requires sudo"
	@echo "⚠️  This configures traffic forwarding from VM IP (10.211.55.3) to MetalLB service (192.168.49.100)"
	@echo ""
	@read -p "Continue? [y/N]: " confirm && [ "$$confirm" = "y" ] || exit 1
	@echo ""
	@echo "📡 Setting up DNAT rules..."
	sudo iptables -t nat -A PREROUTING -d 10.211.55.3 -p tcp --dport 443 -j DNAT --to-destination 192.168.49.100:443
	sudo iptables -t nat -A PREROUTING -d 10.211.55.3 -p tcp --dport 80 -j DNAT --to-destination 192.168.49.100:80
	sudo iptables -t nat -A OUTPUT -d 10.211.55.3 -p tcp --dport 443 -j DNAT --to-destination 192.168.49.100:443
	sudo iptables -t nat -A OUTPUT -d 10.211.55.3 -p tcp --dport 80 -j DNAT --to-destination 192.168.49.100:80
	@echo "📡 Setting up MASQUERADE rules..."
	sudo iptables -t nat -A POSTROUTING -d 192.168.49.100 -p tcp -m multiport --dports 80,443 -j MASQUERADE
	sudo iptables -t nat -A POSTROUTING -o enp0s5 -s 10.211.55.0/24 -d 192.168.49.100 -j MASQUERADE
	@echo "📡 Setting up FORWARD rules..."
	sudo iptables -I FORWARD 1 -i enp0s5 -o br-84f3ff1e892b -d 192.168.49.100 -p tcp --dport 443 -j ACCEPT
	sudo iptables -I FORWARD 2 -i br-84f3ff1e892b -o enp0s5 -s 192.168.49.100 -p tcp --sport 443 -j ACCEPT
	sudo iptables -I FORWARD 3 -i enp0s5 -o br-84f3ff1e892b -d 192.168.49.100 -p tcp --dport 80 -j ACCEPT
	sudo iptables -I FORWARD 4 -i br-84f3ff1e892b -o enp0s5 -s 192.168.49.100 -p tcp --sport 80 -j ACCEPT
	sudo iptables -A FORWARD -d 192.168.49.100 -p tcp -m multiport --dports 80,443 -j ACCEPT
	sudo iptables -A FORWARD -s 192.168.49.100 -p tcp -m multiport --sports 80,443 -j ACCEPT
	@echo ""
	@echo "✅ iptables configuration complete!"
	@echo "🔍 Testing internet connectivity..."
	ping -c 1 8.8.8.8 && echo "✅ Internet connectivity preserved" || echo "❌ Internet connectivity lost - check rules"
	@echo ""
	@echo "💡 To make rules persistent: sudo apt install iptables-persistent && sudo netfilter-persistent save"

.PHONY: k8s-deploy-base
k8s-deploy-base: k8s-setup
	@echo "🚀 Deploying base components..."
	kubectl apply -k $(K8S_BASE_DIR)
	@echo "✅ Base components deployed"

.PHONY: k8s-deploy-dev
k8s-deploy-dev: k8s-build-all k8s-setup
	@echo "🚀 Deploying to K8s (development)..."
	kubectl apply -k $(K8S_DEV_DIR)
	@$(MAKE) k8s-wait-ready
	@echo "✅ Development deployment complete"

.PHONY: k8s-deploy-prod
k8s-deploy-prod: k8s-build-all k8s-setup
	@echo "🚀 Deploying to K8s (production)..."
	kubectl apply -k $(K8S_PROD_DIR)
	@$(MAKE) k8s-wait-ready
	@echo "✅ Production deployment complete"

.PHONY: k8s-deploy-ip-access
k8s-deploy-ip-access: k8s-build-all k8s-setup
	@echo "🚀 Deploying with IP-based access..."
	kubectl apply -k $(K8S_BASE_DIR)
	kubectl apply -f $(K8S_BASE_DIR)/ingress-ip.yaml
	@$(MAKE) k8s-wait-ready
	@$(MAKE) k8s-show-ip-access
	@echo "✅ IP-based deployment complete"

.PHONY: k8s-deploy-nginx-only
k8s-deploy-nginx-only: k8s-setup k8s-build-gateway
	@echo "🚀 Deploying nginx gateway only (LoadBalancer test)..."
	minikube kubectl -- apply -f base/gateway/deployment.yaml
	minikube kubectl -- apply -f base/gateway/service.yaml
	@echo ""
	@echo "⏳ Waiting for nginx deployment..."
	minikube kubectl -- wait --for=condition=available --timeout=60s deployment/ai-interviewer-nginx-gateway -n $(NAMESPACE)
	@echo ""
	@echo "📊 Checking LoadBalancer status..."
	minikube kubectl -- get svc ai-interviewer-nginx-gateway -n $(NAMESPACE)
	@echo ""
	@LB_IP=$$(minikube kubectl -- get svc ai-interviewer-nginx-gateway -n $(NAMESPACE) -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending"); \
	echo "LoadBalancer IP: $$LB_IP"
	@echo ""
	@if [ "$$(minikube kubectl -- get svc ai-interviewer-nginx-gateway -n $(NAMESPACE) -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null)" != "" ]; then \
		LB_IP=$$(minikube kubectl -- get svc ai-interviewer-nginx-gateway -n $(NAMESPACE) -o jsonpath='{.status.loadBalancer.ingress[0].ip}'); \
		echo "🎯 Test URLs:"; \
		echo "  Direct MetalLB: https://$$LB_IP/health"; \
		echo "  Via Host IP: https://10.211.55.3/health"; \
		echo ""; \
		echo "🧪 Test Commands:"; \
		echo "  curl -k https://$$LB_IP/health"; \
		echo "  curl -k https://10.211.55.3/health"; \
	else \
		echo "⏳ LoadBalancer IP still pending..."; \
		echo "Check MetalLB setup: make k8s-setup-metallb"; \
	fi
	@echo "✅ Nginx-only deployment complete!"

.PHONY: k8s-wait-ready
k8s-wait-ready:
	@echo "⏳ Waiting for deployments to be ready..."
	kubectl wait --for=condition=available --timeout=300s deployment -l app.kubernetes.io/part-of=ai-interviewer -n $(NAMESPACE)
	@echo "✅ All deployments are ready"

# ==============================================================================
# OPERATIONS TARGETS
# ==============================================================================

.PHONY: k8s-status
k8s-status:
	@echo "📊 K8s Deployment Status:"
	@echo ""
	@echo "PODS:"
	kubectl get pods -n $(NAMESPACE) -o wide
	@echo ""
	@echo "SERVICES:"
	kubectl get services -n $(NAMESPACE)
	@echo ""
	@echo "INGRESS:"
	kubectl get ingress -n $(NAMESPACE)
	@echo ""
	@echo "PERSISTENT VOLUMES:"
	kubectl get pvc -n $(NAMESPACE)

.PHONY: k8s-logs
k8s-logs:
	@echo "📋 Showing logs from all pods..."
	kubectl logs -f -l app.kubernetes.io/part-of=ai-interviewer -n $(NAMESPACE) --max-log-requests=10

.PHONY: k8s-logs-backend
k8s-logs-backend:
	kubectl logs -f -l app.kubernetes.io/name=ai-interviewer-backend -n $(NAMESPACE)

.PHONY: k8s-logs-agents
k8s-logs-agents:
	kubectl logs -f -l app.kubernetes.io/component=agent -n $(NAMESPACE)

.PHONY: k8s-restart
k8s-restart:
	@echo "🔄 Restarting all deployments..."
	kubectl rollout restart deployment -n $(NAMESPACE)
	@$(MAKE) k8s-wait-ready

.PHONY: k8s-clean
k8s-clean:
	@echo "🧹 Cleaning up K8s resources..."
	kubectl delete namespace $(NAMESPACE) --ignore-not-found=true
	@echo "✅ Cleanup complete"

# ==============================================================================
# UTILITY TARGETS
# ==============================================================================

.PHONY: k8s-port-forward
k8s-port-forward:
	@echo "🔗 Port forwarding nginx gateway to localhost:8080..."
	kubectl port-forward service/ai-interviewer-nginx-gateway 8080:80 -n $(NAMESPACE)

.PHONY: k8s-ingress-hosts
k8s-ingress-hosts:
	@echo "🔧 Adding ingress hosts to /etc/hosts..."
	@MINIKUBE_IP=$$(minikube ip); \
	echo "$$MINIKUBE_IP ai-interviewer.local" | sudo tee -a /etc/hosts; \
	echo "$$MINIKUBE_IP registry.ai-interviewer.local" | sudo tee -a /etc/hosts; \
	echo "$$MINIKUBE_IP api.ai-interviewer.local" | sudo tee -a /etc/hosts; \
	echo "$$MINIKUBE_IP pdf-extractor.ai-interviewer.local" | sudo tee -a /etc/hosts; \
	echo "$$MINIKUBE_IP interview-agent.ai-interviewer.local" | sudo tee -a /etc/hosts; \
	echo "$$MINIKUBE_IP llm-agent.ai-interviewer.local" | sudo tee -a /etc/hosts; \
	echo "$$MINIKUBE_IP openai-llm-agent.ai-interviewer.local" | sudo tee -a /etc/hosts; \
	echo "$$MINIKUBE_IP grafana.ai-interviewer.local" | sudo tee -a /etc/hosts; \
	echo "✅ Added all AI Interviewer ingress hosts to /etc/hosts"

.PHONY: k8s-test-health
k8s-test-health:
	@echo "🏥 Testing application health..."
	@echo ""
	@echo "=== Main Application ==="
	@echo "Backend health:"
	curl -s http://ai-interviewer.local/health | jq . || echo "❌ Main app health failed"
	@echo ""
	@echo "=== Registry Service ==="
	@echo "Registry health:"
	curl -s http://registry.ai-interviewer.local/health | jq . || echo "❌ Registry health failed"
	@echo ""
	@echo "Registry agents:"
	curl -s http://registry.ai-interviewer.local/agents | jq '.agents[] | {name: .name, status: .status}' || echo "❌ Registry agents failed"
	@echo ""
	@echo "=== Direct API Access ==="
	@echo "API health:"
	curl -s http://api.ai-interviewer.local/health | jq . || echo "❌ Direct API health failed"
	@echo ""
	@echo "=== Agent Health Checks ==="
	@echo "PDF Extractor:"
	curl -s http://pdf-extractor.ai-interviewer.local/health | jq . || echo "❌ PDF extractor health failed"
	@echo ""
	@echo "Interview Agent:"
	curl -s http://interview-agent.ai-interviewer.local/health | jq . || echo "❌ Interview agent health failed"
	@echo ""
	@echo "LLM Agent:"
	curl -s http://llm-agent.ai-interviewer.local/health | jq . || echo "❌ LLM agent health failed"
	@echo ""
	@echo "OpenAI LLM Agent:"
	curl -s http://openai-llm-agent.ai-interviewer.local/health | jq . || echo "❌ OpenAI LLM agent health failed"

# ==============================================================================
# DEVELOPMENT HELPERS
# ==============================================================================

.PHONY: k8s-shell-backend
k8s-shell-backend:
	kubectl exec -it -n $(NAMESPACE) deployment/ai-interviewer-backend -- /bin/bash

.PHONY: k8s-shell-registry
k8s-shell-registry:
	kubectl exec -it -n $(NAMESPACE) deployment/ai-interviewer-registry -- /bin/bash

.PHONY: k8s-describe-failing
k8s-describe-failing:
	@echo "🔍 Describing failing pods..."
	@for pod in $$(kubectl get pods -n $(NAMESPACE) --field-selector=status.phase!=Running -o name); do \
		echo "=== $$pod ==="; \
		kubectl describe -n $(NAMESPACE) $$pod; \
		echo ""; \
	done

# ==============================================================================
# QUICK WORKFLOWS
# ==============================================================================

.PHONY: k8s-quick-dev
k8s-quick-dev: k8s-context k8s-build-all k8s-deploy-dev k8s-ingress-hosts
	@echo "🎉 Quick dev deployment complete!"
	@echo ""
	@echo "🌐 Service URLs:"
	@echo "  Main App:     http://ai-interviewer.local"
	@echo "  Registry:     http://registry.ai-interviewer.local"
	@echo "  Direct API:   http://api.ai-interviewer.local"
	@echo "  Grafana:      http://grafana.ai-interviewer.local"
	@echo ""
	@echo "🔧 Management:"
	@echo "  Status:       make k8s-status"
	@echo "  Logs:         make k8s-logs"
	@echo "  Health:       make k8s-test-health"

.PHONY: k8s-quick-dev-ui-enabled
k8s-quick-dev-ui-enabled: UI_MODE=dev
k8s-quick-dev-ui-enabled: k8s-quick-dev
	@echo "🎨 Development UI deployed (copy/paste enabled for testing)"

.PHONY: k8s-quick-prod
k8s-quick-prod: UI_MODE=prod
k8s-quick-prod: k8s-context k8s-build-all k8s-deploy-prod k8s-ingress-hosts
	@echo "🚀 Production deployment complete!"
	@echo "🔒 Production UI deployed (copy/paste disabled for security)"
	@echo ""
	@echo "🌐 Service URLs:"
	@echo "  Main App:     http://ai-interviewer.local"
	@echo "  Registry:     http://registry.ai-interviewer.local"
	@echo "  Direct API:   http://api.ai-interviewer.local"
	@echo "  Grafana:      http://grafana.ai-interviewer.local"

.PHONY: k8s-quick-update
k8s-quick-update: k8s-build-all k8s-restart
	@echo "🔄 Quick update complete!"

.PHONY: k8s-update-ui-only
k8s-update-ui-only: k8s-build-gateway
	@echo "🎨 Updating UI only..."
	kubectl rollout restart deployment/ai-interviewer-nginx-gateway -n $(NAMESPACE)
	@$(MAKE) k8s-wait-ready
	@echo "✅ UI update complete!"

.PHONY: k8s-update-backend-only
k8s-update-backend-only: k8s-build-backend
	@echo "⚙️ Updating backend only..."
	kubectl rollout restart deployment/ai-interviewer-backend -n $(NAMESPACE)
	@$(MAKE) k8s-wait-ready
	@echo "✅ Backend update complete!"

# ==============================================================================
# IMAGE MANAGEMENT
# ==============================================================================

.PHONY: k8s-list-images
k8s-list-images:
	@echo "📦 Built images:"
	docker images | grep $(REGISTRY)

.PHONY: k8s-clean-images
k8s-clean-images:
	@echo "🧹 Cleaning old images..."
	docker rmi $$(docker images $(REGISTRY) -q) 2>/dev/null || true
	@echo "✅ Old images cleaned"

# ==============================================================================
# MONITORING & DEBUGGING
# ==============================================================================

.PHONY: k8s-events
k8s-events:
	kubectl get events -n $(NAMESPACE) --sort-by='.lastTimestamp'

.PHONY: k8s-top
k8s-top:
	@echo "💻 Resource usage:"
	kubectl top pods -n $(NAMESPACE)

.PHONY: k8s-debug-network
k8s-debug-network:
	@echo "🔍 Testing network connectivity..."
	kubectl run -it --rm debug --image=nicolaka/netshoot --restart=Never -n $(NAMESPACE) -- /bin/bash

.PHONY: k8s-test-mcp-tools
k8s-test-mcp-tools:
	@echo "🔧 Testing MCP tool discovery..."
	@echo ""
	@echo "=== PDF Extractor Tools ==="
	curl -s -X POST http://pdf-extractor.ai-interviewer.local/mcp/ \
	  -H "Content-Type: application/json" \
	  -H "Accept: application/json, text/event-stream" \
	  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}' | grep "^data:" | sed 's/^data: //' | jq '.result.tools[] | {name: .name, description: .description}' || echo "❌ PDF extractor MCP tools failed"
	@echo ""
	@echo "=== Interview Agent Tools ==="
	curl -s -X POST http://interview-agent.ai-interviewer.local/mcp/ \
	  -H "Content-Type: application/json" \
	  -H "Accept: application/json, text/event-stream" \
	  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}' | grep "^data:" | sed 's/^data: //' | jq '.result.tools[] | {name: .name, description: .description}' || echo "❌ Interview agent MCP tools failed"
	@echo ""
	@echo "=== LLM Agent Tools ==="
	curl -s -X POST http://llm-agent.ai-interviewer.local/mcp/ \
	  -H "Content-Type: application/json" \
	  -H "Accept: application/json, text/event-stream" \
	  -d '{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}' | grep "^data:" | sed 's/^data: //' | jq '.result.tools[] | {name: .name, description: .description}' || echo "❌ LLM agent MCP tools failed"

.PHONY: k8s-show-ip-access
k8s-show-ip-access:
	@echo "🌐 IP-based Access Information:"
	@echo ""
	@MINIKUBE_IP=$$(minikube ip) || MINIKUBE_IP="<minikube-ip>"; \
	echo "Minikube IP: $$MINIKUBE_IP"; \
	echo ""; \
	echo "🌐 Direct IP Access URLs:"; \
	echo "  Main App:      http://$$MINIKUBE_IP/"; \
	echo "  Registry:      http://$$MINIKUBE_IP/registry"; \
	echo "  Direct API:    http://$$MINIKUBE_IP/direct-api"; \
	echo "  Grafana:       http://$$MINIKUBE_IP/grafana"; \
	echo ""; \
	echo "🔧 Agent Endpoints:"; \
	echo "  PDF Extractor: http://$$MINIKUBE_IP/agents/pdf-extractor"; \
	echo "  Interview:     http://$$MINIKUBE_IP/agents/interview-agent"; \
	echo "  LLM Agent:     http://$$MINIKUBE_IP/agents/llm-agent"; \
	echo "  OpenAI LLM:    http://$$MINIKUBE_IP/agents/openai-llm-agent"; \
	echo ""; \
	echo "💡 Examples:"; \
	echo "  curl http://$$MINIKUBE_IP/"; \
	echo "  curl http://$$MINIKUBE_IP/registry/health"; \
	echo "  curl http://$$MINIKUBE_IP/api/health"