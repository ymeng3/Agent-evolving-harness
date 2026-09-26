HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re

    action_match = re.search(r"<action>(.*?)</action>", response)
    if action_match:
        raw_action = action_match.group(1).strip().lower()
        
        # Check if the exact action exists in the admissible list first
        if raw_action in admissible:
            return raw_action
        
        # Use regex for more flexible matching if exact match fails
        cleaned_action = re.sub(r'\s+', ' ', raw_action)
        for admissible_action in admissible:
            if re.search(rf"\b{re.escape(cleaned_action)}\b", admissible_action):
                return admissible_action
    
    # Default to 'look' if unable to find a valid action
    return 'look'