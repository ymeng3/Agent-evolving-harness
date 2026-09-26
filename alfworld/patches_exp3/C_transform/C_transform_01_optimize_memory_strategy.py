HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'visited_receptacles' not in state:
        state['visited_receptacles'] = set()
    if 'repeated_actions' not in state:
        state['repeated_actions'] = {}

    # Update visited receptacles based on observation
    receptacle_match = re.search(r"on the (\w+)", observation, re.IGNORECASE)
    if receptacle_match:
        state['visited_receptacles'].add(receptacle_match.group(1).lower())

    # Track repeated actions
    if action not in state['repeated_actions']:
        state['repeated_actions'][action] = 0
    state['repeated_actions'][action] += 1

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = "The previous action was invalid. "

        # Guide to avoid repeating the same action and revisiting receptacles
        if state['repeated_actions'].get(action, 0) >= 3:
            extra_instruction += "You've repeated the same action multiple times. Consider exploring other options. "

        # Suggest to explore unvisited receptacles if that seems like a bottleneck
        unvisited = [a for a in admissible if a.split()[-1] not in state['visited_receptacles']]
        if unvisited:
            extra_instruction += f"Consider actions like {unvisited} to explore new areas. "
        
        return {"extra_instruction": extra_instruction, "temperature": 0.35}
    return None