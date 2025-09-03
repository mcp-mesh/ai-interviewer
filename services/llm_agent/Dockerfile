# Optimized Dockerfile using official MCP Mesh Python runtime
# Production-ready containerization for LLM Agent

# Use official MCP Mesh Python runtime as base
ARG MCP_MESH_VERSION=0.5.3
FROM mcpmesh/python-runtime:${MCP_MESH_VERSION}

# Set environment variables for the agent
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    AGENT_NAME=llm-claude-agent \
    MCP_MESH_HTTP_PORT=8090 \
    LOG_LEVEL=INFO

# Install additional system dependencies if needed
USER root
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY --chown=mcp-mesh:mcp-mesh services/llm_agent/requirements.txt ./

# Install agent-specific dependencies as root
RUN pip install --no-cache-dir -r requirements.txt

# Switch back to non-root user
USER mcp-mesh

# Copy agent source code (will be overridden by volume mount in dev mode)
COPY --chown=mcp-mesh:mcp-mesh services/llm_agent/ ./llm_agent/

# Create directories for agent
RUN mkdir -p logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:${MCP_MESH_HTTP_PORT:-8090}/health || exit 1

# Expose the agent port
EXPOSE ${MCP_MESH_HTTP_PORT:-8090}

# Start the agent
CMD ["-m", "llm_agent"]