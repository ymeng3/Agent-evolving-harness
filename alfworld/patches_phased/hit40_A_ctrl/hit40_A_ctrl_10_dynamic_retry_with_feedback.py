HISTORY_LENGTH = 6

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    # Extract action from model response
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    action = match.group(1).strip().lower() if match else ""
    state['last_action'] = action
    return action if action in admissible else "look"

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Update history of actions and consequences
    if 'seen_observations' not in state:
        state['seen_observations'] = set()
    state['seen_observations'].add(observation)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {"extra_instruction": "Recall prior steps and refocus on the given task requirements."}
    if attempt == 2:
        return {"extra_instruction": f"Previous action '{state['last_action']}' was inadmissible. Reassess based on newly seen state. Pick from admissible: {', '.join(admissible)}."}
    return None

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Avoid repeating inadmissible action
    chosen = admissible[0] if state['last_action'] not in admissible else "look"
    return chosen