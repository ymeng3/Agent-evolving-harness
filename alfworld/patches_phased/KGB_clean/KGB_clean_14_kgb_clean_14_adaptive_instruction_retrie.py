HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    instruction_templates = [
        "Your last action wasn't valid. Focus on selecting one of the admissible actions listed.",
        "Please try again. Ensure your action is among the admissible ones.",
        "Final retry: Select an admissible action from the list."
    ]
    if attempt <= len(instruction_templates):
        return {"extra_instruction": instruction_templates[attempt - 1]}
    return None