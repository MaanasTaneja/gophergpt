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
    Creates and returns a ChromaDB HTTP client using the host and port from environment variables.

    Returns:
        a chromadb.HttpClient connected to the ChromaDB service
    """
    return chromadb.HttpClient(host = CHROMA_HOST, port = CHROMA_PORT)


def get_collection():
    """
    Returns the umn_docs ChromaDB collection, creating it if it doesn't exist.

    Returns: 
        chromadb.Collection — the umn_docs collection configured with cosine similarity.
    """
    client = get_client()
    return client.get_or_create_collection(
        name = COLLECTION_NAME, 
        metadata={"hnsw:space": "cosine"} # cosine similarity (measures distance between similarity)
    )


def upsert_chunks(chunks: list[dict], embeddings: list[list[float]]) -> None:
    """
    Inserts or updates a batch of document chunks and their embeddings into the collection.
    
    Args:
        chunks: list of dicts, each with keys text, source_url, source_name, scraped_at, and chunk_index
        embeddings: list of float vectors, one per chunk, in the same order as chunks
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
    

def query_collection(query_embedding: list[float], top_k: int = 5, where: dict | None = None) -> list[dict]:
    """
    Finds the top_k most similar chunks to a given query embedding.
    
    Args:
        query_embedding: embedded vector of the user's question
        top_k: number of chunks to return, defaults to 5
        where: optional metadata filter e.g. {"source_url": "catalog:CSCI1133"}, pass None for normal semantic search

    Returns:
        list of dicts each with keys: text, source_url, source_name, distance (lower = more similar)
    """

    collection = get_collection()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
        where=where
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