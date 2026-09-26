HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'visited_locations' not in state:
        state['visited_locations'] = set()
    # Sampling part of the observation to store as a "location tag"
    location_tag = observation[:observation.find('\n')] if '\n' in observation else observation
    state['visited_locations'].add(location_tag.strip().lower())

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prefer using 'look' if available to get more context
    if 'look' in admissible:
        return 'look'
    # Prefer actions that involve new locations if possible
    new_location_actions = [action for action in admissible if not any(loc in action for loc in state.get('visited_locations', []))]
    if new_location_actions:
        return new_location_actions[0]
    return admissible[0]  # Default to the first admissible action if nothing else matches