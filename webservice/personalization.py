def build_personalized_prompt(profile: dict) -> str:
    details = []

    if profile.get("major"):
        details.append(f"The user is studying {profile['major']}.")

    level = profile.get("level", "").strip()
    year = profile.get("year", "").strip()

    if level and year:
        details.append(f"The user is a {level} student in their {year}.")
    elif level:
        details.append(f"The user is a {level} student.")
    elif year:
        details.append(f"The user's academic year is {year}.")

    if level == "Undergraduate":
        details.append(
            "When recommending courses, prioritize undergraduate-level courses (1xxx–4xxx). "
            "Check that any prerequisites are appropriate for an undergraduate student. "
            "Avoid recommending graduate-only courses (5xxx+) unless the user explicitly asks."
        )
    elif level == "Graduate":
        details.append(
            "When recommending courses, prioritize graduate-level courses (5xxx+). "
            "The user has already completed undergraduate prerequisites, so do not suggest intro-level courses. "
            "Recommend advanced or specialized courses relevant to their field."
        )
    elif level == "PhD":
        details.append(
            "The user is a PhD student. When recommending courses, focus on advanced graduate courses (5xxx+) "
            "and research-oriented offerings. Assume strong foundational knowledge — skip introductory content. "
            "Highlight courses relevant to research depth, specialization, or qualifying exam preparation."
        )

    if profile.get("personalization_notes"):
        details.append(f"Additional user preferences: {profile['personalization_notes']}.")

    if not details:
        return ""

    return (
        "Use the following user profile information to personalize your response. "
        "Only use it when relevant, and do not mention the profile unless it helps answer the user.\n"
        + "\n".join(f"- {item}" for item in details)
    )
