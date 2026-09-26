from collections import defaultdict

HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'visited_locations' not in state:
        state['visited_locations'] = set()
    # Updating the memory with the current location if the action is 'go to'
    if action.startswith('go to'):
        location = action.split('go to ')[1].strip()
        state['visited_locations'].add(location)

def format_prompt(prompt: str, state: dict) -> str:
    visited = state.get('visited_locations', set())
    visited_info = f"Previously visited locations: {', '.join(visited)}.\n" if visited else ""
    return f"{visited_info}{prompt}"