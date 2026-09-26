HISTORY_LENGTH = 6

def format_prompt(prompt: str, state: dict) -> str:
    """
    Extend the prompt with more structured guidance on the next best action using past successes.
    """
    action_guide = state.get("action_guide", [])
    if action_guide:
        guide_context = ", ".join(action_guide[-2:])
        prompt += f"\nNote: Recent successful actions to consider: {guide_context}."
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            return action
    # Default fallback action when no valid action is found
    return "examine"

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Update the state with more detailed tracking of successful actions.
    """
    if 'action_success' not in state:
        state['action_success'] = []
    if "successfully" in next_observation and action not in state['action_success']:
        state['action_success'].append(action)
        state['action_guide'] = state['action_success'][-3:] # keep the three most recent successful actions

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Introduce clearer and simplified additional instructions on retries.
    """
    if attempt == 1:
        extra_instruction = (
            "Recall recent successes. Prioritize choosing from admissible options."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2:
        extra_instruction = (
            "Focus on earlier successful actions that fit within admissible options."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None