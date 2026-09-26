HISTORY_LENGTH = 7
TEMPERATURE = 0.45

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "The action you chose was not valid. Please ensure your action matches one of the admissible actions given."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.35}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.25}
    return None

def format_prompt(prompt: str, state: dict) -> str:
    from collections import deque
    max_history_length = HISTORY_LENGTH
    if 'action_history' not in state:
        state['action_history'] = deque(maxlen=max_history_length)
    if 'observation_history' not in state:
        state['observation_history'] = deque(maxlen=max_history_length)

    # Extract current parts of the prompt
    parts = prompt.splitlines()
    task_description = parts[0]
    step_count = int(parts[1].split()[-1].split('(')[0])
    
    # Update history state
    if step_count > 0:
        current_observation = parts[-2]
        last_action = parts[-3].split(':')[-1].strip()
        state['observation_history'].append(current_observation)
        state['action_history'].append(last_action)

    # Create new action history prompt
    action_history_prompt = ""
    for obs, act in zip(state['observation_history'], state['action_history']):
        action_history_prompt += f"Observation: {obs} | Action: {act}\n"

    # Update the prompt with shortened history
    return f"{task_description}\nYou have taken {step_count} step(s). Below are the most recent {len(state['action_history'])} observations and actions:\n{action_history_prompt}{parts[-2]}\n{parts[-1]}"