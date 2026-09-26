TEMPERATURE = 0.5  # Start with a slightly higher temperature for exploration

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """Update the state with useful memory feedback."""
    if 'memory_feedback' not in state:
        state['memory_feedback'] = ""

    if 'successfully' in next_observation:
        state['memory_feedback'] = f"Action '{action}' worked well."
    elif 'cannot' in next_observation:
        state['memory_feedback'] = f"The action '{action}' was not effective. Consider other options."

def format_prompt(prompt: str, state: dict) -> str:
    """Add memory feedback to the prompt for guidance."""
    memory_feedback = state.get("memory_feedback", "")
    if memory_feedback:
        prompt += f"\nNote: {memory_feedback}"
    return prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """Adjust temperature and prompt on retry based on previous failures."""
    extra_instruction = "Your previous action was not admissible, consider your past actions and memory feedback."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None