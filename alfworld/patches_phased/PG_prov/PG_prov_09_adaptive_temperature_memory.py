HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "visited_actions" not in state:
        state["visited_actions"] = set()
    state["visited_actions"].add(action.lower())
    if "temperature" not in state:
        state["temperature"] = TEMPERATURE

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    action_start = response.find("<action>") + len("<action>")
    action_end = response.find("</action>")
    selected_action = response[action_start:action_end].strip().lower()

    if selected_action in admissible:
        state["temperature"] = max(0.3, state["temperature"] * 0.9)
    else:
        state["temperature"] = min(1.0, state["temperature"] * 1.1)

    return selected_action