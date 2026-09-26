HISTORY_LENGTH = 8

def format_prompt(prompt: str, state: dict) -> str:
    # Ensure the prompt includes directions for consistent actions
    if 'last_success_action' in state:
        reminder = f"Remember that previously successful actions include: {state['last_success_action']}."
    else:
        reminder = ""
    return f"{prompt}\n{reminder}"

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Keep track of successful actions
    if "success" in next_observation:
        state['last_success_action'] = action