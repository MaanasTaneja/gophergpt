from pydantic import BaseModel
from fastapi import APIRouter
from webservice.routers.research import run_research_query, ResearchRequest
from webservice.profile_store import get_profile
from webservice.personalization import build_personalized_prompt
from autonomy.tools.gophergrades_api import gophergrades_class

import os
import re
import json

# This defines where we are storing the conversation history into.
# Will be using as a memory cache, to continue dialogue with agent.
DATA_DIR = "/app/data" # where the file will be stored
os.makedirs(DATA_DIR, exist_ok=True) # makes directory if doesn't exist, nothing if does exist
CONVERSATION_FILE = os.path.join(DATA_DIR, "conversations.json") # full path of where JSON file is stored

gopher_assistant = None

router = APIRouter()

class ChatRequest(BaseModel):

    message: str

    # ensures loading the correct history and not all
    conversation_id: int | None = None # makes it optional, provide stability to frontend, since no history may exist
    user_id: str | None = None  # optional — used to load profile context

class ConversationRequest(BaseModel):
    id: int
    title: str
    messages: list

def extract_course_codes(text):
    """Extract normalized UMN course codes (e.g. CSCI4041) from a message."""
    pattern = r'\b([A-Z]{2,6})\s*(\d{4})\b'
    seen = []
    for m in re.finditer(pattern, text.upper()):
        code = f"{m.group(1)}{m.group(2)}"
        if code not in seen:
            seen.append(code)
    return seen

def is_research_followup(message, history):
    """Returns True if this looks like a follow-up to a prior research query."""
    if not re.match(r'^(what|how)\s+about|^and\b|^what if', message.strip(), re.IGNORECASE):
        return False
    recent = history[-6:] if len(history) > 6 else history
    return any(re.search(r'rea?sea?rch', msg["content"].lower()) for msg in recent)


def build_research_query(current_message, history):
    """Construct a full research query from a follow-up message using prior context."""
    for msg in reversed(history):
        if msg["role"] == "user" and re.search(r'rea?sea?rch', msg["content"].lower()):
            # Extract the new subject from the follow-up (e.g. "what about for biology" → "biology")
            m = re.search(r'(?:for|about|in)\s+([\w\s]+?)(?:\?|$)', current_message, re.IGNORECASE)
            if m:
                subject = m.group(1).strip()
                return f"research opportunities for {subject} at University of Minnesota"
            break
    return current_message


def _enrich_research_query(raw_query: str, profile: dict) -> str:
    """Make a research query more specific using profile context and UMN-specific terms."""
    query = raw_query.strip()

    # Add major from profile if not already in the query
    major = (profile.get("major") or "").strip()
    if major and major.lower() not in query.lower():
        query = f"{query} {major}"

    # Add specificity terms if the query is generic
    generic_terms = ["research", "research opportunities", "research opportunity"]
    if query.lower() in generic_terms or re.match(r'^research\s*(opportunities?|programs?)?\s*$', query.lower()):
        query = f"undergraduate research opportunities programs apply University of Minnesota"
        if major:
            query += f" {major}"
    elif re.search(r'research', query, re.IGNORECASE):
        # Already has research in it — ensure UMN context and add specificity
        if "university of minnesota" not in query.lower() and "umn" not in query.lower():
            query += " University of Minnesota"
        if not any(t in query.lower() for t in ["apply", "program", "lab", "undergraduate", "faculty"]):
            query += " undergraduate program apply"

    return query

def summarize_research_text(text, limit=200):
    if not text:
        return ""

    cleaned = re.sub(r"\s+", " ", str(text)).strip()
    cleaned = re.sub(r"(#{1,6}\s*)+", "", cleaned)

    if len(cleaned) <= limit:
        return cleaned

    shortened = cleaned[:limit].rsplit(" ", 1)[0].strip()
    return f"{shortened}..."

# responsible for loading/retrieving chat messages
@router.post("/chat")
def chat_endpoint(request: ChatRequest):
    global gopher_assistant
    if gopher_assistant is None:
        return {"error": "Agent not initialized."}

    message = request.message.lower()

    # Load profile context if user_id provided
    profile_context = ""
    if request.user_id:
        profile = get_profile(request.user_id)
        profile_context = build_personalized_prompt(profile)

    # Loads the conversation history from file "app/data"
    history = []
    if request.conversation_id is not None and os.path.exists(CONVERSATION_FILE):
        with open(CONVERSATION_FILE, "r") as file:
            conversations = json.load(file)
        match = next((c for c in conversations if c["id"] == request.conversation_id), None)
        if match:
            history = [{
                "role": "user" if msg["isUser"] else "assistant",
                "content": msg["text"]}
                for msg in match["messages"]
            ]
    

    if re.search(r'rea?sea?rch', message) or is_research_followup(message, history):
        raw_query = request.message if re.search(r'rea?sea?rch', message) else build_research_query(message, history)
        query = _enrich_research_query(raw_query, get_profile(request.user_id) if request.user_id else {})
        research_data = run_research_query(ResearchRequest(query=query, max_results=10))

        # Deduplicate by domain, but allow up to 2 results per domain for rich sources
        domain_counts: dict = {}
        unique_results = []
        for r in research_data.results:
            domain = re.sub(r'^https?://([^/]+).*', r'\1', r.url)
            count = domain_counts.get(domain, 0)
            if count < 2:
                domain_counts[domain] = count + 1
                unique_results.append(r)

        summary_text = summarize_research_text(research_data.summary, limit=200)

        return {
            "response": "Here's a research snapshot with the strongest matches I found.",
            "content": [
                {
                    "type": "research",
                    "summary": summary_text,
                    "results": [
                        {
                            "title": summarize_research_text(result.title, limit=90),
                            "url": result.url,
                            "snippet": summarize_research_text(result.snippet, limit=160)
                        }
                        for result in unique_results
                    ][:6]
                }
            ]
        }

    # Detect course comparison requests
    course_codes = extract_course_codes(request.message)
    is_compare_request = "compare" in message and len(course_codes) >= 1

    if is_compare_request or len(course_codes) >= 2:
        courses = []
        for code in course_codes[:2]:
            try:
                class_result = json.loads(gophergrades_class.invoke(code))
                if class_result.get("data"):
                    courses.append({
                        "code": code,
                        "data": class_result["data"]
                    })
            except Exception:
                pass

        if courses:
            guided_message = (
                request.message
                + "\n\n[System: Grade distributions and SRT ratings will be shown visually. "
                "Write 2-3 sentences max giving a high-level insight or recommendation. "
                "Do NOT mention any numbers, grades, or ratings — those are already in the charts.]"
            )
            ai_summary = gopher_assistant.invoke(guided_message, history=history)
            return {
                "response": "",
                "content": [{"type": "compare", "courses": courses, "summary": ai_summary}]
            }

    full_message = f"{profile_context}\n\nUser message:\n{request.message}" if profile_context else request.message
    response = gopher_assistant.invoke(full_message, history=history)
    return {
        "response": response,
        "content": []
    }

# Implementing History Permanent Storage 

# receives a conversation object from frontend, and store it
@router.post("/save")
def save_endpoint(request: ConversationRequest):
    
    # checks if json already exist, before saving.
    if os.path.exists(CONVERSATION_FILE):

        # exist, so read file
        with open(CONVERSATION_FILE, "r") as file:
            conversations = json.load(file)
    else:

        # doesn't exist, so make list to store temporarily
        conversations = []

    # find index of the existing conversation in list, if exist.
    match_index = next((i for i, c in enumerate(conversations) if c["id"] == request.id), None)

    # if conversation exist, overwrite it with updated version.
    if match_index is not None:
        # found index, loading message
        conversations[match_index] = {
            "id": request.id,
            "title": request.title,
            "messages": request.messages
        }
    else:
        # adds conversations components
        conversations.append({
            "id": request.id,
            "title": request.title,
            "messages": request.messages
        })

    # open file to write, creates if doesn't exist
    with open(CONVERSATION_FILE, "w") as file:
        json.dump(conversations, file, indent=2)

    # Good Return
    return {"ok": True}


# clears all saved conversations
@router.delete("/history/clear")
def clear_history_endpoint():
    if os.path.exists(CONVERSATION_FILE):
        os.remove(CONVERSATION_FILE)
    return {"ok": True}


# returns all saved conversations to the frontend
@router.get("/history")
def history_endpoint():
    # checks if file exist
    if os.path.exists(CONVERSATION_FILE):

        # opens and read file
        with open(CONVERSATION_FILE, "r") as file:

            # load file into parsed format
            conversations = json.load(file)

            # return file
            return {"ok": True, "conversations": list(reversed(conversations))}
    else:
        # file doesn't exist, return empty list
        return {"ok": True, "conversations": []}


