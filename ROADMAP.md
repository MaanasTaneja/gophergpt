# GopherGPT Roadmap

Status as of 2026-08-15, cross-checked against `evals/golden_set.json`,
`evals/results/` (latest judged run: `run_20260813_212129_judged.json`), and
the current `dev` branch.

---

## Phase 1 — LLM Factory ✅ done

`get_llm()` factory pattern, Ollama/OpenAI/vLLM branching.

---

## Phase 2 — Measure + Trim ✅ done

* Ahshaam: GPT-4o judge (`scripts/judge.py`) — rubric on correctness,
  groundedness, tool-use correctness, completeness, style. Also owns token
  trimming (the ~100KB JSON dumps per course/grade block).
* Dev D (co-owns): Golden set of 30-50 questions tagged by intent (36 in
  `evals/golden_set.json`) + the runner that fires them at `/chat`
  (`scripts/eval_runner.py`).
* Dev A: Deterministic regex guardrails (`webservice/guardrails.py`, no
  tool-name leaks, no filler, etc.).
* Dev C: Self-signed HTTPS for dev.

🛑 Tag `v0.2-measured`.

*(Dev A's 24h scheduled cache and Dev B's `/evals` dashboard were scoped here
originally but never landed in the codebase — moved to Phase 3 and Phase 6
respectively, see below.)*

**Measured results** (baseline Aug 1 → latest Aug 13 21:21, 36 cases each):

| | Baseline (Aug 1) | Latest (Aug 13) |
|---|---|---|
| Judge pass rate | 19/36 (53%) | **27/36 (75%)** |
| correctness | 3.61 | 4.25 |
| groundedness | 3.44 | 4.14 |
| tool_use | 2.81 | 4.06 |
| completeness | 3.42 | 4.11 |
| style | 4.53 | 4.69 |
| avg latency | 2.3s | 4.9s (median 2.4s, **one 40.7s outlier**) |

Token trimming confirmed in `autonomy/tools/gophergrades_api.py` etc.:
class 8218→395 chars, prof 8401→121, dept 110092→768, sections 3096→866.

⚠️ The **40.7s latency outlier** in the latest run vs. 6.4s max at baseline
is a regression worth a quick look — tracked under Phase 3 below since the
24h cache (a likely fix) now lives there.

---

## Phase 3 — Agent Quality 🔄 in progress (current phase)

* **Ahshaam:** RAG tool is **already registered** as `course_search` in
  `webservice/agent.py` (type=`retriever`) — earlier framing of "exists but
  never registered" is stale. What's still open: it never fired in the
  latest 36-case eval run (`tools_used` shows only
  gophergrades_*/umn_class_sections/umn_room_booking/tavily_search — zero
  `course_search` hits), so it needs golden-set coverage proving it's
  selected correctly, plus the MCP prototype on one tool (not started — no
  `mcp` references in the codebase yet), A/B'd against the current LangChain
  `@tool` selection. Also: getting the agent to give insight/comparisons
  instead of raw data dumps.
* **Dev A:** Tool robustness — tighter docstrings, graceful degradation,
  retry-on-bad-arg. *(moved from Phase 2)* Also owns the **24h scheduled
  cache** for catalog/GopherGrades data — biggest cost win, and a likely fix
  for the 40.7s latency outlier flagged in Phase 2.
* **Dev B:** Trim + few-shot the system prompt (`webservice/prompts/system.md`,
  still ~2000 tokens), keep changes only if the eval score improves — now
  with a real baseline (table above) to test against.
* **Dev D:** Tavily → ChromaDB code path is wired (`docker-compose.yml` runs
  a `chromadb` service, `autonomy/rag/` chunker/retriever/vector_store is
  correctly targeting it, Tavily kept as fallback) — **but verified live on
  2026-08-15 that it's not actually working**: the `umn_docs` collection is
  completely empty (0 collections via Chroma's API), because (a) the
  webservice's one-time auto-index-on-startup hit `WARNING: ChromaDB
  connection failed` — a `depends_on` race in `docker-compose.yml` that
  waits for the container, not for Chroma's HTTP server readiness, and
  (b) `autonomy/rag/indexer.py` points at `autonomy/rag/data/courses.csv`,
  which doesn't exist in the repo (only `sample_courses.csv` is present, and
  the line to use it is commented out). Until both are fixed, every
  `course_search` call returns "No course information found." — this is
  the real blocker before A/B-testing RAG selection makes sense, not just
  "confirm it's cut over."

**Known issues found in code review (2026-08-16) — add to this phase:**

- **Blocking I/O on every external call** — `gophergrades_api.py` and
  `umn_courses_tool.py` use sync `urlopen` (12s timeout) inside async
  FastAPI endpoints, stalling the whole server while one fetch runs.
  Effectively caps the app at ~1 concurrent user. → Dev A, pairs with the
  cache work.
- **Sequential course fetches** — `_fetch_schedule_data()`
  (`webservice/routers/chat.py:72`) loops up to 4 courses one at a time;
  this fully explains the eval latency tail (sched-03 40.7s, sched-02
  26.0s, multi-05 21.8s). Fix: `asyncio.gather` + async HTTP client.
  → Dev A, same change as above.
- **Card paths give canned text, not answers** — 7 of the 9 judge failures
  in the latest run (grades-04/05/06, sched-05, pers-03, multi-02, multi-04)
  are "right card, but the text didn't answer the specific question" (e.g.
  asked "what % got an A?", got "here are the distributions"). The
  deterministic paths return fixed one-liners with no LLM synthesis.
  Highest-leverage quality fix. → folds into Ahshaam's "insight not dumps"
  item.
- **Destructive guardrails** — `check_prof_rating()`
  (`webservice/guardrails.py:57`) discards the entire response if a
  "prof" message lacks a literal `X/5` pattern; `check_tool_leak()`
  replaces the whole response instead of redacting the leaked name. Both
  can nuke correct answers (likely source of rooms-04-style failures).
  Soften to redact/repair. → Dev A, tool robustness.
- **`tools_used` bug in the professor path** — `chat.py:539`:
  `tools_used.extend(...)` sits inside the `except` block, so on success
  the tool trace is never recorded, skewing eval tool-use scoring. → quick
  fix, anyone.

🛑 Tag `v0.3-quality`.

---

## Phase 4 — Multi-user (auth + database) 📋 planned

* Dev A (owns): Postgres + SQLAlchemy + Alembic, migrate off JSON storage.
  Tables: User, Profile, Conversation, Message. (Early exploratory commits
  exist — JSON→SQLite, not yet Postgres — scope as originally written.)
* Ahshaam: Login/registration flow, session handling, `/health` endpoint,
  env-based CORS.
* Dev B: Login/register UI, profile settings, "delete my data" button.
* Dev C: Cloud Postgres (Neon free tier), Secrets Manager foundation.
* Dev D: Integration tests across the whole auth/persistence flow.

**Known issues found in code review (2026-08-16) — add to this phase:**

- **`/history` returns every user's conversations to any client** — no
  `user_id` filtering anywhere in the history/save endpoints
  (`webservice/routers/chat.py`), and `DELETE /history/clear` wipes
  everyone. Profiles are similarly unscoped. This is a privacy leak even
  for a friends-only soft launch — if any shared testing happens before
  this phase lands, pull the minimum user-scoping fix forward.
- **Shared-JSON-file storage has no locking** — every `/chat` with history
  parses the entire `conversations.json`, and two concurrent saves will
  corrupt it. Goes away with the Postgres migration, but is the concrete
  reason this phase can't slip past real users.
- Head start: Alembic + SQLAlchemy groundwork already exists
  (`alembic/versions/d76846ac7744_initial_migration.py`,
  `scripts/migrate_json_to_db.py`, `docs/database-schema.md`) — this phase
  is closer to done than the plan implies.

🛑 Tag `v0.4-multiuser`.

---

## Phase 5 — Provider Routing 📋 planned

* Ahshaam: Extend the factory so multiple providers run live simultaneously
  (not one-per-process).
* Dev A (owns): The router — simple queries → local Ollama, complex →
  cloud/vLLM, deterministic lookups → no LLM, fallback chain with circuit
  breaker.
* Dev C: Stand up vLLM on an AWS GPU (g5/g6).
* Dev D: Run the Phase 2 harness against every provider/model, produce a
  quality × latency × cost table.
* Dev B: Cold-start "warming up" state, graceful degradation.

**Notes from code review (2026-08-16):**

- The factory (`autonomy/llm/factory.py`) already supports vLLM via env
  vars (`LLM_PROVIDER=vllm` + `LLM_BASE_URL`/`LLM_MODEL`), so the vLLM
  branch is config work, not new code. The gap is only "multiple providers
  live simultaneously."
- The deterministic card paths in `chat.py` already ARE the
  "deterministic lookups → no LLM" tier of the router — the router item
  should build on them, not duplicate them.
- Cost check before standing up the GPU: at current traffic a g5/g6
  instance (~$700+/mo) likely costs far more than the gpt-4o bill. Dev D's
  quality × latency × cost table should run FIRST and gate whether the
  vLLM box happens at all — cheapest outcome may be routing simple queries
  to gpt-4o-mini instead.

🛑 Tag `v0.5-routing`.

---

## Phase 6 — Deploy 📋 planned

* Dev C (owns): Terraform — ECR, ECS Fargate, ALB, Secrets Manager,
  Route 53, S3+CloudFront, CA-signed HTTPS via ACM.
* Ahshaam: IAM least-privilege review, region/domain, AWS Budgets cost caps.
* Dev A: 12-factor review (stdout logging, graceful SIGTERM, no local
  state).
* Dev B: Production build, code splitting, real-device testing.
  *(moved from Phase 2)* Also owns the **`/evals` dashboard**, alongside the
  monitoring stack below.
* Dev D (owns): CI/CD — GitHub Actions with OIDC; eval harness runs as a
  merge gate.
* Monitoring: CloudWatch, Sentry, UptimeRobot on `/health`.

**Known issues found in code review (2026-08-16) — add to this phase:**

- **The Terraform backend + frontend modules are empty placeholders** —
  `infra/modules/backend/main.tf` and `infra/modules/frontend/main.tf` are
  comment-only ("Future resources may include..."). Networking/IAM/database
  modules and the dev env scaffolding exist, but the two modules that
  actually run the app are 0% done — budget this phase accordingly.
- **No CI exists at all** — no `.github/workflows/` directory. The
  eval-harness-as-merge-gate item is greenfield, but cheap: the runner and
  judge already work locally, so a basic Actions workflow wiring them up
  should land EARLY in this phase (or sooner) so every merge from now on
  is eval-gated.
- **`allow_origins=["*"]` with `allow_credentials=True`** in
  `webservice/app.py` — must become env-based CORS before anything is
  publicly reachable (already assigned to Ahshaam in Phase 4, flagging the
  concrete current state here).
- **`/debug/prof` endpoint in `app.py`** ships raw upstream API dumps —
  remove or gate it before deploy (also fails the 12-factor review item).
- **`/health` does not exist yet** — it's listed in Phase 4 (Ahshaam), but
  all monitoring in this phase depends on it; it's a 3-line endpoint, don't
  let it slip to here.

🛑 Tag `v0.6-deployed`.

---

## Phase 7 — Launch 📋 planned

* Load test (50 concurrent), security review, mobile + accessibility audit,
  disclaimers/terms/privacy.
* Soft launch to ~10 friends, then public (r/uofmn, Discord).
* Dev D (owns): load testing, launch-day runbook, coordinating team testing.

**Note from code review (2026-08-16):** the 50-concurrent load test will
fail instantly unless Phase 3's blocking-I/O fix (sync `urlopen` inside
async endpoints) has landed — the backend currently serializes all
external fetches. Same fix, just make sure it isn't discovered here during
launch week.

🛑 Tag `v1.0`.
