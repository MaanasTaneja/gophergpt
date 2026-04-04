from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv
import os
import logging

logger = logging.getLogger(__name__)
if not logger.handlers:
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


def run_research_query(request: ResearchRequest) -> ResearchResponse:
    load_dotenv()
    logger.info("/research POST called; query=%s, max_results=%s", request.query, request.max_results)
    openai_key = os.getenv("OPENAI_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")

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

    try:
        from autonomy.llm.openai_llm import OpenAILLM
        from langchain_tavily import TavilySearch

        llm = OpenAILLM(model_name="gpt-4o").get_model()
        search = TavilySearch(max_results=str(request.max_results), include_domains=["umn.edu"])

        raw = search.run(request.query)

        results: List[ResearchResult] = []

        def clean_text(s: Optional[str]) -> str:
            if not s:
                return ""
            text = " ".join(str(s).split()).strip()
            text = text.replace("{", "").replace("}", "").replace("[", "").replace("]", "")
            return text

        def flatten_raw(obj):
            items = []
            if isinstance(obj, dict):
                if "results" in obj and isinstance(obj["results"], list) and obj["results"]:
                    for x in obj["results"]:
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

        if len(normalized_items) == 1 and isinstance(normalized_items[0], dict):
            wrapper = normalized_items[0]
            if "results" in wrapper and isinstance(wrapper["results"], list) and wrapper["results"]:
                normalized_items = flatten_raw(wrapper["results"])

        for item in normalized_items:
            if isinstance(item, dict):
                title = clean_text(item.get("title") or item.get("metadata", {}).get("title", "") or item.get("name", ""))
                url = clean_text(item.get("url") or item.get("metadata", {}).get("source", "") or item.get("source", ""))
                snippet = clean_text(
                    item.get("snippet")
                    or item.get("content")
                    or item.get("raw_content")
                    or item.get("summary")
                    or item.get("text")
                    or item.get("excerpt")
                )
            else:
                title = "Result"
                url = ""
                snippet = clean_text(str(item))

            results.append(
                ResearchResult(
                    title=title or "Untitled",
                    url=url or "",
                    snippet=snippet[:500],
                )
            )

        logger.info("Tavily search returned %d results", len(results))

        summary = "\n\n".join([r.snippet for r in results[:5]]) if results else None
        return ResearchResponse(results=results, source="tavily", summary=summary)

    except Exception as e:
        logger.exception("Error during research endpoint")
        fallback = [
            ResearchResult(
                title="Fallback Result (error)",
                url="",
                snippet=f"Search failed: {str(e)}",
            )
        ]
        return ResearchResponse(results=fallback, source="fallback")


@router.post("/research", response_model=ResearchResponse)
def research_endpoint(request: ResearchRequest):
    return run_research_query(request)


@router.get("/research")
def research_info():
    example = {"query": "climate change adaptation", "max_results": 3}
    return {
        "message": "POST to this endpoint with JSON body {query, max_results}.",
        "example_body": example,
        "note": "If OPENAI_KEY or TAVILY_API_KEY are not set this endpoint returns a mock result for testing.",
    }
