# One service: build React, then serve it alongside the Python API.
FROM node:22-alpine AS frontend-build
WORKDIR /build
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt && useradd --create-home portfolio
COPY backend/app backend/app
COPY content content
COPY --from=frontend-build /build/dist frontend/dist
USER portfolio
EXPOSE 10000
CMD ["python", "-m", "backend.app.serve"]
