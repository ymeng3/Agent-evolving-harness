import re

HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    def extract_action(text: str) -> str:
        action_match = re.search(r"<action>\s*(.*?)\s*</action>", text, re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip().lower()
            if action in admissible:
                return action
        
        for action in admissible:
            if action in text.lower():
                return action
        
        return "look"

    extracted_action = extract_action(response)
    state.setdefault("action_memory", []).append(extracted_action)
    return extracted_action

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        recent_actions = state.get("action_memory", [])[-3:]
        recent_action_str = ", ".join(recent_actions)
        extra_instruction = (
            f"The previous action '{action}' was not admissible."
            f" Avoid repeating recent actions: {recent_action_str}."
            " Carefully choose from the list of admissible actions."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None