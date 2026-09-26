def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'prior_actions' not in state:
        state['prior_actions'] = []
    state['prior_actions'].append(action)

    # Maintain a memory size limit to prevent excessive growth
    max_memory_size = 10
    if len(state['prior_actions']) > max_memory_size:
        state['prior_actions'].pop(0)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = "Focus on admissible actions and avoid repeating the same actions. "
        if state.get('prior_actions'):
            prior_action_set = set(state['prior_actions'])
            prior_actions_subtext = ", ".join(prior_action_set)
            extra_instruction += f"You have previously tried: {prior_actions_subtext}. "
        
        return {
            "extra_instruction": extra_instruction,
            "temperature": 0.35 if attempt == 1 else 0.3
        }
    return None