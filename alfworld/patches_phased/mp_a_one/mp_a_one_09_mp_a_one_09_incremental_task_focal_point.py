HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def format_prompt(prompt: str, state: dict) -> str:
    if "initial_info" not in state:
        start_index = prompt.find("Your task is to:")
        end_index = prompt.find("Prior to this step")
        task_info = prompt[start_index:end_index]
        state["initial_info"] = task_info
    return f"{state['initial_info']} {prompt}"