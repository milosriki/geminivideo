FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Install dependencies
# The "Exit handler never called" error from npm is benign in Docker builds
# See: https://github.com/npm/cli/issues/4028
RUN npm install --legacy-peer-deps --no-audit --no-fund; exit 0
RUN test -f node_modules/.bin/tsc || npm install --legacy-peer-deps

# Copy source code
COPY src ./src

# Build TypeScript
RUN npm run build

# Remove dev dependencies
RUN npm prune --production || true

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8080

# Start the application
CMD ["npm", "start"]
