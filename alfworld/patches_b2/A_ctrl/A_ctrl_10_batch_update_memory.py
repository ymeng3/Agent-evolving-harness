HISTORY_LENGTH = 8

def format_prompt(prompt: str, state: dict) -> str:
    memory_notes = state.get("memory_notes", [])
    if memory_notes:
        notes = " ".join(memory_notes[-3:])  # Include the last three memory notes
        prompt += f"\nMemory Notes: {notes}."
    return prompt

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Batch update memory based on significant action-outcome patterns
    if 'memory_notes' not in state:
        state['memory_notes'] = []

    significant_terms = ['successful', 'failed', 'blocked', 'acquired']
    if any(term in next_observation.lower() for term in significant_terms):
        note = f"Action '{action}' led to '{next_observation}'."
        state['memory_notes'].append(note)
        if len(state['memory_notes']) > 20:  # Keep the memory size reasonable
            state['memory_notes'].pop(0)