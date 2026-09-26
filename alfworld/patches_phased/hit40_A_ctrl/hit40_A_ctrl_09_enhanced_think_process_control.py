TEMPERATURE = 0.4
HISTORY_LENGTH = 5

def format_prompt(prompt: str, state: dict) -> str:
    # Enhance the thinking process by injecting specifics about the task
    task_details = state.get("task_details", "")
    enhanced_prompt = f"{prompt}\nKeep in mind specific task details: {task_details}. Ensure clarity in reasoning and action."
    return enhanced_prompt

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'task_details' not in state:
        # Extract relevant task-related details from the initial observation and store them
        if 'cleaning' in observation:
            state['task_details'] = 'Focus on cleaning objects before placing.'
        elif 'cooling' in observation:
            state['task_details'] = 'Focus on cooling objects before placing.'
        elif 'heating' in observation:
            state['task_details'] = 'Focus on heating objects before placing.'
        elif 'look for' in observation:
            state['task_details'] = 'Focus on finding and looking at objects.'
        elif 'pick two' in observation:
            state['task_details'] = 'Ensure picking and placing two objects.'
        else:
            state['task_details'] = 'Follow the instructions for item handling.'

    # Store last action results to notice specific feedback
    successful_clues = ['success', 'completed', 'correct']
    if any(clue in next_observation.lower() for clue in successful_clues):
        state['last_successful_action'] = action