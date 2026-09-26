TEMPERATURE = 0.5

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    def extract_action(text: str) -> str:
        # Attempt to extract the first action enclosed in <action> tags
        action_match = re.search(r"<action>\s*(.*?)\s*</action>", text, re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip().lower()
            if action in admissible:
                return action
        
        # If extraction fails, try to find the action directly in the text
        for action in admissible:
            if action in text.lower():
                return action
        
        # Default to 'look' if no action is found
        return "look"

    return extract_action(response)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Ensure your action is from the admissible list, considering the context."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None