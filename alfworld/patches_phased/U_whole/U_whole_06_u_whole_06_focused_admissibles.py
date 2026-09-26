HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = (
        "Your last action wasn't valid. Focus on selecting one of the admissible actions which are perfectly aligned "
        "with the task. Re-assess the task requirements and recent observations, and try again."
    )
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def format_prompt(prompt: str, state: dict) -> str:
    # Enhance prompt formatting to improve action selection focus.
    def clean_history(history_str):
        history_lines = history_str.strip().split('\n')
        relevant_history = "\n".join(history_lines[-HISTORY_LENGTH:])
        return relevant_history
    
    def relevant_admissible_tasks(admissible, task_description):
        keywords = task_description.split()
        return [action for action in admissible if any(keyword in action for keyword in keywords)]
    
    task_desc_marker = "Your task is to:"
    task_start = prompt.index(task_desc_marker) + len(task_desc_marker)
    task_end = prompt.index("\n", task_start)
    task_description = prompt[task_start:task_end].strip()
    
    admissible_start = prompt.index("Your admissible actions of the current situation are: [")
    admissible_end = prompt.index("].", admissible_start) + 1
    admissible_actions_section = prompt[admissible_start:admissible_end]
    
    current_admissible_actions = prompt[admissible_start + len("Your admissible actions of the current situation are: [") : admissible_end - 1].split(", ")
    relevant_admissible_actions = relevant_admissible_tasks(current_admissible_actions, task_description)
    
    prompt = (
        prompt[:admissible_start]
        + admissible_actions_section.replace(
            ", ".join(current_admissible_actions), ", ".join(relevant_admissible_actions)
        )
        + prompt[admissible_end:]
    )
    
    action_history_marker = "Below are the most recent"
    action_history_start = prompt.index(action_history_marker)
    action_history_end = prompt.index("Your admissible actions of the current situation are: [")
    action_history_section = prompt[action_history_start:action_history_end]
    
    cleaned_action_history = clean_history(action_history_section)
    
    prompt = (
        prompt[:action_history_start]
        + cleaned_action_history
        + prompt[action_history_end:]
    )
    
    return prompt