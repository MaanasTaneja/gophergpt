from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
import os
import json

router = APIRouter()

class DifficultyRequest(BaseModel):
    course_id: str  # e.g. "CSCI1133"

class DifficultyResponse(BaseModel):
    course_id: str
    difficulty_score: Optional[float]  # 1.0 (easy) to 10.0 (hard)
    reasoning: str
    average_gpa: Optional[float]
    source: str

@router.post("/umn/difficulty", response_model=DifficultyResponse)
def difficulty_endpoint(request: DifficultyRequest):
    load_dotenv()
    openai_key = os.getenv("OPENAI_KEY")

    course_id = request.course_id.strip().replace(" ", "").upper()

    # Import GopherGrades tool
    from autonomy.tools.gophergrades_api import gophergrades_class
    from autonomy.llm.openai_llm import OpenAILLM

    # Fetch grade distribution data
    try:
        raw = gophergrades_class.invoke(course_id)
        course_data = json.loads(raw)
    except Exception as e:
        return DifficultyResponse(
            course_id=course_id,
            difficulty_score=None,
            reasoning=f"Failed to fetch course data: {str(e)}",
            average_gpa=None,
            source="error"
        )

    # Extract average GPA if available
    try:
        avg_gpa = course_data.get("average_gpa") or course_data.get("gpa")
    except Exception:
        avg_gpa = None

    # Fallback if no API key
    if not openai_key:
        return DifficultyResponse(
            course_id=course_id,
            difficulty_score=None,
            reasoning="OpenAI key not set. Cannot analyze difficulty.",
            average_gpa=avg_gpa,
            source="mock"
        )

    # Send to OpenAI for analysis
    try:
        llm = OpenAILLM(model_name="gpt-4o").get_model()

        prompt = f"""
You are a course difficulty analyst for the University of Minnesota.
Based on the following GopherGrades data for course {course_id}, estimate its difficulty.

Data:
{json.dumps(course_data, indent=2)}

Respond with:
1. A difficulty score from 1.0 (very easy) to 10.0 (very hard)
2. A short reasoning (2-3 sentences)

Format your response exactly like this:
SCORE: <number>
REASONING: <text>
"""
        result = llm.invoke(prompt)
        text = result.content if hasattr(result, "content") else str(result)

        # Parse response
        score = None
        reasoning = text

        for line in text.splitlines():
            if line.startswith("SCORE:"):
                try:
                    score = float(line.replace("SCORE:", "").strip())
                except ValueError:
                    pass
            if line.startswith("REASONING:"):
                reasoning = line.replace("REASONING:", "").strip()

        return DifficultyResponse(
            course_id=course_id,
            difficulty_score=score,
            reasoning=reasoning,
            average_gpa=avg_gpa,
            source="gophergrades+openai"
        )

    except Exception as e:
        return DifficultyResponse(
            course_id=course_id,
            difficulty_score=None,
            reasoning=f"AI analysis failed: {str(e)}",
            average_gpa=avg_gpa,
            source="gophergrades"
        )
