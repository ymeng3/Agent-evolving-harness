HISTORY_LENGTH = 10

def format_prompt(prompt: str, state: dict) -> str:
    state.setdefault('step_count', 0)
    step_line = f"\nCurrent total steps taken so far in this episode: {state['step_count']}."
    prompt = prompt.replace("\nNow it's your turn", step_line + "\nNow it's your turn")
    return prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    state['step_count'] += 1