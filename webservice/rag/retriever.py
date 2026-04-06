from openai import AsyncOpenAI
import os

from webservice.rag.embedder import embed_text
from webservice.rag.vector_store import query_collection

client = AsyncOpenAI(api_key=os.getenv("OPENAI_KEY"))


async def rewrite_query(question: str, history: list[dict]) -> str:
    """
    Rewrites the user's question using conversation history to make it
    self-contained before embedding.

    Called by retrieve() before embedding the question so that follow-up
    questions like "what about CSCI 3081?" get rewritten into
    "what are the prerequisites for CSCI 3081?" for better RAG retrieval.
    If there is no history, the original question is returned unchanged.
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


async def retrieve(question: str, history: list[dict] = [], top_k: int = 5) -> tuple[list[dict], str]:
    """
    Returns both the relevant chunks AND the rewritten question.
    The rewritten question is used in build_prompt() so the grounded
    prompt reflects the full context, not the vague follow-up.
    """
    if history:
        question = await rewrite_query(question, history)
    
    embedded = await embed_text(question)
    chunks = query_collection(query_embedding=embedded, top_k=top_k)
    
    return chunks, question 


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
        
    return f"""You are a helpful UMN assistant. Answer ONLY what was asked — do not include extra information beyond what the question asks for.
    Use only the sources below to answer.
    If the answer is not in the sources, say so.

    SOURCES:
    {sources}

    QUESTION: {question}"""