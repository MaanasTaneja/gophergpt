import asyncio
from ..rag.retriever import retrieve
from langchain.tools import tool

@tool
def rag_search(query: str) -> str:
    """
    Searches for course information, pre-reqs, and offered terms using CourseDog.
    Within the ChrombaDB vector database.

    Args:
        query: the user's question (e.g., "What are the prerequisites for CSCI 1111?")

    Returns:
        string of relevant course information pulled from vector db.
    """
    try:
        chunks, question = asyncio.run(retrieve(query))

        text = ""
        for chunk in chunks:
            text += chunk["text"]

        return text
    except Exception as e:
        return f"RAG search failed: {str(e)}"