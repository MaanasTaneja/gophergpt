from fastapi import APIRouter
from autonomy.tools.gophergrades_api import gophergrades_search, gophergrades_class, gophergrades_dept
from pydantic import BaseModel

import json
import statistics
import re

router = APIRouter()

class CourseLookupRequest(BaseModel):
    query: str

class ProfessorLookupRequest(BaseModel):
    name: str

class DepartmentLookupRequest(BaseModel):
    dept: str

def _parse_srt_vals(raw):
    if raw is None or raw == "null":
        return None

    if isinstance(raw, dict):
        return raw

    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return None


def _sum_grade_counts(grades):
    if not grades:
        return 0

    return sum(value for value in grades.values() if isinstance(value, (int, float)))


def _compute_course_metrics(course):
    grades = course.get("total_grades") or {}
    total_outcomes = _sum_grade_counts(grades)
    srt_vals = _parse_srt_vals(course.get("srt_vals"))

    recommend = srt_vals.get("RECC") if srt_vals else None
    responses = srt_vals.get("RESP") if srt_vals else None

    high_grade_rate = None
    challenge_rate = None
    withdraw_rate = None

    if total_outcomes > 0:
        high_grade_rate = (
            grades.get("A", 0) + grades.get("A-", 0) + grades.get("B+", 0)
        ) / total_outcomes
        challenging_count = (
            grades.get("C-", 0)
            + grades.get("D+", 0)
            + grades.get("D", 0)
            + grades.get("F", 0)
            + grades.get("W", 0)
            + grades.get("N", 0)
        )
        # Bayesian smoothing: blend observed rate toward a prior (7%) weighted
        # by 100 pseudo-students. Small classes get pulled toward the prior;
        # large classes are barely affected.
        _PRIOR_RATE = 0.07
        _PRIOR_WEIGHT = 100
        challenge_rate = (challenging_count + _PRIOR_WEIGHT * _PRIOR_RATE) / (total_outcomes + _PRIOR_WEIGHT)
        withdraw_rate = grades.get("W", 0) / total_outcomes

    return {
        "recommend": recommend,
        "responses": responses,
        "deep_understanding": srt_vals.get("DEEP_UND") if srt_vals else None,
        "stimulating_interest": srt_vals.get("STIM_INT") if srt_vals else None,
        "technical_effectiveness": srt_vals.get("TECH_EFF") if srt_vals else None,
        "accessible_support": srt_vals.get("ACC_SUP") if srt_vals else None,
        "effort": srt_vals.get("EFFORT") if srt_vals else None,
        "grading_standards": srt_vals.get("GRAD_STAND") if srt_vals else None,
        "high_grade_rate": high_grade_rate,
        "challenge_rate": challenge_rate,
        "withdraw_rate": withdraw_rate,
    }


def _normalize_department_course(course):
    return {
        "id": course.get("id"),
        "course_num": course.get("course_num", ""),
        "title": course.get("class_desc", ""),
        "description": course.get("onestop_desc", ""),
        "catalog_url": course.get("onestop", ""),
        "credits": {
            "min": course.get("cred_min"),
            "max": course.get("cred_max"),
        },
        "total_students": course.get("total_students", 0),
        "grades": course.get("total_grades") or {},
        "metrics": _compute_course_metrics(course),
    }


def _build_department_summary(courses):
    student_counts = [course.get("total_students", 0) for course in courses]
    recommend_values = [
        course["metrics"]["recommend"]
        for course in courses
        if course["metrics"]["recommend"] is not None
    ]

    return {
        "course_count": len(courses),
        "total_students": sum(student_counts),
        "median_course_size": int(statistics.median(student_counts)) if student_counts else 0,
        "courses_with_srt": len(recommend_values),
        "avg_recommend": (
            round(sum(recommend_values) / len(recommend_values), 3)
            if recommend_values
            else None
        ),
    }


def _build_department_featured(courses):
    popular = sorted(
        courses,
        key=lambda course: course.get("total_students", 0),
        reverse=True,
    )[:8]

    best_rated_pool = [
        course
        for course in courses
        if course["metrics"]["recommend"] is not None
        and (course["metrics"]["responses"] or 0) >= 50
    ]
    best_rated = sorted(
        best_rated_pool,
        key=lambda course: (
            course["metrics"]["recommend"],
            course["metrics"]["responses"] or 0,
        ),
        reverse=True,
    )[:8]

    challenging_pool = [
        course
        for course in courses
        if course["metrics"]["challenge_rate"] is not None
        and _sum_grade_counts(course.get("grades")) >= 100
    ]
    most_challenging = sorted(
        challenging_pool,
        key=lambda course: (
            course["metrics"]["challenge_rate"],
            course.get("total_students", 0),
        ),
        reverse=True,
    )[:8]

    return {
        "popular": popular,
        "best_rated": best_rated,
        "most_challenging": most_challenging,
    }


@router.post("/umn/course")
def lookup_course(request: CourseLookupRequest):
    query = request.query.strip()

    try:
        search_result = json.loads(gophergrades_search.invoke(request.query))
        
        response = {
            "ok": True,
            "query": query,
            "search": search_result,
            "class": None
        }

        normalized = query.replace(" ", "").upper()

        if re.match(r"^[A-Z]{2,}\d{4}$", normalized):
            class_result = json.loads(gophergrades_class.invoke(normalized))
            response["class"] = class_result
        
        return response
    
    except Exception as e:
        return {
            "ok": False,
            "query": query,
            "error": str(e)
        }

@router.post("/umn/prof")
def lookup_professor(request: ProfessorLookupRequest):
    name = request.name.strip()

    try:
        search_result = json.loads(gophergrades_search.invoke(name))

        return {
            "ok": True,
            "name": name,
            "search": search_result
        }

    except Exception as e:
        return {
            "ok": False,
            "name": name,
            "error": str(e)
        }
    

@router.post("/umn/dept")
def lookup_department(request: DepartmentLookupRequest):
    dept = request.dept.strip().upper()

    try:
        raw_result = json.loads(gophergrades_dept.invoke(dept))

        if not raw_result.get("success") or not raw_result.get("data"):
            return {
                "ok": False,
                "dept": dept,
                "error": "Department not found."
            }

        data = raw_result["data"]
        normalized_courses = [
            _normalize_department_course(course)
            for course in data.get("distributions", [])
        ]

        return {
            "ok": True,
            "dept": {
                "campus": data.get("campus"),
                "code": data.get("dept_abbr"),
                "name": data.get("dept_name"),
            },
            "summary": _build_department_summary(normalized_courses),
            "featured": _build_department_featured(normalized_courses),
            "courses": normalized_courses,
        }

    except Exception as e:
        return {
            "ok": False,
            "dept": dept,
            "error": str(e)
        }
    