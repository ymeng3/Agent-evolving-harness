HISTORY_LENGTH = 5

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'current_episode_actions' not in state:
        state['current_episode_actions'] = []
    state['current_episode_actions'].append(action)

    success_keywords = ["completed", "successful", "achieved"]
    failure_keywords = ["failed", "unsuccessful", "retry"]

    adjustment_window = 5
    successful_actions = sum(any(kw in obs for kw in success_keywords) for obs in state['current_episode_actions'][-adjustment_window:])
    failure_actions = sum(any(kw in obs for kw in failure_keywords) for obs in state['current_episode_actions'][-adjustment_window:])

    if successful_actions > failure_actions:
        state['history_length_adjustment'] = max(2, len(state['current_episode_actions']) // 10)
    elif successful_actions < failure_actions:
        state['history_length_adjustment'] = min(10, len(state['current_episode_actions']) // 5)
    else:
        state['history_length_adjustment'] = HISTORY_LENGTH

def format_prompt(prompt: str, state: dict) -> str:
    adjusted_history = state.get('history_length_adjustment', HISTORY_LENGTH)
    prompt_lines = prompt.split("\n")
    
    for i, line in enumerate(prompt_lines):
        if 'most recent' in line:
            prompt_lines[i] = line.replace(f"{HISTORY_LENGTH}", f"{adjusted_history}")

    formatted_prompt = "\n".join(prompt_lines)
    return formatted_prompt