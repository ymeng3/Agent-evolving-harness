HISTORY_LENGTH = 6

def format_prompt(prompt: str, state: dict) -> str:
    """
    Enhance the prompt with explicit instructions and task reminders to minimize confusion.
    """
    if 'task_reminder' not in state:
        task_description = prompt.split("Your task is to: ")[1].split("\n")[0]  # Extract task description
        state['task_reminder'] = task_description
    if 'step_count_reminder' not in state:
        state['step_count_reminder'] = 0

    # Include task and step reminders in the prompt
    task_reminder = state['task_reminder']
    step_reminder = state['step_count_reminder']
    updated_prompt = f"\nTask reminder: {task_reminder}. Total steps taken on this task: {step_reminder}."
    state['step_count_reminder'] += 1

    return prompt + updated_prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            state["action_guide"] = action  # Update guidance with admissible actions only
            return action
    # When no action found or parsed incorrectly, suggest an observation action strategy
    if any(obs_action in admissible for obs_action in ['look', 'examine']):
        return "look"
    return admissible[0]  # Fallback to the first admissible action

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Track successful actions for potential future guidance.
    """
    if 'action_success' not in state:
        state['action_success'] = []
    if "successfully" in next_observation:
        state['action_success'].append(action)
        state['action_guide'] = action if len(state['action_success']) > 3 else ""

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Adjust retry mechanism for cases where unclear task understanding caused action errors.
    """
    if attempt == 1:
        extra_instruction = (
            "The task requires careful consideration of admissible options. Remember recent action successes."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2:
        extra_instruction = (
            "Prioritize clear choices among admissible actions, recalling task objectives."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None