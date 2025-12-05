FROM node:20-alpine

# Install wget for health checks
RUN apk add --no-cache wget

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./
COPY prisma ./prisma

# Install dependencies
RUN npm install --legacy-peer-deps --no-audit --no-fund

# Copy source code
COPY src ./src
COPY shared /shared

# Build TypeScript
RUN npm run build

# Remove dev dependencies
RUN npm prune --production || true

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:${PORT:-8080}/health || exit 1

# Start the application
CMD ["npm", "start"]
