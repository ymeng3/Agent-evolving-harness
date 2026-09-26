HISTORY_LENGTH = 8
TEMPERATURE = 0.35

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Remember to select only from the list of admissible actions provided."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": TEMPERATURE - 0.05}
    return None

import re
from collections import defaultdict

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

    return extract_action(response)

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "visited" not in state:
        state["visited"] = defaultdict(int)
    state["visited"][next_observation] += 1
    state["last_action"] = action

def choose_fallback(admissible: list[str], state: dict) -> str:
    last_action = state.get("last_action", None)
    for action in admissible:
        if action != last_action:
            return action
    return admissible[0]