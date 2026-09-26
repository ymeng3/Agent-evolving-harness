HISTORY_LENGTH = 10

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    # Action extraction using <action> tags or direct matching
    def extract_action(text: str) -> str:
        action_match = re.search(r"<action>\s*(.*?)\s*</action>", text, re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip().lower()
            if action in admissible:
                return action
        # Attempt to match actions directly from the text
        for action in admissible:
            if action in text.lower():
                return action
        return "look"
    return extract_action(response)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Please choose an action from the provided admissible actions."
    if attempt < 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None