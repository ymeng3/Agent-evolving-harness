HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prioritize 'look' as the fallback as it is generally harmless and informative
    preferred_actions = ['look', 'examine', 'inspect']
    for action in preferred_actions:
        if action in admissible:
            return action

    # If none of the preferred actions are available, return the first admissible action
    return admissible[0] if admissible else 'look'