HISTORY_LENGTH = 8

def format_prompt(prompt: str, state: dict) -> str:
    # Emphasize the importance of selecting an admissible action in the prompt
    return prompt.replace("You should first reason step-by-step about the current situation.",
                          "You should consider all admissible actions carefully while reasoning step-by-step about the current situation.")

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    
    # Extracting the action inside <action> tags, allowing variations in case
    match = re.search(r"<action>\s*(.*?)\s*</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            return action
    
    # Fallback strategy: pick the first admissible action mentioned in response
    response_lower = response.lower()
    for action in admissible:
        if action in response_lower:
            return action
    
    # Final default action
    return 'look'