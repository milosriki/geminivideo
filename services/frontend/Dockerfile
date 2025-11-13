FROM node:20-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

# Install gettext for envsubst command
RUN apk add --no-cache gettext

# Copy built assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy nginx config template and entrypoint script
COPY nginx.conf.template /etc/nginx/conf.d/default.conf.template
COPY entrypoint.sh /entrypoint.sh

# Make entrypoint executable
RUN chmod +x /entrypoint.sh

# Remove default nginx config
RUN rm -f /etc/nginx/conf.d/default.conf

# Expose port (Cloud Run will set PORT env var)
EXPOSE 8080

# Use entrypoint script to configure and start nginx
ENTRYPOINT ["/entrypoint.sh"]
