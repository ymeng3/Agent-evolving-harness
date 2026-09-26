HISTORY_LENGTH = 3

def format_prompt(prompt: str, state: dict) -> str:
    state.setdefault("fallback_triggered", False)
    if state["fallback_triggered"]:
        additional_context = "Consider alternative strategies to avoid repetitive failures."
        prompt += f" <think>{additional_context}</think>"
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re

    action_match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if action_match:
        action = action_match.group(1).strip().lower()
        if action not in admissible:
            state["fallback_triggered"] = True
        else:
            state["fallback_triggered"] = False
        return action
    return admissible[0]

def choose_fallback(admissible: list[str], state: dict) -> str:
    if state.get("fallback_triggered", False):
        state["fallback_triggered"] = False
        for action in admissible:
            if "explore" in action or "look" in action:
                return action
    return "look"