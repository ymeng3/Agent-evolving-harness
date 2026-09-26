HISTORY_LENGTH = 10
TEMPERATURE = 0.3

def format_prompt(prompt: str, state: dict) -> str:
    lines = prompt.split("\n")
    
    enhanced_task_detail_prompt = "Pay special attention to the task requirements and recently taken actions to ensure progress."
    
    for idx, line in enumerate(lines):
        if "Your task is to:" in line:
            lines.insert(idx + 1, enhanced_task_detail_prompt)
            break
    
    return "\n".join(lines)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Reminder: Your last action wasn't valid. Please focus on the task requirements and select one of the admissible actions."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None