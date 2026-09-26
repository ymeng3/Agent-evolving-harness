HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus specifically on selecting one of the admissible actions. Be precise and review the options carefully."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def format_prompt(prompt: str, state: dict) -> str:
    additional_guidance = " When choosing an action, ensure it matches exactly one of the options provided."
    if "action_guidance" not in state:
        state["action_guidance"] = True  # Add a flag to state so the guidance is added only once
        prompt += additional_guidance
    return prompt