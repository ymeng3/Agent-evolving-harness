HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'locations' not in state:
        state['locations'] = {}
    for line in observation.split('\n'):
        if 'object:' in line and 'location:' in line:
            parts = line.split('location:')
            obj = parts[0].split('object:')[-1].strip().lower()
            loc = parts[1].strip().lower()
            state['locations'][obj] = loc
    if 'last_action' not in state:
        state['last_action'] = ''
    state['last_action'] = action

def format_prompt(prompt: str, state: dict) -> str:
    if 'last_action' in state and state['last_action']:
        prompt += f"\nRemember, your last action was: {state['last_action']}."
    if state.get('locations'):
        remembered_info = "Objects and their known locations: " + ", ".join([f"{obj} in {loc}" for obj, loc in state['locations'].items()])
        prompt += f"\n{remembered_info}"
    return prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = "The previous action was inadmissible."
        if 'locations' in state and len(state['locations']) > 0:
            known_objects = ", ".join(state['locations'].keys())
            extra_instruction += f" You have information on these objects: {known_objects}."
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None