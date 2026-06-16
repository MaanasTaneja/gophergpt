# GopherGPT

An AI assistant for University of Minnesota students. Ask it about courses, professors, grade distributions, study spaces, or what's on campus, and it pulls real data from GopherGrades, UMN's room booking system, and the broader web before answering.

Built on a ReAct agent (LangGraph + OpenAI) with a FastAPI backend and a React frontend.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.118-009688.svg)
![React](https://img.shields.io/badge/React-18-61dafb.svg)
![Docker](https://img.shields.io/badge/Docker-ready-2496ed.svg)

## What it does

- **Course & professor lookup.** Pulls grade distributions, SRT ratings, and recommended-by rates from GopherGrades (`umn.lol`). Supports comparing two professors or two sections side by side.
- **Department Explorer.** Browse a full department's courses with grade charts and ratings in one view.
- **Study space finder.** Suggests buildings by category (quiet, group, late-night, tech, St. Paul) with Google Maps and campus map links, plus direct LibCal reservation links where available.
- **UMN Research Finder.** Domain-restricted search across `umn.edu` with LLM-generated summaries for each result.
- **Chat with memory.** Conversations persist across sessions. You can save, reload, and clear history.
- **Personalization.** Profile-aware responses — major, year, and completed coursework feed into the system prompt so recommendations skip prereqs you've already taken.

## Architecture

```
┌─────────────────┐         ┌──────────────────────┐
│  React frontend │ ──HTTP─▶│  FastAPI backend     │
│  (port 3000)    │         │  (port 8000)         │
└─────────────────┘         └──────────┬───────────┘
                                       │
                            ┌──────────▼───────────┐
                            │   ReAct Agent        │
                            │   (LangGraph)        │
                            └──────────┬───────────┘
                                       │
              ┌────────────────┬───────┼────────────┬─────────────────┐
              ▼                ▼       ▼            ▼                 ▼
         GopherGrades    UMN Rooms   Tavily    OpenAI LLM      Conversation
         (umn.lol API)   booking     search    (gpt-4o-mini)   + profile JSON
```

The agent decides which tool to call based on the user's message. Tool outputs feed back into the LLM until it produces a final answer.

### Backend tools

| Tool | Purpose |
|------|---------|
| `gophergrades_search` | Free-text search across courses, profs, and departments |
| `gophergrades_class` | Full data for one course — grade dist, SRT, instructors |
| `gophergrades_prof` | Full profile for one professor |
| `gophergrades_dept` | Department-wide breakdown |
| `umn_room_booking` | Room/study-space lookup with directions |
| `tavily_search` | General web search for anything else |

## Stack

- **Backend:** FastAPI, LangChain, LangGraph, OpenAI (gpt-4o-mini by default), Tavily, Poetry
- **Frontend:** React 18, Recharts (grade distribution charts), Tailwind CSS, Lucide icons
- **Infra:** Docker Compose, JSON file persistence for conversations and profiles

## Quickstart

### With Docker (recommended)

```bash
cp .env.example .env
# add your OPENAI_KEY and TAVILY_API_KEY to .env

docker compose up --build
```

Frontend at [http://localhost:3000](http://localhost:3000), backend at [http://localhost:8000](http://localhost:8000).

The research endpoint falls back to a mock response if `TAVILY_API_KEY` is missing, so you can run a partial demo without it.

### Without Docker

Backend:

```bash
poetry install
poetry run uvicorn webservice.app:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm start
```

## API

All endpoints accept and return JSON.

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/` | Health check |
| `POST` | `/chat` | Main chat endpoint. Body: `{ message, conversation_id?, user_id? }` |
| `POST` | `/research` | UMN-scoped research. Body: `{ query, max_results }` |
| `POST` | `/umn/course` | Course lookup by code or name |
| `POST` | `/umn/prof` | Professor lookup |
| `POST` | `/umn/dept` | Department breakdown |
| `GET`  | `/profile?user_id=...` | Get a user profile |
| `PUT`  | `/profile` | Update a user profile |
| `GET`  | `/history` | List saved conversations |
| `POST` | `/save` | Save a conversation |
| `DELETE` | `/history/clear` | Clear all history |

Example:

```bash
curl -X POST http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message": "Compare CSCI 1933 sections"}'
```

```bash
curl -X POST http://localhost:8000/research \
  -H 'Content-Type: application/json' \
  -d '{"query": "machine learning energy systems", "max_results": 5}'
```

## Environment

Required:

- `OPENAI_KEY` — for the LLM
- `TAVILY_API_KEY` — for the research endpoint and general web search

Optional:

- `GOPHERGRADES_API_BASE` — defaults to `https://umn.lol/api`, override for local dev

## Project layout

```
gophergpt/
├── autonomy/              # agent + tools
│   ├── agent/             # base, ReAct, planning-exec, simple agents
│   ├── llm/               # OpenAI wrapper
│   ├── tools/             # GopherGrades, UMN rooms, search
│   └── prompts.py
├── webservice/            # FastAPI app
│   ├── app.py             # endpoints + ChatAgent
│   ├── routers/           # /research router
│   ├── personalization.py # profile → prompt
│   ├── profile_store.py   # JSON-backed profile store
│   └── data/              # conversations.json, profiles.json
├── frontend/              # React app
│   ├── src/pages/         # ChatPage, DepartmentExplorer, Research, ProfileSettings, CourseCompare
│   └── src/components/    # ChatWindow, Sidebar, GradeChart, etc.
├── scripts/
│   └── test_research.py
├── docker-compose.yml
└── pyproject.toml
```

## Testing

```bash
python scripts/test_research.py
```

## Contributors

Built collaboratively. Branch contributors include Ahshaam, Adil, Jamie, Nick, Akihito, and Jesse.

## License

No license file included yet. Contact the contributors before reuse.