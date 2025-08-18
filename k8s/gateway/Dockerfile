# AI Interviewer Nginx Gateway with Next.js UI
# Combines Nginx reverse proxy with static UI assets

FROM openresty/openresty:1.21.4.1-alpine

# Install basic tools for debugging
RUN apk add --no-cache curl

# Copy built Next.js UI from frontend/out to nginx html directory
COPY ai-interviewer/frontend/out /usr/local/openresty/nginx/html

# Copy full Nginx configuration with OAuth and Lua scripts (adapted for K8s)
COPY ai-interviewer/k8s/gateway/nginx-k8s.conf /usr/local/openresty/nginx/conf/nginx.conf
COPY ai-interviewer/k8s/gateway/lua /etc/nginx/lua

# Copy SSL certificates for HTTPS
COPY ai-interviewer/nginx/ssl/server.crt /etc/ssl/certs/server.crt
COPY ai-interviewer/nginx/ssl/server.key /etc/ssl/private/server.key

# Create required directories with proper permissions
RUN mkdir -p /usr/local/openresty/nginx/logs \
    && mkdir -p /tmp/nginx \
    && mkdir -p /tmp/nginx/client_body_temp \
    && mkdir -p /tmp/nginx/proxy_temp \
    && mkdir -p /tmp/nginx/fastcgi_temp \
    && mkdir -p /tmp/nginx/uwsgi_temp \
    && mkdir -p /tmp/nginx/scgi_temp

# Set proper permissions for all directories and SSL files
RUN chown -R nobody:nobody /usr/local/openresty/nginx/html \
    && chown -R nobody:nobody /usr/local/openresty/nginx/logs \
    && chown -R nobody:nobody /tmp/nginx \
    && chown nobody:nobody /etc/ssl/certs/server.crt \
    && chown nobody:nobody /etc/ssl/private/server.key \
    && chmod -R 755 /usr/local/openresty/nginx/html \
    && chmod -R 755 /tmp/nginx \
    && chmod 644 /etc/ssl/certs/server.crt \
    && chmod 600 /etc/ssl/private/server.key

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:9080/health || exit 1

# Expose HTTP and HTTPS ports
EXPOSE 9080 9443

# Use nobody user for security
USER nobody

# Start OpenResty
CMD ["/usr/local/openresty/bin/openresty", "-g", "daemon off;"]