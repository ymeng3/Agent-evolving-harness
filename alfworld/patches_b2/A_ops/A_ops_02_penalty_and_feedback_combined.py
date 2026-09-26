HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'action_count' not in state:
        state['action_count'] = {}
    if action not in state['action_count']:
        state['action_count'][action] = 0
    state['action_count'][action] += 1

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    instruction = ""
    if attempt < 2:
        if action in state.get('action_count', {}) and state['action_count'][action] >= 3:
            admissible = [a for a in admissible if a != action]
            instruction += "Avoid repeating actions excessively. "
        instruction += "Focus on the admissible actions provided and choose from them."
        
        # Provide additional feedback to focus reasoning
        if attempt == 1:
            instruction += " Ensure your reasoning process includes all observations."

        if admissible:
            return {"extra_instruction": instruction, "temperature": 0.3}
    return None