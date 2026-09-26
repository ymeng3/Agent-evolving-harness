HISTORY_LENGTH = 7

def format_prompt(prompt: str, state: dict) -> str:
    # Reduce redundancy in observations and focus on critical reasoning points
    prompt_sections = prompt.split("\n")
    
    # Extract current observation and task for clarity in reasoning
    task_section = next((s for s in prompt_sections if 'Your task is to:' in s), "")
    current_observation_section = next((s for s in prompt_sections if 'your current observation is:' in s), "")
    admissible_actions_section = next((s for s in prompt_sections if 'Your admissible actions' in s), "")
    
    reasoning_instruction = (
        "Reason about the task step-by-step, focusing only on essential observations and actions that can lead to task completion. "
        "Minimize referencing past actions unless they're directly impactful to the current situation."
    )
    
    formatted_prompt = (
        f"{task_section}\n{current_observation_section}\n"
        f"{admissible_actions_section}\n{reasoning_instruction}"
    )
    
    return formatted_prompt