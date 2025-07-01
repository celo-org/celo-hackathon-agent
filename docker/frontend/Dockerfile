# ===============================
# AI Project Analyzer - Frontend
# Production Docker Image
# ===============================

# Use official Node.js runtime as base image
FROM node:18-alpine AS base

# Set working directory
WORKDIR /app

# ===============================
# Dependencies stage
# ===============================
FROM base AS deps

# Copy package files
COPY packages/frontend/package*.json ./
COPY packages/frontend/pnpm-lock.yaml* ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# ===============================
# Build stage
# ===============================
FROM base AS builder

# Copy package files
COPY packages/frontend/package*.json ./
COPY packages/frontend/pnpm-lock.yaml* ./

# Install all dependencies (including dev)
RUN npm ci

# Copy source code
COPY packages/frontend/ .

# Build the application
RUN npm run build

# ===============================
# Production stage
# ===============================
FROM nginx:alpine AS production

# Copy custom nginx configuration
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built application from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Create non-root user
RUN addgroup -g 1001 -S nodejs &&
  adduser -S nextjs -u 1001

# Set proper permissions
RUN chown -R nextjs:nodejs /usr/share/nginx/html &&
  chown -R nextjs:nodejs /var/cache/nginx &&
  chown -R nextjs:nodejs /var/log/nginx &&
  chown -R nextjs:nodejs /etc/nginx/conf.d

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]

# ===============================
# Development stage
# ===============================
FROM base AS development

# Install development dependencies
COPY packages/frontend/package*.json ./
RUN npm install

# Copy source code
COPY packages/frontend/ .

# Expose port for development
EXPOSE 5173

# Development command with hot reload
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
