FROM node:18-slim as build

WORKDIR /app

# Copy package files
COPY package*.json ./
COPY tsconfig.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build TypeScript
RUN npm run build

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8080

# Start the application
CMD ["npm", "start"]
