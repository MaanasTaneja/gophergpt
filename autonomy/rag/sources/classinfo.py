import httpx
from bs4 import BeautifulSoup
from datetime import datetime

# human readable label used in metadata and chunk IDs
SOURCE_NAME = "UMN Class Info"


async def fetch_page(url: str) -> str:
    """
    Fetches the raw HTML from a given URL and returns it as a string.

    Used internally by scrape() — not called directly by the indexer.
    Keeping fetch and parse separate makes each easier to test and debug.
    """

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        return response.text
    

def parse_text(html: str) -> str:
    """
    Takes raw HTML and returns just the readable text, stripping all tags,
    scripts, and navigation elements.

    Used internally by scrape() after fetch_page() returns the raw HTML.
    BeautifulSoup handles the tag stripping — you just need to call the
    right method on it.

    Hint: look into BeautifulSoup's get_text() method, and consider
          passing separator=" " to avoid words running together
    """

    return BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)


async def scrape(urls: list[str]) -> list[dict]:
    """
    Fetches and parses a list of classinfo URLs, returning a list of raw
    document dicts ready to be passed to chunk_text() in chunker.py.

    Called by the indexer during the indexing pipeline.
    Each returned dict will have:
        - text:        the parsed page text
        - source_url:  the URL it came from
        - source_name: SOURCE_NAME constant
        - scraped_at:  ISO timestamp of when it was scraped
    """

    documents = []

    for url in urls:
        try:
            html = await fetch_page(url)
            text = parse_text(html)

            documents.append({
                "text": text,
                "source_url": url,
                "source_name": SOURCE_NAME,
                "scraped_at": datetime.utcnow().isoformat()
            })
        except Exception as e:
            print(f"Skipping {url}: {e}")
            
    return documents