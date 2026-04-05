import os
from fastapi import APIRouter
from openai import AsyncOpenAI
from pydantic import BaseModel
from webservice.rag.retriever import retrieve, build_prompt

client = AsyncOpenAI(api_key=os.getenv("OPENAI_KEY"))

router = APIRouter(prefix="/rag", tags=["rag"])


class RAGRequest(BaseModel):
    """
    Incoming request body for the RAG chat endpoint.
    question: the user's question to answer using UMN sources
    top_k:    how many chunks to retrieve from ChromaDB (optional, defaults to 5)
    """
    question: str
    top_k: int = 5


class RAGResponse(BaseModel):
    """
    Response returned to the frontend.
    answer:  GPT-4o's grounded response
    sources: list of chunks used to generate the answer, for citation display
    """
    answer: str
    sources: list[dict]


@router.post("/chat", response_model=RAGResponse)
async def rag_chat(request: RAGRequest):
    """
    Takes a user question, retrieves relevant UMN document chunks from ChromaDB,
    builds a grounded prompt, and returns GPT-4o's answer alongside the sources
    used. Called by the frontend when the user asks a UMN-specific question.

    Steps:
        1. retrieve relevant chunks using the question
        2. build a grounded prompt from the chunks and question
        3. call GPT-4o with the prompt
        4. return the answer and sources
    """
    
    
    chunks = await retrieve(question=request.question, top_k=request.top_k)
    prompt = build_prompt(question=request.question, chunks=chunks)

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}]
    )

    answer = response.choices[0].message.content

    return RAGResponse(answer=answer, sources=chunks)