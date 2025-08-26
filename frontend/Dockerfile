# Frontend2 Dockerfile - Next.js 15 with hot reload
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Health check endpoint for docker-compose
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
  CMD curl -f http://localhost:3000/api/health || exit 1

# Development command with hot reload
CMD ["npm", "run", "dev"]