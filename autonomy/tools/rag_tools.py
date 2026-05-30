from ..rag.retriever import retrieve
from langchain.tools import tool

@tool
async def rag_search(query: str) -> str:
    """
    Searches for course information, pre-reqs, and offered terms using CourseDog.
    Within the ChrombaDB vector database.

    Args: 
        query: the user's question (e.g., "What are the prerequisites for CSCI 1111?")

    Returns: 
        string of relevant course information pulled from vector db.
    """

    # unpacking chunks and question from retrieve
    chunks, question = await retrieve(query)

    text = ""

    # reassembling relevant chunks into readable string
    for chunk in chunks:
        text += chunk["text"]

    # returning readable string of top-k most relevant chunks from vector db using provided query.
    return text