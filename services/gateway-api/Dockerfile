FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Install dependencies
# The "Exit handler never called" error from npm is benign in Docker builds
# See: https://github.com/npm/cli/issues/4028
# The '; exit 0' forces the RUN command to succeed even when npm returns a non-zero exit code.
# This is necessary because npm fails with the error above but packages install correctly.
RUN npm install --legacy-peer-deps --no-audit --no-fund; exit 0

# Verify TypeScript compiler was installed, retry if missing
RUN test -f node_modules/.bin/tsc || \
    (echo "WARNING: tsc not found after npm install. Retrying..." >&2 && npm install --legacy-peer-deps)

# Copy source code
COPY src ./src
COPY shared /shared

# Build TypeScript
RUN npm run build

# Remove dev dependencies
RUN npm prune --production || true

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8080

# Start the application
CMD ["npm", "start"]
