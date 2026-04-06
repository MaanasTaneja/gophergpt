from webservice.rag.chunker import chunk_text
from webservice.rag.embedder import embed_batch
from webservice.rag.vector_store import upsert_chunks
from webservice.rag.sources.classinfo import scrape as scrape_classinfo
import json
from autonomy.tools.gophergrades_api import gophergrades_dept
# TODO: import scrapers for catalog and onestop the same way


def get_urls_from_gophergrades(dept: str) -> list[str]:
    """
    Fetches course page URLs from the GopherGrades API for a given department.

    Called by run_indexing() to dynamically build the list of pages to scrape,
    rather than hardcoding URLs manually. Returns the onestop URL for each
    course in the department, which is what classinfo.py will scrape.
    """

    raw = gophergrades_dept.invoke(dept)
    data = json.loads(raw)
    return [course["onestop"] for course in data["data"]["distributions"] if course["onestop"] is not None]


async def index_source(documents: list[dict]) -> None:
    """
    Runs the chunk → embed → store pipeline for one source's documents.

    Called by run_indexing() once per source. Each document dict coming in
    will have text, source_url, source_name, and scraped_at. After chunking,
    the source metadata needs to be added back onto each chunk before storing,
    since chunk_text() only returns text and chunk_index.
    """
    all_chunks = []

    for document in documents:
        chunks = chunk_text(document["text"])
        
        for chunk in chunks:
            chunk["source_url"] = document["source_url"]
            chunk["source_name"] = document["source_name"]
            chunk["scraped_at"] = document["scraped_at"]
            all_chunks.append(chunk)

    # embeds all chunks 
    embeddings = await embed_batch([c["text"] for c in all_chunks])

    # store everything
    upsert_chunks(chunks=all_chunks, embeddings=embeddings)


async def run_indexing() -> None:
    """
    Orchestrates the full indexing pipeline for all UMN sources.

    Called by scripts/run_indexing.py to trigger a full re-index offline.
    Gets URLs from GopherGrades, scrapes each source, then passes the
    results through index_source() to chunk, embed, and store everything.
    """
    
    urls =  get_urls_from_gophergrades("CSCI") #TODO: UPDATE TO INCLUDE MORE DEPT CODES

    documents = await scrape_classinfo(urls)

    await index_source(documents=documents)

