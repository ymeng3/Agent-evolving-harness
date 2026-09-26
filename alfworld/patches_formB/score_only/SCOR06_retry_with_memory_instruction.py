def format_prompt(prompt: str, state: dict) -> str:
    if 'memory_notes' in state:
        memory_instructions = "Here's what you should keep in mind: " + "; ".join(state['memory_notes'])
        prompt += f"\n{memory_instructions}"
    return prompt

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    important_phrases = ["pick", "place", "clean", "heat", "cool", "look"]
    lower_obs = next_observation.lower()
    lower_action = action.lower()

    notes = state.get('memory_notes', [])
    for phrase in important_phrases:
        if phrase in lower_obs or phrase in lower_action:
            notes.append(f"Remember to {phrase} objects when required.")
    
    state['memory_notes'] = list(set(notes))

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        extra_instruction = "Be sure to consider your previous actions and observations;"
        if 'memory_notes' in state:
            extra_instruction += " also consider these notes: " + "; ".join(state['memory_notes'])
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None