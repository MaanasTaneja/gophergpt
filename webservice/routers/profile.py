from fastapi import APIRouter
from pydantic import BaseModel

from webservice.profile_store import get_profile, save_profile

router = APIRouter()

class ProfileRequest(BaseModel):
    user_id: str
    major: str = ""
    year: str = ""
    personalization_notes: str = ""

# Profile endpoints
@router.get("/profile")
def get_profile_endpoint(user_id: str):
    profile = get_profile(user_id)
    return {"ok": True, "profile": profile}

@router.put("/profile")
def update_profile_endpoint(request: ProfileRequest):
    profile = save_profile(request.user_id, {
        "major": request.major,
        "year": request.year,
        "personalization_notes": request.personalization_notes,
    })
    return {"ok": True, "profile": profile}