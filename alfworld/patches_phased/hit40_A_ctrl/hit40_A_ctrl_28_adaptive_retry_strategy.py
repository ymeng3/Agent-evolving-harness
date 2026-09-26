TEMPERATURE = 0.4

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # Extract the action from <action> tags and ensure it is valid
    import re
    action_match = re.search(r"<action>\s*(.*?)\s*</action>", response, re.IGNORECASE)
    if action_match:
        action = action_match.group(1).strip().lower()
        if action in admissible:
            return action
    # If no valid action found, fallback to a default strategy
    return "look"

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Implement a strategy that adapts based on the number of attempts
    if attempt == 1:
        # Provide additional instruction after the first failed attempt
        return {"extra_instruction": "Make sure to select an action from the admissible list provided.", "temperature": 0.45}
    elif attempt == 2:
        # Provide further guidance after the second failed attempt
        return {"extra_instruction": "Choose carefully from the admissible actions. Double-check your reasoning.", "temperature": 0.35}
    return None