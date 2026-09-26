HISTORY_LENGTH = 10

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'visited' not in state:
        state['visited'] = set()
    state['visited'].update(observation.lower().split())

def format_prompt(prompt: str, state: dict) -> str:
    if 'visited' in state and state['visited']:
        visited_info = ", ".join(list(state['visited']))
        prompt += f"\nRemember these visited items or places: {visited_info}."
    return prompt