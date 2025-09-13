# Multi-stage Dockerfile for DreamSeed Portal V2

# Stage 1: Build shared packages
FROM node:20-alpine AS shared-builder
WORKDIR /app
COPY package*.json ./
COPY packages/ packages/
RUN npm ci --only=production
RUN npm run build --workspaces --if-present

# Stage 2: Build frontend apps
FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY package*.json ./
COPY --from=shared-builder /app/packages/ packages/
COPY apps/ apps/
RUN npm ci
RUN npm run build --workspace=@dreamseed/portal-app
RUN npm run build --workspace=@dreamseed/learner-app

# Stage 3: Python backend services
FROM python:3.12-slim AS backend-base
WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn

# Stage 4: Career API
FROM backend-base AS career-api
COPY services/career-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/career-api/ .
EXPOSE 8001
CMD ["python", "app/main.py"]

# Stage 5: Learning API  
FROM backend-base AS learning-api
COPY services/learning-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/learning-api/ .
EXPOSE 8002
CMD ["python", "app/main.py"]

# Stage 6: Progress API
FROM backend-base AS progress-api
COPY services/progress-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/progress-api/ .
EXPOSE 8003
CMD ["python", "app/main.py"]

# Stage 7: AI Orchestrator
FROM backend-base AS ai-orchestrator
COPY services/ai-orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY services/ai-orchestrator/ .
EXPOSE 8000
CMD ["python", "app/main.py"]

# Stage 8: Nginx for serving frontend apps
FROM nginx:alpine AS frontend
COPY --from=frontend-builder /app/apps/portal-app/dist /usr/share/nginx/html/portal
COPY --from=frontend-builder /app/apps/learner-app/dist /usr/share/nginx/html/learner
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]