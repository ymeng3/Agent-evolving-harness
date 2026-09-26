HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def format_prompt(prompt: str, state: dict) -> str:
    # Append a focus message to the prompt encouraging the model to concentrate on the changes in the environment
    change_focus_message = "Focus on any changes in the environment and how they relate to your goal."
    return f"{prompt}\n{change_focus_message}"

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None