# GopherGPT — Demo Ideas & Implementation Plan

This document describes focused demo ideas for University of Minnesota (UMN)‑centric AI use cases, maps the backend tools required, lists endpoints and data shapes, describes error modes, and proposes a recommended minimal MVP to implement first.

---

## Summary (recommended path)

- Recommended MVP: **UMN Research Finder** — search UMN sites and return summarized results with links.
- Why: reuses existing backend tools in this repo (TavilySearch + OpenAI LLM), minimal infra, fast to demo.

---

## Ranked Use Cases

1. UMN Research Finder (Recommended)
2. UMN FAQ / Campus Assistant
3. Campus Events Aggregator & Summarizer
4. Document Upload → Q&A (Document QA)
5. Course Lookup / Recommender
6. Researcher / Lab Finder

Each idea below contains: short description, backend tools required, minimal API design, error modes, and frontend wiring notes.

---

## 1) UMN Research Finder (Recommended)

Description
- Search UMN domains (e.g., `umn.edu`) for papers, pages, or resources on a topic. Return a ranked list with short LLM-generated summaries and direct links.

Backend tools
- TavilySearch (existing in repo)
- OpenAI LLM via `OpenAILLM` (existing wrapper)

Endpoint (FastAPI)
- POST /research
  - Request: `{ "query": "machine learning energy systems", "max_results": 5 }`
  - Response: `{ "query": "...", "results": [{"title":"...","url":"...","snippet":"...","summary":"..."}, ...], "meta": {"total_found": N} }

Flow
- Use `TavilySearch(max_results=N, include_domains=["umn.edu"])` to fetch results.
- For each result, call the LLM to produce a 1–2 sentence summary and optionally a relevance score.

Error modes
- No results → return empty list and a helpful message.
- Search API error → HTTP 502 (or 200 with `error` field) and partial results if available.
- LLM error or rate limit → return raw snippet and `summary: null` with a `warnings` field.

Frontend wiring
- Add a “Research” UI: search input → POST `/research` → render cards with title, summary, link.

Dependencies / env
- `TAVILY_API_KEY`, `OPENAI_KEY` (already used by repo)
- Python packages: `langchain_tavily`, `langchain-openai`, `fastapi`, `uvicorn`

Acceptance criteria
- Returns up to N clickable results with meaningful summaries within a short demo time (a few seconds).

---

## 2) UMN FAQ / Campus Assistant

Description
- Answer common campus questions (admissions, hours, departments) using web search + LLM. Prefer UMN sources and cite URLs.

Backend tools
- TavilySearch, OpenAI LLM
- Optional: a small curated JSON/CSV knowledge base for high-confidence answers.

Endpoint
- POST /faq or reuse POST /chat with a different system prompt
  - Request: `{ "message": "When does fall semester start?" }`
  - Response: `{ "response": "...", "sources": [{"url":"...","snippet":"..."}] }

Notes
- Prompt engineering: instruct the model to cite sources and prefer UMN domains.

---

## 3) Campus Events Aggregator & Summarizer

Description
- Collect upcoming events from department pages or RSS feeds, summarize event descriptions and present a campus calendar view.

Backend tools
- feedparser (or custom scraping), OpenAI for summarization

Endpoint
- GET /events?dept=comp-sci&days=14
  - Response: `{ "events": [{"title":"...","date":"...","location":"...","summary":"...","link":"..."}] }

Notes
````markdown
# GopherGPT — Demo Ideas & Implementation Plan

This document describes focused demo ideas for University of Minnesota (UMN)‑centric AI use cases, maps the backend tools required, lists endpoints and data shapes, describes error modes, and proposes a recommended minimal MVP to implement first.

---

## Summary (recommended path)

- Recommended MVP: **UMN Research Finder** — search UMN sites and return summarized results with links.
- Why: reuses existing backend tools in this repo (TavilySearch + OpenAI LLM), minimal infra, fast to demo.

---

## Ranked Use Cases

1. UMN Research Finder (Recommended)
2. UMN FAQ / Campus Assistant
3. Campus Events Aggregator & Summarizer
4. Document Upload → Q&A (Document QA)
5. Course Lookup / Recommender
6. Researcher / Lab Finder

Each idea below contains: short description, backend tools required, minimal API design, error modes, and frontend wiring notes.

---

## 1) UMN Research Finder (Recommended)

Description
- Search UMN domains (e.g., `umn.edu`) for papers, pages, or resources on a topic. Return a ranked list with short LLM-generated summaries and direct links.

Backend tools
- TavilySearch (existing in repo)
- OpenAI LLM via `OpenAILLM` (existing wrapper)

Endpoint (FastAPI)
- POST /research
  - Request: `{ "query": "machine learning energy systems", "max_results": 5 }`
  - Response: `{ "query": "...", "results": [{"title":"...","url":"...","snippet":"...","summary":"..."}, ...], "meta": {"total_found": N} }

Flow
- Use `TavilySearch(max_results=N, include_domains=["umn.edu"])` to fetch results.
- For each result, call the LLM to produce a 1–2 sentence summary and optionally a relevance score.

Error modes
- No results → return empty list and a helpful message.
- Search API error → HTTP 502 (or 200 with `error` field) and partial results if available.
- LLM error or rate limit → return raw snippet and `summary: null` with a `warnings` field.

Frontend wiring
- Add a “Research” UI: search input → POST `/research` → render cards with title, summary, link.

Dependencies / env
- `TAVILY_API_KEY`, `OPENAI_KEY` (already used by repo)
- Python packages: `langchain_tavily`, `langchain-openai`, `fastapi`, `uvicorn`

Acceptance criteria
- Returns up to N clickable results with meaningful summaries within a short demo time (a few seconds).

---

## 2) UMN FAQ / Campus Assistant

Description
- Answer common campus questions (admissions, hours, departments) using web search + LLM. Prefer UMN sources and cite URLs.

Backend tools
- TavilySearch, OpenAI LLM
- Optional: a small curated JSON/CSV knowledge base for high-confidence answers.

Endpoint
- POST /faq or reuse POST /chat with a different system prompt
  - Request: `{ "message": "When does fall semester start?" }`
  - Response: `{ "response": "...", "sources": [{"url":"...","snippet":"..."}] }

Notes
- Prompt engineering: instruct the model to cite sources and prefer UMN domains.

---

## 3) Campus Events Aggregator & Summarizer

Description
- Collect upcoming events from department pages or RSS feeds, summarize event descriptions and present a campus calendar view.

Backend tools
- feedparser (or custom scraping), OpenAI for summarization

Endpoint
- GET /events?dept=comp-sci&days=14
  - Response: `{ "events": [{"title":"...","date":"...","location":"...","summary":"...","link":"..."}] }

Notes
- Maintain a JSON mapping of department → feed URL for quick demos.

---

## 4) Document Upload → Q&A (Document QA)

Description
- Upload a PDF (e.g., syllabus), index it with embeddings and allow question answering over the document.

Backend tools
- LangChain loaders (PyPDFLoader), embeddings (OpenAI embeddings or local), simple vector store (Chroma/FAISS)

Endpoints
- POST /upload (multipart) → returns doc_id
- POST /doc_qa { "doc_id":"...","question":"..." } → `{ "answer":"...","sources":[...] }`

Notes
- Higher implementation cost; useful for powerful demos but needs embedding infra.

---

## 5) Course Lookup / Recommender

Description
- Query a static course catalog (CSV/JSON) or recommend courses given student interests.

Backend tools
- Simple CSV/JSON search; optionally LLM for generating friendly course descriptions

Endpoint
- GET /courses?query=data+science
  - Response: list of matched courses

Notes
- Quick to implement; good for demonstrating structured-data retrieval and lightweight LLM augmentation.

---

## 6) Researcher / Lab Finder

Description
- Given a research topic, find UMN faculty/labs working in that area and return concise bios and contact links.

Backend tools
- Domain search (Tavily), LLM summarization, optional curated directory

Endpoint
- POST /find_researchers { "topic":"natural language processing" }

---

# Implementation Recommendation (MVP)

- Implement the **UMN Research Finder** first.
- Minimal file changes:
  - New router: `webservice/routers/research.py` (FastAPI router with `/research`).
  - Minor helper (optional): `autonomy/tools/tavily_tool.py` to wrap TavilySearch calls.
  - Frontend: add a simple search component/page in `frontend/src` that calls `/research` and displays results.

## Example: POST /research (pseudo-code flow)

1. Receive request `{query, max_results}`.
2. Call TavilySearch with include_domains=["umn.edu"].
3. For each result (title,url,snippet): call LLM with prompt `Summarize this snippet in 1-2 sentences and produce a relevance score`.
4. Return aggregated results.

## Example curl

```bash
curl -X POST http://localhost:8000/research \
  -H 'Content-Type: application/json' \
  -d '{"query":"climate modeling umn","max_results":5}'
```

## Next steps / Offer

- I can implement the Research Finder backend route and a minimal frontend UI for you. That will include:
  - `webservice/routers/research.py` (FastAPI router)
  - A small frontend page (`frontend/src/Research.js`) and a link or button added to `App.js`
  - Test instructions and a simple integration test (curl) and a demo script.

- Or, if you want a different demo from the list, tell me which one and I’ll prepare a minimal implementation plan or code.

---

If you'd like, I can commit the Research Finder backend and frontend changes now. Which option do you want me to implement? (Research Finder is the fastest.)

---

## Additional simple features (quick wins)

Below are small, high-value features that are quick to add and not limited to UMN content. Each entry includes a brief description, suggested backend tool, minimal endpoint, and estimated effort.

1) Smart paraphrase / grammar fix
   - Description: Rewrites user text for clarity or tone.
   - Backend: OpenAI LLM.
   - Endpoint: POST /paraphrase { text, tone? } -> { original, paraphrase }
   - Effort: Very small.

2) Keyword extractor / tagger
   - Description: Extracts keywords/tags from text.
   - Backend: LLM or lightweight NLP (RAKE/spaCy).
   - Endpoint: POST /keywords { text } -> { keywords: [] }
   - Effort: Very small.

3) Short text summarizer
   - Description: Summarizes a message or article into 1 sentence.
   - Backend: LLM.
   - Endpoint: POST /summarize { text, max_sentences } -> { summary }
   - Effort: Very small.

4) URL / page summarizer
   - Description: Fetches a URL server-side, extracts main content, and summarizes.
   - Backend: server-side fetch + html parsing + LLM.
   - Endpoint: POST /summarize_url { url } -> { title, summary, top_points: [] }
   - Effort: Small.

5) Browser bookmarklet / Share to Chat
   - Description: Bookmarklet that sends current page to the app and opens chat with a summary.
   - Backend: reuse /summarize_url.
   - Effort: Small.

6) Sentiment analysis / tone detection
   - Description: Labels messages positive/neutral/negative.
   - Backend: LLM or lightweight library.
   - Endpoint: POST /sentiment { text } -> { label, score }
   - Effort: Very small.

7) Meeting minutes summarizer
   - Description: Summarize transcripts into minutes and extract action items.
   - Backend: LLM with an action-item extraction prompt.
   - Endpoint: POST /minutes { transcript } -> { summary, actions: [] }
   - Effort: Small.

8) Code snippet runner (sandboxed)
   - Description: Run a small code snippet (Python) and return output/errors.
   - Backend: Dockerized runner or sandboxed subprocess (careful with security).
   - Endpoint: POST /run_code { language, code } -> { stdout, stderr, exit_code }
   - Effort: Small–Medium (security required).

9) Quick Q&A with curated knowledge (local file)
   - Description: Upload a small JSON/CSV of FAQs, then ask questions retrieving exact answers.
   - Backend: simple search or lightweight vector index.
   - Endpoint: POST /qa { question } -> { answer, source }
   - Effort: Small.

10) Translate messages
   - Description: Translate a message to a target language.
   - Backend: LLM or translation API.
   - Endpoint: POST /translate { text, to } -> { translated_text }
   - Effort: Small.

11) Citation generator for answers
   - Description: For generated answers, produce human-friendly citations from source URLs.
   - Backend: LLM + source extraction.
   - Endpoint: POST /cite { question, urls } -> { answer, citations: [] }
   - Effort: Small.

12) Email / draft generator
   - Description: Generate email drafts from a short brief and desired tone.
   - Backend: LLM.
   - Endpoint: POST /draft_email { purpose, tone } -> { subject, body }
   - Effort: Very small.

Mapping to repo
- Use `OpenAILLM` for all LLM-based tasks.
- Use `TavilySearch` for web/domain search related features.
- Add new FastAPI routers under `webservice/routers/` for each feature.
- Frontend: add UI buttons or a small toolbar to call new endpoints.

Security notes
- Sandboxing is required for code execution features.
- Keep API keys in `.env` and do not expose them to the client.
- Watch token usage and implement caching where appropriate.

Which of these would you like me to implement next? I can generate the backend router and a small frontend UI for any 1–2 of them quickly.

````
