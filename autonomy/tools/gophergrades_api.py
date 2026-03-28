import os
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from langchain.tools import tool


def _get_json(url: str, timeout: int = 12) -> dict:
    req = Request(url, headers={"User-Agent": "gophergpt/1.0"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            data = resp.read().decode("utf-8")
            return json.loads(data)
    except HTTPError as e:
        return {"success": False, "error": f"HTTPError {e.code}: {e.reason}", "url": url}
    except URLError as e:
        return {"success": False, "error": f"URLError: {e.reason}", "url": url}
    except Exception as e:
        return {"success": False, "error": f"Unknown error: {str(e)}", "url": url}


def _base_api() -> str:
    # Use deployed umn.lol by default, override in .env for local dev:
    # GOPHERGRADES_API_BASE=http://localhost:3000/api
    return os.getenv("GOPHERGRADES_API_BASE", "https://umn.lol/api").rstrip("/")

# Returns class_name, description, and total student aggregated. 
@tool
def gophergrades_search(query: str) -> str:
    """
    Search UMN classes/instructors/departments using GopherGrades.
    Input: a free-text query (e.g., "CSCI 1933", "data structures", "Kauffman")
    Output: JSON string of results.
    """
    base = _base_api()
    qs = urlencode({"q": query})
    url = f"{base}/search?{qs}"
    return json.dumps(_get_json(url), ensure_ascii=False)

# Returns course info: {desc, total_student, grades, SRT, profs, and their ratings}
@tool
def gophergrades_class(class_code: str) -> str:
    """
    Get class info + grade distributions from GopherGrades.
    Input: class code like "CSCI1933" or "CSCI 1933"
    Output: JSON string with class info + distributions.
    """
    base = _base_api()
    normalized = class_code.replace(" ", "").upper()
    url = f"{base}/class/{normalized}"
    return json.dumps(_get_json(url), ensure_ascii=False)

# Returns prof's RMP, courses, overall grade breakdown, and SRT value
@tool
def gophergrades_prof(prof_code: str) -> str:
    """
    Get professor info + distributions from GopherGrades.
    Input: prof code/id from a search result (not the name).
    Output: JSON string with instructor info + distributions.
    """
    base = _base_api()
    url = f"{base}/prof/{prof_code}"
    return json.dumps(_get_json(url), ensure_ascii=False)

# Returns full list of courses and their grade breakdown with student ratings, and SRT values
@tool
def gophergrades_dept(dept_code: str) -> str:
    """
    Get department info + distributions from GopherGrades.
    Input: dept code like "CSCI"
    Output: JSON string with department info + distributions.
    """
    base = _base_api()
    url = f"{base}/dept/{dept_code.upper()}"
    return json.dumps(_get_json(url), ensure_ascii=False)

