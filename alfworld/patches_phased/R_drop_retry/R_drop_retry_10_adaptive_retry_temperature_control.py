HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def format_prompt(prompt: str, state: dict) -> str:
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r'<action>(.*?)</action>', response, re.IGNORECASE)
    if match:
        return match.group(1).strip().lower()
    return ''

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        new_temperature = max(0.4, TEMPERATURE - 0.2)
        return {"extra_instruction": "Ensure your action is among the admissible actions.", "temperature": new_temperature}
    elif attempt == 2:
        new_temperature = max(0.3, TEMPERATURE - 0.4)
        return {"extra_instruction": "Action must be one of the listed admissible actions.", "temperature": new_temperature}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    pass

def choose_fallback(admissible: list[str], state: dict) -> str:
    return admissible[0]