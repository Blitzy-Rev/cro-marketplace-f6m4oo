# Stage 1: Build the React application
FROM node:16-alpine AS builder
WORKDIR /app

# Copy package files for dependency installation
COPY package*.json ./
RUN npm ci

# Copy all source files
COPY . .

# Set environment to production for optimized build
ENV NODE_ENV=production

# Build the application
RUN npm run build

# Stage 2: Serve the application with Nginx
FROM nginx:alpine

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Configure Nginx for SPA routing
RUN echo 'server {\
    listen 80;\
    location / {\
        root /usr/share/nginx/html;\
        index index.html index.htm;\
        try_files $uri $uri/ /index.html;\
    }\
}' > /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Add health check
HEALTHCHECK --interval=30s --timeout=3s CMD wget -q -O - http://localhost/ || exit 1

# Start Nginx in foreground mode
CMD ["nginx", "-g", "daemon off;"]