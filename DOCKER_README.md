# Docker Setup and Build Guide

This guide explains how to install Docker, build this project’s Docker images, and run the app.

## Prerequisites

- Windows 10/11 with virtualization enabled
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- Internet access for pulling base images and installing dependencies

## 1) Install and verify Docker

1. Install Docker Desktop.
2. Start Docker Desktop and wait until it shows Docker is running.
3. Verify in PowerShell:

```powershell
docker --version
docker compose version
```

If both commands print versions, Docker is ready.

## 2) Configure environment variables

From the project root, create `.env` (if it does not exist):

```powershell
Copy-Item .env.example .env
```

Then update your `.env` values:

- `OPENAI_KEY`
- `TAVILY_API_KEY`

If these keys are empty, backend research falls back to mock output.

## 3) Build and run with Docker Compose (recommended)

From project root:

```powershell
docker compose up --build
```

Services:

- Frontend: http://localhost:3000
- Backend: http://localhost:8000

Run in detached mode:

```powershell
docker compose up --build -d
```

Stop services:

```powershell
docker compose down
```

View logs:

```powershell
docker compose logs -f
```

## 4) Build Dockerfiles manually (without Compose)

### Backend image

From project root:

```powershell
docker build -f webservice/backend.dockerfile -t gophergpt-backend .
```

Run backend container:

```powershell
docker run --rm -p 8000:8000 --env-file .env --name gophergpt-backend gophergpt-backend
```

### Frontend image

From project root:

```powershell
docker build -f frontend/frontend.dockerfile -t gophergpt-frontend ./frontend
```

Run frontend container:

```powershell
docker run --rm -p 3000:3000 --name gophergpt-frontend gophergpt-frontend
```

## 5) Rebuild from scratch (no cache)

```powershell
docker compose build --no-cache
docker compose up -d
```

## Troubleshooting

- **Port already in use**: stop conflicting services or change host ports in `docker-compose.yml`.
- **Docker Desktop not running**: open Docker Desktop and wait for engine startup.
- **Backend build fails at dependency install**: ensure project files like `pyproject.toml` (and lock file if used) are present in the root.
- **Frontend cannot reach backend**: confirm backend is healthy and listening on `8000`.
