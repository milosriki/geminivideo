FROM node:18-slim as build

WORKDIR /app

# Copy package files
COPY services/gateway-api/package*.json ./
COPY services/gateway-api/tsconfig.json ./

# Install dependencies
RUN npm install

# Copy shared config directory
COPY shared/config /app/config

# Copy source code
COPY services/gateway-api .

# Build TypeScript
RUN npm run build

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8080

# Start the application
CMD ["npm", "start"]
