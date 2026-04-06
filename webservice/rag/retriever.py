from webservice.rag.embedder import embed_text
from webservice.rag.vector_store import query_collection


async def retrieve(question: str, top_k: int = 5) -> list[dict]:
    """
    Takes a user's question and returns the most relevant chunks from ChromaDB.

    Called by build_prompt() — embeds the question first, then uses the
    resulting vector to find the closest matching chunks in the vector store.
    This is the core of the RAG query pipeline.
    """
    embedded = await embed_text(question)
    chunk = query_collection(query_embedding=embedded, top_k=top_k)

    return chunk


def build_prompt(question: str, chunks: list[dict]) -> str:
    """
    Combines retrieved chunks and the user's question into a single prompt
    string ready to be sent to GPT-4o.

    Called by the RAG router after retrieve() returns relevant chunks.
    The prompt instructs GPT-4o to answer using only the provided sources,
    so responses are grounded in real UMN documents rather than guesswork.

    Each chunk dict will have:
        - text
        - source_url
        - source_name
        - distance
    """
    sources = ""
    for i, chunk in enumerate(chunks):
        sources += f"[{i+1}] {chunk['text']} (from: {chunk['source_url']})\n"
        
    return f"""You are a helpful UMN assistant. Answer the question using only the sources below.
    If the answer is not in the sources, say so.

    SOURCES:
    {sources}

    QUESTION: {question}"""