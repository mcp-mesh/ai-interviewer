# Multi-stage build for OpenAI LLM Agent
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    pkg-config \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy local MCP Mesh source (with unified proxy changes)
COPY src/runtime/python/ ./mcp_mesh_local/

# Install local MCP Mesh first
RUN cd mcp_mesh_local && pip install --no-cache-dir -e .

# Copy project files
COPY ai-interviewer/services/openai_llm_agent/pyproject.toml.local pyproject.toml
COPY ai-interviewer/services/openai_llm_agent/README.md ./
COPY ai-interviewer/services/openai_llm_agent/__init__.py ai-interviewer/services/openai_llm_agent/__main__.py ai-interviewer/services/openai_llm_agent/main.py ./openai_llm_agent/

# Build wheel
RUN pip install --no-cache-dir build && \
    python -m build --wheel

# Runtime stage
FROM python:3.11-slim as runtime

# Create non-root user
RUN groupadd -r openaillmagent && useradd -r -g openaillmagent openaillmagent

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy local MCP Mesh source from builder and install in runtime
COPY --from=builder /build/mcp_mesh_local/ /tmp/mcp_mesh_local/
RUN cd /tmp/mcp_mesh_local && pip install --no-cache-dir . && \
    rm -rf /tmp/mcp_mesh_local

# Copy and install wheel from builder
COPY --from=builder /build/dist/*.whl /tmp/

# Install the application and its dependencies
RUN pip install --no-cache-dir /tmp/*.whl && \
    rm -rf /tmp/*.whl

# Create directories and set permissions
RUN mkdir -p /app/logs && \
    chown -R openaillmagent:openaillmagent /app

# Switch to non-root user
USER openaillmagent

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8090/health || exit 1

# Expose port
EXPOSE 8090

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Start the agent - MCP Mesh handles everything with auto_run=True
CMD ["python", "-m", "openai_llm_agent"]