HISTORY_LENGTH = 10

def format_prompt(prompt: str, state: dict) -> str:
    # Adjusting the prompt to explicitly guide the agent to pay more attention to specific task goals and correct actions.
    task_focus_instruction = "\nBe sure to focus on the specific task goals while selecting actions."
    action_focus_instruction = "\nEnsure your action selection aligns closely with the task requirements."
    return prompt + task_focus_instruction + action_focus_instruction

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None