HISTORY_LENGTH = 6
TEMPERATURE = 0.4

def format_prompt(prompt: str, state: dict) -> str:
    action_guide = state.get("action_guide", "")
    if action_guide:
        prompt += f"\nNote: Consider actions similar to previous successes: {action_guide}."
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
    if 'action_success' not in state:
        state['action_success'] = []
    if "successfully" in next_observation:
        state['action_success'].append(action)
        state['action_guide'] = action if len(state['action_success']) > 3 else ""

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Adjust temperature only slightly and refine instructions to improve retries.
    """
    if attempt == 1:
        extra_instruction = (
            "Recall previous actions similar to successful ones. Select from admissible options."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.45}
    elif attempt == 2:
        extra_instruction = (
            "Focus on choosing an action aligned with past successes from admissible options."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.42}
    return None