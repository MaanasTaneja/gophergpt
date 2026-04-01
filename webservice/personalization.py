def build_personalized_prompt(profile: dict) -> str:
    details = []

    if profile.get("major"):
        details.append(f"The user is studying {profile['major']}.")
    
    if profile.get("year"):
        details.append(f"The user's academic year is {profile['year']}.")

    if profile.get("personalization_notes"):
        details.append(f"Additional user preferences: {profile['personalization_notes']}.")

    if not details:
        return ""
    
    return (
        "Use the following user profile information to personalize your response. "
        "Only use it when relevant, and do not mention the profile unless it helps answer the user. \n"
        + "\n".join(f"- {item}" for item in details)
    )