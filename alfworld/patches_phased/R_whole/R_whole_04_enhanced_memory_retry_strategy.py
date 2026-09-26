HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Study the environment and focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "actions_taken" not in state:
        state["actions_taken"] = []
    state["actions_taken"].append(action)

    if len(state["actions_taken"]) > 5:
        recent_actions = state["actions_taken"][-5:]
        repeats = {a for a in recent_actions if recent_actions.count(a) > 1}
        if repeats:
            state["likely_loop"] = True
        else:
            state["likely_loop"] = False
    else:
        state["likely_loop"] = False

def format_prompt(prompt: str, state: dict) -> str:
    if state.get("likely_loop"):
        return prompt + "\nNote: You seem to be repeating actions. Consider new strategies to progress."
    return prompt