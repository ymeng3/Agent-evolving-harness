HISTORY_LENGTH = 10
TEMPERATURE = 0.3

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Initialize or Update the state values.
    if 'steps' not in state:
        state['steps'] = 0
        state['receptacle_revisits'] = collections.defaultdict(int)

    state['steps'] += 1

    # Detect potential revisits; Example assumes a specific format naming for receptacles 
    # (e.g., "in the fridge" or "inside refrigerator").
    receptacles = ['fridge', 'refrigerator', 'drawer', 'cabinet', 'cupboard', 'table', 'shelf', 'counter']
    for receptacle in receptacles:
        if receptacle in observation:
            state['receptacle_revisits'][receptacle] += 1
            break

def format_prompt(prompt: str, state: dict) -> str:
    # Appending state information to the prompt
    revisits_info = ', '.join(f'{k}: {v}' for k, v in state['receptacle_revisits'].items())
    step_info = f"Steps taken so far: {state['steps']}"
    revisits_summary = f"Receptacle revisits: {revisits_info}"
    
    return f"{prompt}\n\n{step_info}\n{revisits_summary}"

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if action in admissible:
        return None

    extra_instruction = (
        f"Observed action: '{action}' is not in the admissible actions list. "
        "Remember to use only the actions provided. Consider revisiting your reasoning."
    )
    
    retry_temperature = TEMPERATURE - 0.05 * attempt
    return {"extra_instruction": extra_instruction, "temperature": retry_temperature}

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Choose a fallback based on least revisits
    revisits_sorted = sorted(state['receptacle_revisits'].items(), key=lambda item: item[1])
    for receptacle, _ in revisits_sorted:
        action = f"examine {receptacle}"
        if action in admissible:
            return action
    return random.choice(admissible)