HISTORY_LENGTH = 7
TEMPERATURE = 0.5

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'visited_receptacles' not in state:
        state['visited_receptacles'] = set()
    
    # Check if the action was to open or look into a receptacle
    if any(keyword in action for keyword in ['open', 'look', 'close']):
        state['visited_receptacles'].add(action)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = "Your previous action was not admissible. "
        
        # Suggest avoiding recently visited locations
        visited = state.get('visited_receptacles', set())
        if visited:
            extra_explanations = f"Avoid these recently visited actions: {', '.join(visited)}."
            extra_instruction += extra_explanations

        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None