#!/bin/sh
set -e

# Use PORT environment variable from Cloud Run (defaults to 8080)
export PORT="${PORT:-8080}"

echo "Starting nginx on port ${PORT}"

# Substitute environment variables in nginx config template
envsubst '${PORT}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

# Remove the template file
rm -f /etc/nginx/conf.d/default.conf.template

# Start nginx
exec nginx -g "daemon off;"
