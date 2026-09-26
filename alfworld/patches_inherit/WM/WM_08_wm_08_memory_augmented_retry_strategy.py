HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if "attempted_actions" not in state:
        state["attempted_actions"] = set()
    
    state["attempted_actions"].add(action)

    if attempt == 1:
        extra_instruction = (
            "Your last action wasn't valid. Focus on selecting one of the admissible actions listed. "
            f"Remember to avoid these previously attempted actions in this step: {', '.join(state['attempted_actions'])}."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        extra_instruction = (
            "Your last action wasn't valid. This is your last retry. Make sure to select one of the admissible actions, "
            "and avoid the following actions which have already been attempted and failed in this step: "
            f"{', '.join(state['attempted_actions'])}."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None