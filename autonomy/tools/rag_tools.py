import os

from ..rag.retriever import retrieve
from langchain.tools import tool

from dotenv import load_dotenv
from langchain_tavily import TavilySearch


load_dotenv()
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY")
tavily = TavilySearch(max_results=5, topic="general", search_depth="advanced", include_domains=["umn.edu", "reddit.com"])


async def _retrieve_chunks(query: str):
    """
    Calls retrieve() and returns the raw chunk dicts for a given query

    Args:
        query: the user's question (e.g., "What are the prerequisites for CSCI 1111?")

    Returns:
        list of dicts, each containing text, source_url, source_name, and distance
    """
    chunks, rewritten_question = await retrieve(query)

    return chunks


@tool
async def rag_search(query: str) -> str:
    """
    Searches the ChromaDB vector database directly for UMN course information. 
    Returns raw results with no fallback. Use course_search instead for general course questions.

    Args:
        query: the user's question (e.g., "What are the prerequisites for CSCI 1111?")

    Returns:
        string of course information retrieved directly from the vector database, no fallback applied.
    """

    try:
        chunks = await _retrieve_chunks(query)

        text = ""
        for chunk in chunks:
            text += chunk["text"]

        return text
    except Exception as e:
        return f"RAG search failed: {str(e)}"
    

@tool
async def course_search(query: str) -> str:
    """
    Primary tool for UMN course questions. Use for course descriptions, prerequisites, and offered terms. 
    Searches the course catalog database first, falls back to web search if no relevant results are found.

    Args:
        query: the user's question (e.g., "What are the prerequisites for CSCI 1111?")

    Returns:
        string of course information from the vector database or web search.    
    """

    try:
        chunks = await _retrieve_chunks(query)

        if all(chunk["distance"] > 0.7 for chunk in chunks):
            return tavily.invoke(query)
        
        else:
            text = ""
            for chunk in chunks:
                text += chunk["text"]   

        return text
    except Exception as e:
        return f"Course search failed: {str(e)}"