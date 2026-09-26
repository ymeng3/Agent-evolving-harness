HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def format_prompt(prompt: str, state: dict) -> str:
    action_suggestions = ""
    if "recent_actions" in state:
        recent_actions = state["recent_actions"]
        if recent_actions:
            action_suggestions = " Based on your recent successful actions: " + ", ".join(recent_actions[-3:]) + "."
    return prompt + action_suggestions

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "recent_actions" not in state:
        state["recent_actions"] = []
    if action in state.get("recent_actions", []):
        state["recent_actions"].remove(action)  # Remove duplicate
    state["recent_actions"].append(action)
    # Keep only the last 5 actions for context
    if len(state["recent_actions"]) > 5:
        state["recent_actions"].pop(0)