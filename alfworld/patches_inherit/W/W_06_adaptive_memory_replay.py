HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "action_log" not in state:
        state["action_log"] = collections.deque(maxlen=10)
    state["action_log"].append((observation, action, next_observation))

def format_prompt(prompt: str, state: dict) -> str:
    if state.get("action_log"):
        past_actions = "Past useful actions in similar contexts: " + "; ".join([
            f"Obs: {obs} -> Act: {act} -> Next: {next_obs}"
            for obs, act, next_obs in state["action_log"]
        ])
        prompt += "\n" + past_actions
    return prompt