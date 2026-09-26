def format_prompt(prompt: str, state: dict) -> str:
    # Adjust verbosity based on success and failure in past actions
    if 'verbosity_control' not in state:
        state['verbosity_control'] = 0

    if state['verbosity_control'] > 2:
        # Reduce verbosity if previous attempts indicate successful understanding with less feedback
        reduced_prompt = prompt.replace(
            "You should first reason step-by-step about the current situation. This reasoning process MUST be enclosed within <think> </think> tags.",
            "Think about the current situation within <think> tags."
        ).replace(
            "Once you've finished your reasoning, you should choose an admissible action for current step and present it within <action> </action> tags.",
            "Choose an admissible action within <action> tags."
        )
        return reduced_prompt
    else:
        # Use default verbosity
        return prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        state['verbosity_control'] += 1
        return {"extra_instruction": "Focus carefully on the admissible actions."}
    return None