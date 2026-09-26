HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Encouraging the model to focus on admissible actions with temperature adjustments for each attempt.
    if attempt == 1:
        return {
            "extra_instruction": "Focus on the admissible actions. Consider the task's objective.",
            "temperature": 0.3
        }
    elif attempt == 2:
        return {
            "extra_instruction": "Try again with attention to admissible actions. Think strategically.",
            "temperature": 0.2
        }
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Heuristic to choose the first perceived viable option among admissible actions.
    if "look around" in admissible:
        return "look around"
    elif "look" in admissible:
        return "look"
    else:
        return admissible[0]