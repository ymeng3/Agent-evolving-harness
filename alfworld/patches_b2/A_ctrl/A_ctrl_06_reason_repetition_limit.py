HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'recent_actions' not in state:
        state['recent_actions'] = []

    state['recent_actions'].append(action)
    # Maintain a fixed window of past 5 actions for reason repetition limit
    if len(state['recent_actions']) > 5:
        state['recent_actions'].pop(0)

def format_prompt(prompt: str, state: dict) -> str:
    # Add instruction to avoid reasoning about repeating recent unsuccessful actions
    if 'recent_actions' in state and len(state['recent_actions']) >= 5:
        recent_actions_str = ', '.join(state['recent_actions'])
        additional_instruction = f"\nAvoid considering actions in this list excessively when reasoning: {recent_actions_str}."
        prompt += additional_instruction
    return prompt