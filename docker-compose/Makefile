# AI Interviewer Makefile
# Simplified commands for development and deployment

# Default environment
ENV ?= prod

# Docker Compose configurations
COMPOSE_FILE := docker-compose.yml
ifeq ($(ENV),local)
	COMPOSE_FILE := docker-compose.yml -f docker-compose.local.yml
endif

.PHONY: help
help:
	@echo "AI Interviewer - MCP Mesh Based Interview System"
	@echo ""
	@echo "🏗️  BUILD MODES:"
	@echo "  make build              - Build base images (required once)"
	@echo "  make build-local        - Build with local MCP Mesh source (required once for local mode)"
	@echo ""
	@echo "🚀 DEVELOPMENT MODES:"
	@echo "  make dev                - DEV MODE: Released MCP Mesh + Local AI code (instant reload)"
	@echo "  make local              - LOCAL MODE: Local MCP Mesh + Local AI code (instant reload)"
	@echo ""
	@echo "🔧 OPERATIONS:"
	@echo "  make down               - Stop all services"
	@echo "  make restart-dev        - Restart in dev mode"
	@echo "  make restart-local      - Restart in local mode"
	@echo "  make logs               - Show logs from all services"
	@echo "  make logs-api           - Show logs from FastAPI backend"
	@echo "  make logs-pdf           - Show logs from PDF extractor"
	@echo "  make logs-grafana       - Show logs from Grafana"
	@echo "  make logs-tempo         - Show logs from Tempo"
	@echo "  make clean              - Remove all containers and volumes"
	@echo "  make test               - Run basic functionality tests"
	@echo ""
	@echo "📊 OBSERVABILITY:"
	@echo "  Grafana Dashboard: http://localhost:3000 (admin/admin)"
	@echo "  Tempo Tracing: http://localhost:3200"
	@echo "  Redis Traces: make redis-traces"
	@echo ""
	@echo "💡 DEFINITIONS:"
	@echo "  DEV MODE    = MCP Mesh (released images) + AI-Interviewer (local source + volume mounts)"
	@echo "  LOCAL MODE  = MCP Mesh (local source) + AI-Interviewer (local source + volume mounts)"
	@echo "  Volume mounts = Instant code changes without rebuilds!"

.PHONY: build
build: ensure-symlink
	@echo "🔨 Building AI Interviewer with official MCP Mesh runtime..."
	docker compose build

.PHONY: build-local
build-local: ensure-symlink
	@echo "🔨 Building AI Interviewer with local MCP Mesh source..."
	docker compose -f docker-compose.yml -f docker-compose.local.yml build

.PHONY: dev
dev: ensure-symlink ensure-ssl
	@echo "🚀 Starting AI Interviewer (DEV MODE: Released MCP Mesh + Local AI code)..."
	@echo "💡 Volume mounts enabled - code changes are instant!"
	docker compose up -d

.PHONY: local
local: ensure-symlink ensure-ssl
	@echo "🚀 Starting AI Interviewer (LOCAL MODE: Local MCP Mesh + Local AI code)..."
	@echo "💡 Volume mounts enabled - code changes are instant!"
	docker compose -f docker-compose.yml -f docker-compose.local.yml up -d

.PHONY: down
down:
	@echo "⏹️ Stopping AI Interviewer..."
	docker compose -f docker-compose.yml -f docker-compose.local.yml down

.PHONY: logs
logs:
	docker compose -f $(COMPOSE_FILE) logs -f

.PHONY: logs-api
logs-api:
	docker compose -f $(COMPOSE_FILE) logs -f fastapi

.PHONY: logs-pdf
logs-pdf:
	docker compose -f $(COMPOSE_FILE) logs -f pdf-extractor

.PHONY: logs-grafana
logs-grafana:
	docker compose -f $(COMPOSE_FILE) logs -f grafana

.PHONY: logs-tempo
logs-tempo:
	docker compose -f $(COMPOSE_FILE) logs -f tempo

.PHONY: restart-dev
restart-dev: down
	@sleep 2
	$(MAKE) dev

.PHONY: restart-local
restart-local: down
	@sleep 2
	$(MAKE) local

.PHONY: clean
clean:
	@echo "🧹 Cleaning up AI Interviewer containers and volumes..."
	docker compose -f docker-compose.yml -f docker-compose.local.yml down -v --remove-orphans
	docker system prune -f
	@echo "✅ Cleanup complete"

.PHONY: test
test:
	@echo "🧪 Running basic functionality tests..."
	@./test_simple_curl.sh || echo "Test script not found - create test_simple_curl.sh for basic tests"

# Development helpers
.PHONY: shell-api
shell-api:
	docker compose -f $(COMPOSE_FILE) exec fastapi bash

.PHONY: shell-pdf
shell-pdf:
	docker compose -f $(COMPOSE_FILE) exec pdf-extractor bash

.PHONY: status
status:
	@echo "📊 AI Interviewer Service Status:"
	docker compose -f $(COMPOSE_FILE) ps

.PHONY: redis-traces
redis-traces:
	@echo "📈 Latest Redis trace entries:"
	docker exec ai-interviewer-redis redis-cli xread count 10 streams "mesh:trace" 0-0

# Internal helper to ensure symlink exists for Docker builds
.PHONY: ensure-symlink
ensure-symlink:
	@if [ ! -L "../ai-interviewer" ]; then \
		echo "🔗 Creating ai-interviewer symlink for Docker builds..."; \
		cd .. && ln -sf . ai-interviewer; \
	fi

# Internal helper to ensure SSL certificates exist for nginx
.PHONY: ensure-ssl
ensure-ssl:
	@if [ ! -f "../nginx/ssl/server.crt" ] || [ ! -f "../nginx/ssl/server.key" ]; then \
		echo "🔒 Creating self-signed SSL certificates for local development..."; \
		mkdir -p ../nginx/ssl; \
		openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
			-keyout ../nginx/ssl/server.key \
			-out ../nginx/ssl/server.crt \
			-subj "/C=US/ST=CA/L=Local/O=AI-Interviewer/CN=localhost"; \
		echo "✅ SSL certificates created in nginx/ssl/"; \
	fi