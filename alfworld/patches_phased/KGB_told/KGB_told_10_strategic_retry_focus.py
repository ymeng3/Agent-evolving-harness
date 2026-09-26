HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Provide a tailored instruction based on the attempt number to guide the LLM more effectively.
    if attempt == 1:
        extra_instruction = "Your last action was not valid. Carefully select from the listed admissible actions."
        temperature = 0.5  # Slightly increase temperature to encourage exploration.
        return {"extra_instruction": extra_instruction, "temperature": temperature}
    elif attempt == 2:
        extra_instruction = "Your action selection needs more attention. Focus directly on the admissible options."
        temperature = 0.3  # Decrease temperature to encourage more deterministic choice.
        return {"extra_instruction": extra_instruction, "temperature": temperature}
    return None