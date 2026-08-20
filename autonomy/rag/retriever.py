from openai import AsyncOpenAI
import asyncio
import os

from autonomy.rag.embedder import embed_text
from autonomy.rag.vector_store import query_collection

client = AsyncOpenAI(api_key=os.getenv("OPENAI_KEY"))

# Hard ceiling on the ChromaDB round trip. The chroma client is synchronous
# and was being called directly from this coroutine, so a stalled socket read
# blocked uvicorn's event loop and took the WHOLE backend down until restart
# (confirmed by py-spy: httpcore read -> HttpClient.__init__ on MainThread
# inside asyncio_run). Degrading to "no results" is always better than that.
RAG_TIMEOUT_S = float(os.getenv("RAG_TIMEOUT_S", "10"))


async def rewrite_query(question: str, history: list[dict]) -> str:
    """
    Rewrites the user's question using conversation history to make it
    self-contained before embedding.

    Args:
        question: the user's question to re-write with history
        history: the entire conversation history between user and agent

    Returns:
        the rewritten question as a self-contained string
    """
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": (
                "You are a query rewriting assistant. "
                "Given a conversation history and a follow-up question, rewrite the question "
                "to be fully self-contained so it can be understood without the conversation history. "
                "If the question is already self-contained, return it unchanged. "
                "Return only the rewritten question, no explanation or extra text."
            )},
            *history,
            {"role": "user", "content": f"Rewrite this question to be self-contained: {question}"}
        ]
    )
    
    return response.choices[0].message.content


async def retrieve(question: str, history: list[dict] = [], top_k: int = 5, where: dict | None = None) -> tuple[list[dict], str]:
    """
    Retrieves relevant document chunks from ChromaDB for a given question.

    If conversation history is provided, the question is rewritten first
    to be self-contained, improving retrieval accuracy

    Args:
        question: the user's question to retrieve context for
        history: prior conversation messages from query rewriting
        top_k: number of chunks to retrieve from ChromaDB
        where: optional ChromaDB metadata filter, e.g. {"source_url": "catalog:CSCI1133"} for exact course lookups

    Example:
        (
        # chunks — list of dicts
        [
            {
                "text": "CSCI 3081W covers software design patterns...",
                "source_url": "https://umtc.catalog.prod.coursedog.com/courses/123",
                "source_name": "UMN Class Info",
                "distance": 0.1234
            },
            {
                "text": "Prerequisites for CSCI 3081W include CSCI 1933...",
                "source_url": "https://umtc.catalog.prod.coursedog.com/courses/123",
                "source_name": "UMN Class Info",
                "distance": 0.2345
            }
        ],

        # rewritten_question — string
        "What are the prerequisites and description for CSCI 3081W?"
        )

    Returns:
        a tuple of (chunks, rewritten_question) where chunks is a list
        of relevant document dicts and rewritten_question is the 
        self-contained version of the original question
    """
    if history:
        question = await rewrite_query(question, history)
    
    embedded = await embed_text(question)

    # Off the event loop, and time-boxed: query_collection() is sync and its
    # underlying httpx read has no timeout of its own.
    try:
        chunks = await asyncio.wait_for(
            asyncio.to_thread(
                query_collection,
                query_embedding=embedded,
                top_k=top_k,
                where=where,
            ),
            timeout=RAG_TIMEOUT_S,
        )
    except asyncio.TimeoutError:
        print(f"WARNING: ChromaDB query exceeded {RAG_TIMEOUT_S}s - returning no chunks")
        chunks = []
    except Exception as e:
        print(f"WARNING: ChromaDB query failed: {e} - returning no chunks")
        chunks = []

    return chunks, question 