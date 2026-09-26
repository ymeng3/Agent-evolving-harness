HISTORY_LENGTH = 10


def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    base_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    additional_guidance = ["Try to be more precise in your choice.", "Consider all options carefully and pick one that aligns with your reasoning."]
    
    if attempt == 1:
        return {"extra_instruction": f"{base_instruction} {additional_guidance[0]}"}
    elif attempt == 2:
        return {"extra_instruction": f"{base_instruction} {additional_guidance[1]}"}
    return None


import re

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    extract_action = lambda text: (lambda action_match: action_match.group(1).strip().lower() if action_match and (action_match := re.search(r"<action>\s*(.*?)\s*</action>", text, re.IGNORECASE)) and action_match.group(1).strip().lower() in admissible else next((action for action in admissible if action in text.lower()), "look"))(None)
    return extract_action(response)