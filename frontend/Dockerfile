# Multi-stage Dockerfile for React Frontend
# Stage 1: Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files and install dependencies
COPY package.json package-lock.json* ./
RUN npm ci --silent || npm install

# Copy source code and build config
COPY . .

# Build production bundle
RUN npm run build

# Stage 2: Production web server stage
FROM nginx:1.25-alpine

# Copy built assets from stage 1
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy Nginx server configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/healthz || exit 1

CMD ["nginx", "-g", "daemon off;"]
