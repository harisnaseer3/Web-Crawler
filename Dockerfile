# Multi-stage build for Web Crawler Search Engine

# Backend stage
FROM python:3.9-slim as backend

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/
COPY schema.sql .
COPY start_backend.py .

# Frontend build stage
FROM node:16-alpine as frontend

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy frontend source and build
COPY frontend/ .
RUN npm run build

# Production stage
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from backend stage
COPY --from=backend /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=backend /usr/local/bin /usr/local/bin

# Copy application code
COPY --from=backend /app/backend ./backend
COPY --from=backend /app/schema.sql .
COPY --from=backend /app/start_backend.py .

# Copy built frontend
COPY --from=frontend /app/frontend/build ./frontend/build

# Configure nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Create startup script
RUN echo '#!/bin/bash\n\
# Start backend in background\n\
python start_backend.py &\n\
\n\
# Start nginx in foreground\n\
nginx -g "daemon off;"' > /app/start.sh && chmod +x /app/start.sh

EXPOSE 80

CMD ["/app/start.sh"]
