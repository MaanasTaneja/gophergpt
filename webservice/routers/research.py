from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import os
import logging

logger = logging.getLogger(__name__)
if not logger.handlers:
    # basic configuration if the app hasn't configured logging yet
    logging.basicConfig(level=logging.INFO)

router = APIRouter()


class ResearchRequest(BaseModel):
    query: str
    max_results: Optional[int] = 5


class ResearchResult(BaseModel):
    title: str
    url: str
    snippet: str


class ResearchResponse(BaseModel):
    results: List[ResearchResult]
    source: str
    summary: Optional[str] = None


@router.post("/research", response_model=ResearchResponse)
def research_endpoint(request: ResearchRequest):
    """
    Search UMN domains using TavilySearch and summarize results with OpenAI.
    If API keys are not present, return a small canned response so the endpoint
    is usable for local testing without secrets.
    """
    load_dotenv()
    logger.info("/research POST called; query=%s, max_results=%s", request.query, request.max_results)
    openai_key = os.getenv("OPENAI_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")

    # Dev fallback when keys are missing
    if not (openai_key and tavily_key):
        sample = [
            ResearchResult(
                title="Sample UMN Result",
                url="https://umn.edu/sample-paper",
                snippet=(
                    "This is a canned sample result returned because OPENAI_KEY or "
                    "TAVILY_API_KEY was not found in the environment. Replace them in "
                    ".env to enable live search."
                ),
            )
        ]
        logger.info("Missing API keys; returning mock response")
        return ResearchResponse(results=sample, source="mock")

    # Try to perform a live Tavily search and produce simple structured results.
    try:
        # Local imports here so the endpoint still imports if the packages are missing
        # but the dev fallback above will run when keys aren't present.
        from autonomy.llm.openai_llm import OpenAILLM
        from langchain_tavily import TavilySearch

        llm = OpenAILLM(model_name="gpt-4o").get_model()
        # TavilySearch expects string values for some params in some versions
        search = TavilySearch(max_results=str(request.max_results), include_domains=["umn.edu"])

        raw = search.run(request.query)

        results: List[ResearchResult] = []

        def clean_text(s: Optional[str]) -> str:
            if not s:
                return ""
            # collapse whitespace and remove weird newlines
            text = " ".join(str(s).split())
            # trim
            text = text.strip()
            # remove JSON-like braces/brackets to avoid raw dumps
            text = text.replace('{', '').replace('}', '').replace('[', '').replace(']', '')
            # remove excessive quotes left from dumps
            text = text.replace("\"", '"').replace("'", "'")
            return text

        def make_paragraph(title: str, snippet: str, url: str, score: Optional[float] = None) -> str:
            parts = []
            if title:
                parts.append(title.rstrip('.'))
            if snippet:
                parts.append(snippet if snippet.endswith('.') else snippet + '.')
            if score is not None:
                parts.append(f"(score: {score:.3f})")
            if url:
                parts.append(url)
            return " — ".join(parts)

        # Flatten raw provider output recursively into a list of leaf items (dicts or strings)
        def flatten_raw(obj):
            items = []
            if isinstance(obj, dict):
                if 'results' in obj and isinstance(obj['results'], list) and obj['results']:
                    for x in obj['results']:
                        items.extend(flatten_raw(x))
                else:
                    items.append(obj)
            elif isinstance(obj, list):
                for x in obj:
                    items.extend(flatten_raw(x))
            else:
                items.append(obj)
            return items

        normalized_items = flatten_raw(raw)

        # If the provider returned a top-level wrapper dict (e.g., {'query':..., 'results':[...]}), unwrap it
        if len(normalized_items) == 1 and isinstance(normalized_items[0], dict):
            wrapper = normalized_items[0]
            if 'results' in wrapper and isinstance(wrapper['results'], list) and wrapper['results']:
                normalized_items = flatten_raw(wrapper['results'])

        # Build simple paragraph results (title — snippet. — score — url)
        for item in normalized_items:
            if isinstance(item, dict):
                title = clean_text(item.get("title") or item.get("metadata", {}).get("title", "") or item.get('name', ''))
                url = clean_text(item.get("url") or item.get("metadata", {}).get("source", "") or item.get('source', ''))
                snippet = clean_text(item.get("snippet") or item.get("content") or item.get("raw_content") or item.get("summary") or item.get('text') or item.get('excerpt'))
                try:
                    score = float(item.get("score")) if item.get("score") is not None else None
                except Exception:
                    score = None
            else:
                title = "Result"
                url = ""
                snippet = clean_text(str(item))
                score = None

            paragraph = make_paragraph(title, snippet[:500], url, score)
            results.append(ResearchResult(title=title or "Untitled", url=url or "", snippet=paragraph))

        logger.info("Tavily search returned %d results", len(results))

        # Create a simple aggregate summary from top results — join first 5 snippets
        simple_summary = " \n\n".join([r.snippet for r in results[:5]]) if results else None

        return ResearchResponse(results=results, source="tavily", summary=simple_summary)

    except Exception as e:
        # On error, return a friendly fallback that contains the error in the snippet
        fallback = [
            ResearchResult(
                title="Fallback Result (error)",
                url="",
                snippet=f"Search failed: {str(e)}",
            )
        ]
        logger.exception("Error during research endpoint")
        return ResearchResponse(results=fallback, source="fallback")


@router.get("/research")
def research_info():
    """Simple GET helper so visiting /research in a browser is useful.

    Returns an example request body and explains that POST is required.
    """
    example = {"query": "climate change adaptation", "max_results": 3}
    return {
        "message": "POST to this endpoint with JSON body {query, max_results}.",
        "example_body": example,
        "note": "If OPENAI_KEY or TAVILY_API_KEY are not set this endpoint returns a mock result for testing.",
    }
