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
    # Enhance the prompt generation by embedding step failure awareness
    failure_msg = f" You have made {state.get('invalid_steps', 0)} invalid attempts so far."
    task_instruction_end_idx = prompt.find(". Below are the most recent")
    prompt = prompt[:task_instruction_end_idx] + failure_msg + prompt[task_instruction_end_idx:]
    return prompt

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Update memory with invalid step count information
    if 'invalid_steps' not in state:
        state['invalid_steps'] = 0
    
    state['invalid_steps'] += 1 if observation == next_observation else 0