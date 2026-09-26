def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        # On first retry, append extra instructions to guide the model to pick an admissible action.
        return {"extra_instruction": "Ensure to choose one of the listed admissible actions.", "temperature": 0.4}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    return random.choice(admissible)

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    action = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if action:
        action_text = action.group(1).strip().lower()
        if action_text in admissible:
            return action_text
    # Fallback to return any valid action in case of invalid extracted action
    return random.choice(admissible)