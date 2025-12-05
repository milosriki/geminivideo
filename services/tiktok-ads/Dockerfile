# TikTok Ads Publisher Service - Dockerfile
FROM node:18-alpine

# Install wget for health checks
RUN apk add --no-cache wget

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY src ./src

# Build TypeScript
RUN npm run build

# Expose port
EXPOSE 8085

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:${PORT:-8085}/health || exit 1

# Start service
CMD ["npm", "start"]
