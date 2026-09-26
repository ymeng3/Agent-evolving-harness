HISTORY_LENGTH = 0
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction_base = "Your previous action wasn't valid. Carefully choose from the admissible actions listed only."
    if attempt == 1:
        return {"extra_instruction": extra_instruction_base + " Think carefully about why the previous choice might have been invalid.", "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction_base + " Prioritize the actions that advance the task step effectively.", "temperature": 0.25}
    return None

def format_prompt(prompt: str, state: dict) -> str:
    filtered_prompt = prompt.replace("Prior to this step, you have already taken {step_count} step(s). Below are the most recent {history_length} observations and the corresponding actions you took: {action_history}", 
                                     "")
    return filtered_prompt

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "last_action" not in state:
        state["last_action"] = None
    state["last_action"] = action