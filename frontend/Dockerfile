# ──────────────────────────────────────────────────────────────────────────────
# ServerDeals Frontend — Multi-stage Dockerfile
# ──────────────────────────────────────────────────────────────────────────────
#  Stage 1: Builder  — npm ci + npm run build (Vite → dist/)
#  Stage 2: Runtime  — nginx:alpine serving static files + proxying /api
# ──────────────────────────────────────────────────────────────────────────────

# ── Stage 1: Build ───────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies first (layer caching)
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy source and build
# Empty VITE_API_URL → use relative /api/ paths (proxied by nginx)
COPY frontend/ ./
ARG VITE_API_URL=
RUN npm run build

# ── Stage 2: Serve ───────────────────────────────────────────────────────────
FROM nginx:alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy our nginx config
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
