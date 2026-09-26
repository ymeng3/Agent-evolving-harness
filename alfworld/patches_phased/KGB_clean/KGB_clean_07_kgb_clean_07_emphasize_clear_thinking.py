HISTORY_LENGTH = 10
TEMPERATURE = 0.3

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.7}
    return None

def format_prompt(prompt: str, state: dict) -> str:
    parts = prompt.split("\n")
    if len(parts) > 5:
        parts[-2] = "Think clearly and ensure your action is within the admissible list."
    return "\n".join(parts)