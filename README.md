# GopherGPT - UMN Research Finder Demo

This repository contains a FastAPI backend and a React frontend. Right now the app already supports:

- chat through the backend `/chat` endpoint
- UMN-focused research through `/research`
- a frontend with page switching for chat, research, and course comparison

## Quickstart

1. Copy `.env.example` to `.env`.
2. Set `OPENAI_KEY` and `TAVILY_API_KEY` if you want live research results.
3. If you do not have keys, you can still run the project. The research endpoint will fall back to a mock response.
4. Start the services:

```powershell
docker compose up --build
```

5. Open `http://localhost:3000`.

## Testing

Run the sample research test script from the host machine:

```powershell
python .\scripts\test_research.py
```

## Notes

- The backend reads `.env`.
- Do not commit real API keys into the repository.
- If you want to run only the backend locally without Docker, create a virtual environment, install dependencies, and run `uvicorn webservice.app:app --reload`.

For full Docker setup and image build instructions, see [DOCKER_README.md](DOCKER_README.md).

## Additional Guides

- [SCHEDULE_BUILDER_README.md](SCHEDULE_BUILDER_README.md) - step-by-step guide for adding the schedule builder feature
