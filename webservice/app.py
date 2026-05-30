import asyncio
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
from autonomy.rag.vector_store import get_client, get_collection


@asynccontextmanager
async def lifespan_function(app: FastAPI):
    """
    Handles app startup and shutdown — initializes the agent, wires dependencies, and connects to ChromaDB.

    Args:
        app: the FastAPI application instance
    """
    
    init_store()
    dependencies.gopher_assistant = ChatAgent()

    try:
        get_client()
        print("ChromaDB connected successfully.")

        collection = get_collection()

        if collection.count() == 0:
            print("Collection is empty — running indexer...")
            asyncio.create_task(run_indexing())

    except Exception as e:
        print(f"WARNING: ChromaDB connection failed: {e}")

    yield


app = FastAPI(lifespan=lifespan_function)
app.add_middleware(CORSMiddleware,
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
    """
    Health check endpoint.

    Returns:
        a dict with a welcome message confirming the service is running
    """
    return {"message": "The greatest openai wrapper ever made."}