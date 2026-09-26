HISTORY_LENGTH = 10
TEMPERATURE = 0.5

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
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        specific_instruction = (
            f"Consider previous successful actions: {state.get('action_guide', 'none')}."
        )
        return {"extra_instruction": specific_instruction + " " + extra_instruction, "temperature": 0.4}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None