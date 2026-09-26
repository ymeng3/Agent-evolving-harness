HISTORY_LENGTH = 10

def format_prompt(prompt: str, state: dict) -> str:
    """
    Insert specific patterns or historical context when constructing the prompt.
    """
    action_guide = state.get("action_guide", "")
    if action_guide:
        prompt += f"\nNote: Reflect on prior successful actions when deciding."
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            state["action_guide"] = action
            return action
    return "examine"

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Update state post each action with potentially useful information.
    """
    if "success" in next_observation.lower():
        state['action_guide'] = action

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Modify the retry strategy based on past successful retries and history context.
    """
    if attempt == 1:
        extra_instruction = (
            "Recall successful actions and deliberately choose an admissible option."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2:
        extra_instruction = (
            "Review the extended history to align your choice with past successes."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None