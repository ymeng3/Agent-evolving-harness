HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        # Before the second retry, let's check how often the agent chose successfully from recent actions
        recent_actions = state.get("recent_valid_actions", [])
        action_choice_confidence = sum(1 for a in recent_actions if a in admissible) / (len(recent_actions) or 1)
        temperature_adjustment = 0.0 if action_choice_confidence > 0.5 else 0.1
        return {"extra_instruction": extra_instruction, "temperature": 0.2 + temperature_adjustment}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Update state with recent valid actions
    state.setdefault("recent_valid_actions", []).append(action)
    # Trim to keep the most recent 5 actions in memory
    if len(state["recent_valid_actions"]) > 5:
        state["recent_valid_actions"].pop(0)