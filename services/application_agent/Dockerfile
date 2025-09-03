# Application Agent Dockerfile - MCP Mesh Agent
# Production-ready containerization for Application Agent

# Use official MCP Mesh Python runtime as base
ARG MCP_MESH_VERSION=0.5.3
FROM mcpmesh/python-runtime:${MCP_MESH_VERSION}

# Set environment variables for the agent
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MCP_MESH_HTTP_PORT=8096

# Install additional system dependencies if needed
USER root
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY --chown=mcp-mesh:mcp-mesh ai-interviewer/services/application_agent/requirements.txt ./

# Install agent-specific dependencies as root
RUN pip install --no-cache-dir -r requirements.txt

# Switch back to non-root user
USER mcp-mesh

# Copy agent application code (will be overridden by volume mount in dev mode)
COPY --chown=mcp-mesh:mcp-mesh ai-interviewer/services/application_agent/ ./application_agent/

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${MCP_MESH_HTTP_PORT:-8096}/health || exit 1

# Expose port
EXPOSE ${MCP_MESH_HTTP_PORT:-8096}

# Run the application
WORKDIR /app
CMD ["-m", "application_agent"]