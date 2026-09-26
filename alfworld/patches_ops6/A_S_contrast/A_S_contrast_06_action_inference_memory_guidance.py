HISTORY_LENGTH = 8
TEMPERATURE = 0.4

def format_prompt(prompt: str, state: dict) -> str:
    """
    Extend the prompt with previous successful actions and mention reasoning process explicitly.
    """
    actions_to_consider = ', '.join(state.get("successful_actions", []))
    action_guide = f"\nSuccessful actions to consider: {actions_to_consider}" if actions_to_consider else ""
    reasoning_guide = "\nRemember to reason step-by-step considering current observation and admissible actions."
    return f"{prompt}{action_guide}{reasoning_guide}"

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    action = match.group(1).strip().lower() if match else "look"
    return action if action in admissible else "look"

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Record successful actions for future guidance and detect loop situations.
    """
    if 'successful_actions' not in state:
        state['successful_actions'] = []
    if "successfully" in next_observation and action not in state['successful_actions']:
        state['successful_actions'].append(action)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Reinforce step-by-step reasoning and focus on admissible actions on retries.
    """
    reasoning_reminder = "Ensure your reasoning process is step-by-step and choose an admissible action."
    instructions = "Recall previous successes and integrate them in your reasoning." if attempt == 1 else reasoning_reminder
    return {"extra_instruction": instructions, "temperature": max(0.1, 0.4 - 0.1 * attempt)}

def choose_fallback(admissible: list[str], state: dict) -> str:
    """
    Default to 'look' to gather more information if uncertain.
    """
    return "look"