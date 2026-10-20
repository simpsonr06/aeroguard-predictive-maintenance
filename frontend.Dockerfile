# ==============================================================================
# AeroGuard 2.0 / 2.1 — Nuxt 4 Frontend Application
# Multi-stage optimized production container
# ==============================================================================

# Stage 1: Build production bundle
FROM node:20-slim AS builder

WORKDIR /app

# Enable Corepack for pnpm/bun compatibility
RUN corepack enable

COPY frontend/package.json frontend/pnpm-lock.yaml* frontend/bun.lock* ./

# Install dependencies
RUN pnpm install --frozen-lockfile || npm install

# Copy frontend source files
COPY frontend/ .

# Build production bundle with Nitro server
ENV NODE_ENV=production
RUN npm run build

# Stage 2: Minimal Production Runtime
FROM node:20-slim AS runner

WORKDIR /app

ENV NODE_ENV=production \
    PORT=3000 \
    HOST=0.0.0.0

# Install curl for container health check
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root system user
RUN useradd -m -u 1001 nuxtuser

# Copy standalone output from builder stage
COPY --from=builder --chown=nuxtuser:nuxtuser /app/.output ./.output

USER nuxtuser

EXPOSE 3000

HEALTHCHECK --interval=15s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

CMD ["node", ".output/server/index.mjs"]
