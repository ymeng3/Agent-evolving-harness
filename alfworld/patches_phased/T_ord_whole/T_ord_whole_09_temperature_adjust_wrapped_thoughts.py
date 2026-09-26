HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def format_prompt(prompt: str, state: dict) -> str:
    # Wrap the reasoning part in a user-friendly message
    return prompt.replace("<think>", "<think>Let's think this through. ")

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    instructions = [
        "Your last action wasn't valid. Focus on selecting one of the admissible actions listed.",
        "It seems you missed the valid options. Please consider only the given admissible actions."
    ]
    if attempt in {1, 2}:
        return {"extra_instruction": instructions[attempt - 1], "temperature": TEMPERATURE - 0.1 * attempt}
    return None