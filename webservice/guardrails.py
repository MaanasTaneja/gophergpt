import re

def check_tool_leak(response: str) -> str:
    """
    Checks the response for any mention of tools

    Args:
        response: the response from agent, before showing user

    Returns:
        a generic response if name of tool is in response, else the original response unchanged
    """

    tool_list = ["gophergrades_search", 
                 "gophergrades_class", 
                 "gophergrades_prof", 
                 "gophergrades_dept", 
                 "umn_class_sections", 
                 "umn_room_booking", 
                 "course_search", 
                 "rag_search", 
                 "tavily_search"]
    
    for tool in tool_list:
        if tool in response:
            return "I found some relevant information for you. " \
            "Please try rephrasing your question if you'd like more details."
        
    return response


def check_filler(response: str) -> str:
    """
    Checks the response for filler words

    Args:
        response: the response from agent, before showing user

    Returns:
        stripped response with filler phrases removed, 
        or the original response unchanged if none are found.
    """

    filler_list = ["Don't hesitate to reach out",
                   "I hope this helps",
                   "Is there anything else I can help you with",
                   "let me know",
                   "feel free"]
    
    sentences = re.split(r'(?<=[.!?])\s+', response)
    filtered = [s for s in sentences if not any(filler.lower() in s.lower() for filler in filler_list)]
    response = " ".join(filtered)

    return response


def check_prof_rating(response: str, message: str) -> str:
    """
    Nudges professor answers toward including a rating, without destroying them.

    Args:
        response: the response from agent, before showing user
        message: the query from the user

    Returns:
        the original response whenever it actually answered something, else a
        fallback prompting the user to ask more specifically.

    NOTE (Dev A / Phase 3 "soften destructive guardrails"): the original version
    replaced the ENTIRE response whenever a prof-related message came back
    without a literal `X/5`. That nuked correct answers — "who is the easiest
    professor for PSY 1001" (answered with A/B rates per instructor) and "tell
    me about the professors in the CSCI department" (answered with the
    Department Explorer redirect) are both right and neither can contain a
    rating. Now the fallback only fires when the response carries no substance
    at all.
    """

    prof_keywords = ["professor", "prof", "instructor", "teacher", "who teaches"]

    if not any(keyword in message.lower() for keyword in prof_keywords):
        return response

    if re.search(r'\d+\.?\d*/5', response):
        return response

    # No explicit rating — keep the answer anyway if it carries real content:
    # grade stats, a course list, or the department redirect.
    has_substance = (
        re.search(r'\d+\s?%', response)                 # any percentage
        or re.search(r'\bGPA\b', response, re.I)         # a GPA figure
        or re.search(r'\b[A-Z]{2,5}\s?\d{4}\b', response)  # a course code
        or "department explorer" in response.lower()     # intentional redirect
    )
    if has_substance:
        return response

    return "I wasn't able to find a rating for that professor. " \
        "Try asking about a specific professor by name."


def run_guardrails(response: str, message: str) -> str:
    """
    Runs all guardrail checks on the agent response in sequence. 
    Returns the cleaned response or a fallback message if any check fails.

    Args:
        response: the response from agent, before showing user
        message: the query from the user

    Returns:
        the cleaned response or a fallback message if any check fails.    
    """
    response = check_tool_leak(response)
    response = check_filler(response)
    response = check_prof_rating(response, message)


    return response