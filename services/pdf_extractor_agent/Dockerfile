# Optimized Dockerfile using official MCP Mesh Python runtime
# Production-ready containerization for PDF Extractor Agent

# Use official MCP Mesh Python runtime as base
ARG MCP_MESH_VERSION=0.5.3
FROM mcpmesh/python-runtime:${MCP_MESH_VERSION}

# Set environment variables for the agent
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    AGENT_NAME=pdf-extractor \
    MCP_MESH_HTTP_PORT=8090 \
    LOG_LEVEL=INFO

# Install additional system dependencies specific to PDF processing
USER root
RUN apt-get update && apt-get install -y \
    # PDF processing libraries
    libmagic1 \
    libmagic-dev \
    # Image processing libraries
    libjpeg62-turbo \
    libpng16-16 \
    libtiff6 \
    # Build tools for Python packages
    gcc \
    g++ \
    pkg-config \
    # Clean up
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY --chown=mcp-mesh:mcp-mesh services/pdf_extractor_agent/requirements.txt ./

# Install agent-specific dependencies as root
RUN pip install --no-cache-dir -r requirements.txt

# Switch back to non-root user
USER mcp-mesh

# Copy agent source code (will be overridden by volume mount in dev mode)
COPY --chown=mcp-mesh:mcp-mesh services/pdf_extractor_agent/ ./pdf_extractor_agent/

# Create directories for PDF processing
RUN mkdir -p temp output logs cache

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:${MCP_MESH_HTTP_PORT:-8090}/health || exit 1

# Expose the agent port
EXPOSE ${MCP_MESH_HTTP_PORT:-8090}

# Set default environment variables for PDF processing
ENV PDF_CACHE_ENABLED=true \
    PDF_TEMP_DIR=/app/temp \
    PDF_OUTPUT_DIR=/app/output \
    METRICS_ENABLED=true

# Start the agent
CMD ["-m", "pdf_extractor_agent"]