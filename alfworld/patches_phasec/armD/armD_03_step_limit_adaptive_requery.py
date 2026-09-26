HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Idea: Add re-query mechanism when inadmissible actions are encountered
    # to assist in completing tasks that otherwise would fail by hitting the step limit.
    if attempt <= 2:
        return {"extra_instruction": "Please confirm the selection and choose a correct admissible action.", 
                "temperature": TEMPERATURE - 0.1 * attempt}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Track repeated actions to prevent iterations and unnecessary step consumption.
    if "recent_actions" not in state:
        state["recent_actions"] = []
    state["recent_actions"].append(action)
    if len(state["recent_actions"]) > 3:
        state["recent_actions"].pop(0)
    # Check for three-in-a-row repeats and attempt to adjust course if detected.
    if state["recent_actions"][-3:] == [action] * 3:
        state["adjust_in_progress"] = True
    else:
        state["adjust_in_progress"] = False

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Act wisely based on the recent action history when in a fallback scenario.
    if state.get("adjust_in_progress", False):
        # Pick a less common recent action to break out of repetition loops.
        recent_counts = {action: state["recent_actions"].count(action) for action in admissible}
        sorted_actions = sorted(recent_counts, key=recent_counts.get)
        return sorted_actions[0] if sorted_actions else "look"
    return "look"