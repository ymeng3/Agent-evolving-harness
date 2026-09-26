HISTORY_LENGTH = 7
TEMPERATURE = 0.4

def format_prompt(prompt: str, state: dict) -> str:
    # Allow some history to observe patterns but not overwhelm the LLM
    first_part = prompt.split("You are now at step")[0]
    second_part = prompt.split("Now it's your turn to take an action.")[1]
    refined_task_instruction = "Consider the task carefully and make an optimal decision."
    return f"{first_part} {refined_task_instruction}\nYou are now at step{second_part}"

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Concentrate on the task and only select from the listed valid actions."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.35}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None