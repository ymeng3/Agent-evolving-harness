HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your previous action wasn't valid. Refer to the admissible actions and make a careful selection."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "attempted_actions" not in state:
        state["attempted_actions"] = set()
    state["attempted_actions"].add(action)

def format_prompt(prompt: str, state: dict) -> str:
    if "attempted_actions" in state and state["attempted_actions"]:
        additional_info = f"\nNote: Previously attempted actions include: {', '.join(state['attempted_actions'])}."
        prompt = prompt.replace("Now it's your turn to take an action.", 
                                f"Now it's your turn to take an action.{additional_info}")
    return prompt