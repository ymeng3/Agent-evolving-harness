HISTORY_LENGTH = 7
TEMPERATURE = 0.5

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'visited_receptacles' not in state:
        state['visited_receptacles'] = set()
    
    # Track visited locations
    if 'You see a ' in next_observation:
        location = next_observation.split('You see a ')[-1].split()[0]
        state['visited_receptacles'].add(location)

def format_prompt(prompt: str, state: dict) -> str:
    visited_receptacles = ', '.join(state.get('visited_receptacles', []))
    if visited_receptacles:
        prompt += f"\nPreviously visited locations: {visited_receptacles}. Avoid unnecessary revisits."
    return prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Focus on the admissible actions provided and choose among them."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None