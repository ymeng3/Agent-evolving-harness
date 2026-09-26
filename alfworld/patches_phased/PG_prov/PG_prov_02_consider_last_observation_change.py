HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    state.setdefault('observations', []).append((observation, action, next_observation))
    if len(state['observations']) > HISTORY_LENGTH:
        state['observations'].pop(0)

def format_prompt(prompt: str, state: dict) -> str:
    recent_obs_change = "none"
    if state['observations']:
        last_obs, last_action, last_next_obs = state['observations'][-1]
        if last_obs != last_next_obs:
            recent_obs_change = f"From '{last_obs}' to '{last_next_obs}' due to action '{last_action}'."
    return f"{prompt}\nRecent observation change: {recent_obs_change}"

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None