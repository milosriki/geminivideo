FROM node:20-alpine

# Install wget for health checks
RUN apk add --no-cache wget

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Install dependencies
RUN npm install --legacy-peer-deps --no-audit --no-fund; exit 0

# Verify TypeScript compiler was installed, retry if missing
RUN test -f node_modules/.bin/tsc || \
    (echo "WARNING: tsc not found after npm install. Retrying..." >&2 && npm install --legacy-peer-deps)

# Copy source code
COPY . .

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
