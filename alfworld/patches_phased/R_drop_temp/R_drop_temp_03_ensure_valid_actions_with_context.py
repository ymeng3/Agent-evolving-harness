HISTORY_LENGTH = 10
TEMPERATURE = 0.3

def format_prompt(prompt: str, state: dict) -> str:
    # Add a gentle reminder about focusing on the admissible actions with better context understanding.
    reminder_instruction = "Remember to carefully analyze the context and pick an action from the admissible ones."
    return prompt + "\n" + reminder_instruction

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Use a lower temperature with a similar extra instruction strategy to encourage precise decision-making.
    extra_instruction = "Your last action wasn't valid. Ensure you precisely follow context and admissible actions."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.25}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None