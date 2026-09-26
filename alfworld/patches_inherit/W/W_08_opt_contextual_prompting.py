HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def format_prompt(prompt: str, state: dict) -> str:
    state.setdefault('missteps', 0)
    state.setdefault('task_type', None)
    
    # Extracting task type if not already done
    if state['task_type'] is None:
        task_type_keywords = ['look at', 'pick and place', 'pick clean', 'pick cool', 'pick heat', 'pick two objects']
        for keyword in task_type_keywords:
            if keyword in prompt.lower():
                state['task_type'] = keyword
                break
    
    # Enhancing the prompt with contextual cues based on the task type
    if state['task_type']:
        prompt += f"\nThink about the typical actions needed for the {state['task_type']} task."
    
    return prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    state['missteps'] += 1
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None