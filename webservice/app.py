import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import webservice.dependencies as dependencies
from webservice.routers.chat import router as chat_router
from webservice.routers.courses import router as course_router
from webservice.routers.research import router as research_router
from webservice.routers.profile import router as profile_router
from webservice.profile_store import init_store
from webservice.agent import ChatAgent
from autonomy.rag.indexer import run_indexing
from autonomy.rag.vector_store import get_collection
from autonomy.rag.sources.csv_catalog import CATALOG_SOURCE_NAME
from autonomy.tools.gophergrades_api import fetch_search, fetch_prof


logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

CHROMA_CONNECT_ATTEMPTS = int(os.getenv("CHROMA_CONNECT_ATTEMPTS", "10"))
CHROMA_CONNECT_DELAY_SECONDS = float(os.getenv("CHROMA_CONNECT_DELAY_SECONDS", "2"))


async def connect_to_chroma():
    """
    Returns the umn_docs collection, retrying while ChromaDB comes up.

    The compose healthcheck gates the *initial* boot, but chroma runs with
    restart: always and can cycle underneath a long-lived backend, so a transient
    failure here should not disable RAG for the rest of the process lifetime.

    get_collection() opens an HTTP connection, so it runs in a worker thread to
    keep the event loop free while startup waits.

    Raises:
        the last connection error if every attempt fails.
    """
    last_error: Exception | None = None

    for attempt in range(1, CHROMA_CONNECT_ATTEMPTS + 1):
        try:
            return await asyncio.to_thread(get_collection)
        except Exception as error:
            last_error = error
            logger.warning(
                "ChromaDB not reachable (attempt %d/%d): %s",
                attempt, CHROMA_CONNECT_ATTEMPTS, error,
            )
            if attempt < CHROMA_CONNECT_ATTEMPTS:
                await asyncio.sleep(CHROMA_CONNECT_DELAY_SECONDS)

    raise last_error


def _needs_catalog_indexing(collection, count: int) -> bool:
    """
    Decides whether run_indexing() should fire, and says why.

    A plain `count == 0` check is not enough. umn_docs can be non-empty yet hold
    nothing course_search can use — leftovers from the retired ClassInfoScraper
    are stored under their scraped page URL, while course_search filters on
    source_url == "catalog:<CODE>". A collection full of those looks healthy to a
    count check and permanently suppresses indexing of the real catalog.

    Set FORCE_REINDEX=1 to re-index regardless.

    Args:
        collection: the umn_docs collection
        count: total chunks already reported for it

    Returns:
        True if the catalog should be indexed now.
    """
    if os.getenv("FORCE_REINDEX", "").lower() in ("1", "true", "yes"):
        logger.warning("FORCE_REINDEX set — re-indexing the catalog over %d existing chunk(s).", count)
        return True

    if count == 0:
        logger.warning("umn_docs is empty — starting background indexer.")
        return True

    # cheap existence probe rather than pulling every id back
    catalog = collection.get(where={"source_name": CATALOG_SOURCE_NAME}, limit=1, include=[])
    if not catalog["ids"]:
        logger.warning(
            "umn_docs holds %d chunk(s) but none from %s — course_search's exact-code "
            "lookup cannot match any of them. Starting background indexer.",
            count, CATALOG_SOURCE_NAME,
        )
        return True

    logger.info("umn_docs already holds catalog chunks — skipping indexing.")
    return False


def _log_indexing_result(task: asyncio.Task) -> None:
    """
    Done-callback for the background indexing task started during startup.

    asyncio.create_task() discards whatever the coroutine raises unless someone
    retrieves it, so an indexing crash left no trace at all — the app booted
    "successfully" with an empty umn_docs collection and every course_search
    call fell through to "No course information found." This reports the
    outcome either way, so a failed index is visible in the startup log.
    """
    if task.cancelled():
        logger.warning("Indexing task was cancelled before it finished — umn_docs may be empty.")
        return

    error = task.exception()
    if error is not None:
        logger.error(
            "Indexing failed — umn_docs was left as it was, which may be empty or stale.",
            exc_info=error,
        )
        return

    try:
        collection = get_collection()
        count = collection.count()
        # count alone can be satisfied by unrelated leftovers, so report the
        # catalog chunks specifically — those are what course_search matches on
        catalog = len(collection.get(where={"source_name": CATALOG_SOURCE_NAME}, include=[])["ids"])
    except Exception:
        logger.exception("Indexing finished but the umn_docs chunk count could not be read.")
        return

    if catalog == 0:
        logger.error(
            "Indexing finished but umn_docs holds no catalog chunks (%d total) — "
            "course_search will find nothing.", count,
        )
    else:
        logger.info(
            "Indexing complete — umn_docs holds %d catalog chunk(s) of %d total.",
            catalog, count,
        )


@asynccontextmanager
async def lifespan_function(app: FastAPI):
    init_store()
    dependencies.gopher_assistant = ChatAgent()

    try:
        collection = await connect_to_chroma()
        count = await asyncio.to_thread(collection.count)
        logger.info("ChromaDB connected successfully — umn_docs holds %d chunks.", count)

        if await asyncio.to_thread(_needs_catalog_indexing, collection, count):
            task = asyncio.create_task(run_indexing())
            task.add_done_callback(_log_indexing_result)
    except Exception:
        logger.exception(
            "ChromaDB connection failed — course_search will find nothing until this is fixed."
        )

    yield


app = FastAPI(lifespan=lifespan_function)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(research_router)
app.include_router(chat_router)
app.include_router(course_router)
app.include_router(profile_router)


@app.get("/")
def root():
    return {"message": "The greatest openai wrapper ever made."}


def _search_prof_code(name):
    try:
        result = fetch_search(name)
        candidates = []

        def _extract_instructors(obj):
            if isinstance(obj, dict):
                for key in ("instructors", "professors", "instructor", "professor"):
                    val = obj.get(key)
                    if isinstance(val, list):
                        candidates.extend(val)
                for key in ("data", "results"):
                    if isinstance(obj.get(key), (dict, list)):
                        _extract_instructors(obj[key])
            elif isinstance(obj, list):
                for item in obj:
                    if isinstance(item, dict):
                        if any(k in item for k in ("instructor_id", "prof_id", "slug", "full_name")):
                            candidates.append(item)
                        else:
                            _extract_instructors(item)

        _extract_instructors(result)

        if candidates:
            first = candidates[0]
            code = (
                first.get("instructor_id")
                or first.get("prof_id")
                or first.get("id")
                or first.get("slug")
                or first.get("code")
            )
            display = (
                first.get("full_name")
                or first.get("name")
                or first.get("instructor_name")
                or name
            )
            if code:
                return str(code), display
    except Exception:
        import logging

        logging.getLogger(__name__).exception("Prof search failed for %r", name)
    return None


@app.get("/debug/prof")
def debug_prof(name: str):
    search_raw = fetch_search(name)
    found = _search_prof_code(name)
    prof_raw = None
    if found:
        code, _ = found
        prof_raw = fetch_prof(code)
    return {"search": search_raw, "found": found, "prof": prof_raw}