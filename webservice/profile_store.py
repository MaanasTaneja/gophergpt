import json
import os

DATA_DIR = "/app/data"
os.makedirs(DATA_DIR, exist_ok=True)

PROFILES_PATH = os.path.join(DATA_DIR, "profiles.json")
CONVERSATIONS_PATH = os.path.join(DATA_DIR, "conversations.json")


def init_store():
    if not os.path.exists(PROFILES_PATH):
        with open(PROFILES_PATH, "w") as f:
            json.dump({}, f)

    if not os.path.exists(CONVERSATIONS_PATH):
        with open(CONVERSATIONS_PATH, "w") as f:
            json.dump({}, f)


def _read_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            print(f"Warning: invalid JSON in {path}, resetting to empty object")
            return {}


def _write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def get_profile(user_id):
    profiles = _read_json(PROFILES_PATH)
    if not isinstance(profiles, dict):
        profiles = {}

    return profiles.get(user_id, {
        "user_id": user_id,
        "major": "",
        "year": "",
        "personalization_notes": ""
    })


def save_profile(user_id, profile_data):
    profiles = _read_json(PROFILES_PATH)
    if not isinstance(profiles, dict):
        profiles = {}

    profiles[user_id] = {
        "user_id": user_id,
        "major": profile_data.get("major", ""),
        "year": profile_data.get("year", ""),
        "personalization_notes": profile_data.get("personalization_notes", "")
    }
    _write_json(PROFILES_PATH, profiles)
    return profiles[user_id]


def save_conversation(user_id, conversation_id, title, messages):
    conversations = _read_json(CONVERSATIONS_PATH)

    if not isinstance(conversations, dict):
        conversations = {}

    if user_id not in conversations:
        conversations[user_id] = []

    already_exists = any(c.get("id") == conversation_id for c in conversations[user_id])
    if not already_exists:
        conversations[user_id].append({
            "id": conversation_id,
            "title": title,
            "messages": messages,
        })

    _write_json(CONVERSATIONS_PATH, conversations)


def get_conversations(user_id):
    conversations = _read_json(CONVERSATIONS_PATH)

    if not isinstance(conversations, dict):
        return []

    return conversations.get(user_id, [])