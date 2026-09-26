def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    action = re.search(r'<action>(.*?)</action>', response, re.DOTALL)
    if action:
        action_text = action.group(1).strip().lower()
        return action_text if action_text in admissible else admissible[0]
    return admissible[0]