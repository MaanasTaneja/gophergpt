import os
import chromadb


# reading in host and port from env
CHROMA_HOST = os.getenv("CHROMA_HOST", "localhost")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", 8000))

# collection name...
COLLECTION_NAME = "umn_docs"

# 
def get_client():
    """
    Creates and returns a ChromaDB HTTP client.
    
    This is the base connection to the ChromaDB service running in Docker.
    Every other function in this file goes through this client to talk to ChromaDB.
    Called once on startup in lifespan_function (app.py) to validate the connection
    is healthy before the app starts serving requests.
    """
    return chromadb.HttpClient(host = CHROMA_HOST, port = CHROMA_PORT)


def get_collection():
    """
    Returns the umn_docs collection from ChromaDB, creating it if it doesn't exist.
    
    A collection is like a table in a traditional database — it holds all of our
    indexed UMN document chunks alongside their embeddings and metadata.
    Used by both upsert_chunks() (during indexing) and query_collection() (at query time).
    """
    client = get_client()
    return client.get_or_create_collection(
        name = COLLECTION_NAME, 
        metadata={"hnsw:space": "cosine"} # cosine similarity (measures distance between similarity)
    )


def upsert_chunks(chunks: list[dict], embeddings: list[list[float]]) -> None:
    """
    Inserts or updates a batch of document chunks and their embeddings into the collection.
    
    Called by the indexer after scraping and embedding a page's chunks.
    'Upsert' means if a chunk ID already exists it gets overwritten — so re-running
    the indexer refreshes stale data rather than duplicating it.

    Each chunk dict will have:
        - text
        - source_url
        - source_name
        - scraped_at
        - chunk_index

    ChromaDB's upsert() needs four things:
        - ids         (must be unique strings — think about how to build these)
        - documents   (the raw text)
        - embeddings  (the float vectors)
        - metadatas   (everything except the text)
    """

    collection = get_collection()

    # builds a stable, unique ID from source + position for re-indexing
    ids = [f"{chunk['source_url']}::{chunk['chunk_index']}" for chunk in chunks]

    documents = [chunk["text"] for chunk in chunks]

    # metadata is stored alongside vector, returned with search results
    metadatas = [
        {
            "source_url": chunk["source_url"],
            "source_name": chunk["source_name"],
            "scraped_at": chunk["scraped_at"],
            "chunk_index": chunk["chunk_index"],
        }
        for chunk in chunks
    ]

    # insert if new, overwrite if already exist
    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )
    

def query_collection(query_embedding: list[float], top_k: int = 5) -> list[dict]:
    """
    Finds the top_k most similar chunks to a given query embedding.
    
    Called by the retriever at query time — the user's question gets embedded first,
    then passed here to find the most relevant stored chunks to use as context.
    Returns a flat list of dicts so the retriever doesn't need to know anything
    about ChromaDB's internal result format.

    Each returned dict will have:
        - text
        - source_url
        - source_name
        - distance    (lower = more similar)
    """

    collection = get_collection()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    # unpacking ChromaDB's nested results format into flat list
    chunk = []

    for text, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        chunk.append({
            "text": text,
            "source_url": metadata["source_url"],
            "source_name": metadata["source_name"],
            "distance": round(distance, 4)
        })

    return chunk