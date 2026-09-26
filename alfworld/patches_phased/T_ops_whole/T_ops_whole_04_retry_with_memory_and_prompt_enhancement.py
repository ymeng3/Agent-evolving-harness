HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus specifically on the goals given in the task, and be sure to choose from the list of admissible actions."
    if attempt == 1:
        if "retry_count" not in state:
            state["retry_count"] = 0
        state["retry_count"] += 1
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "retry_count" in state:
        state["retry_count"] = 0  # Reset after a valid action
    if "actions_taken" not in state:
        state["actions_taken"] = []
    state["actions_taken"].append(action)
    state["last_observation"] = next_observation

def format_prompt(prompt: str, state: dict) -> str:
    if "retry_count" in state and state["retry_count"] > 0:
        failure_advice = "You're having difficulty selecting a valid action. Reflect on what actions you've tried and focus on the task goals."
        prompt += f"\n<note>{failure_advice}</note>"
    return prompt