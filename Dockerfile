# Stage 1: Build frontend assets
FROM node:18 AS frontend-build
WORKDIR /app
COPY src/frontend ./src/frontend
RUN cd src/frontend && npm install && npm run build

# Stage 2: Build backend and assemble final image
FROM python:3.10-slim AS backend
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src ./src
COPY scripts ./scripts
COPY data ./data
COPY docs ./docs

# Copy built frontend from previous stage
COPY --from=frontend-build /app/src/frontend/dist ./src/frontend/dist

# Default environment variables
ENV PYTHONUNBUFFERED=1
ENV UVICORN_PORT=8000

EXPOSE 8000

CMD ["uvicorn", "src.backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
