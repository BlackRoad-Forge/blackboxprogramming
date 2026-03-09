# ---- Build stage ----
FROM node:25-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev

# ---- Runtime stage ----
FROM node:25-alpine
WORKDIR /app

# Non-root user for security
RUN addgroup -S ollama && adduser -S ollama -G ollama
USER ollama

COPY --from=builder /app/node_modules ./node_modules
COPY package*.json ./
COPY src ./src

ENV NODE_ENV=production \
    PORT=3000 \
    OLLAMA_BASE_URL=http://localhost:11434 \
    OLLAMA_MODEL=llama3

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost:3000/api/health || exit 1

CMD ["node", "src/index.js"]
