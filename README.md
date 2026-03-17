(# GopherGPT — UMN Research Finder demo)

This repository contains a small demo: a FastAPI backend and a React frontend. The backend exposes a `/research` endpoint that searches UMN domains (via TavilySearch) and returns short snippets. When API keys are not provided the endpoint returns a canned mock result so you can test locally.

Quickstart (Docker Compose)

1. Copy `.env.example` to `.env` and set your `OPENAI_KEY` and `TAVILY_API_KEY` if you want live search. If you don't have keys, leave them empty and the backend will return a mock response.

2. Build and start services:

```powershell
docker compose up --build
```

3. Frontend: open http://localhost:3000 and use the top-right "Research" button to open the UMN Research Finder.

4. Test via script (on host):

```powershell
python .\scripts\test_research.py
```

Notes
- The backend reads `.env` (docker-compose loads it into containers). Do not commit real secrets into the repository.
- If you want to run only the backend locally without Docker, create a venv, install the project's dependencies, and run `uvicorn webservice.app:app --reload`.

For full Docker setup and image build instructions, see [DOCKER_README.md](DOCKER_README.md).

