HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def format_prompt(prompt: str, state: dict) -> str:
    history = state.get("history", [])
    num_invalid_actions = state.get("num_invalid_actions", 0)

    # Count invalid actions to adjust temperature dynamically
    if num_invalid_actions > 5:
        state["adaptive_temperature"] = 0.3
    else:
        state["adaptive_temperature"] = 0.5

    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re

    # Extract action from <action></action> tags
    match = re.search(r'<action>(.*?)</action>', response)
    action = match.group(1).strip().lower() if match else 'look'

    # Track invalid actions to adapt prompt temperature
    if action not in admissible:
        state['num_invalid_actions'] = state.get('num_invalid_actions', 0) + 1

    return action

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if action not in admissible:
        temperature = state.get("adaptive_temperature", TEMPERATURE)
        if attempt < 3:
            extra_instruction = (
                "Ensure your chosen action matches one from the list of admissible actions."
            )
            return {"extra_instruction": extra_instruction, "temperature": temperature}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "history" not in state:
        state["history"] = []

    state["history"].append((observation, action))
    state["history"] = state["history"][-HISTORY_LENGTH:]

def choose_fallback(admissible: list[str], state: dict) -> str:
    return random.choice(admissible)