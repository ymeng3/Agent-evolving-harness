HISTORY_LENGTH = 15

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {"extra_instruction": "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."}
    elif attempt == 2:
        return {"extra_instruction": "Refocus and take a closer look at your options. Make sure to choose from the admissible actions given."}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "visited" not in state:
        state["visited"] = set()
    state["visited"].add(observation)

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    action_content = response.lower()
    action_start = action_content.find("<action>") + len("<action>")
    action_end = action_content.find("</action>")
    if 0 <= action_start < action_end:
        action = action_content[action_start:action_end].strip()
        if action in admissible:
            return action

    fallback_action = next((a for a in admissible if "look around" in a), admissible[0])
    if state.get("visited") and state["visited"]:
        fallback_action = next((a for a in admissible if "look" in a and a not in state["visited"]), fallback_action)
    return fallback_action