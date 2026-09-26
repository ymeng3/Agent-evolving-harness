def format_prompt(prompt: str, state: dict) -> str:
    """
    Modify the prompt to emphasize the importance of detailed and repetitive reasoning
    before selecting an action, aiming to improve the decision-making process.
    """
    if "think_instruction_count" not in state:
        state["think_instruction_count"] = 0

    if state["think_instruction_count"] < 2:
        updated_prompt = prompt.replace(
            "You should first reason step-by-step about the current situation.",
            "You MUST first reason step-by-step, considering previous actions' outcomes, details in observations, and admissible actions."
            " Revisit your reasoning to ensure thorough understanding.")
        state["think_instruction_count"] += 1
        return updated_prompt

    return prompt

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Reset the think_instruction_count after each action for consistent reinforcement across steps.
    """
    state["think_instruction_count"] = 0