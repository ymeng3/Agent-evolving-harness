HISTORY_LENGTH = 10

def format_prompt(prompt: str, state: dict) -> str:
    # Add feedback or hints based on previous interactions
    feedback = state.get("feedback", "")
    if feedback:
        prompt += f"\nNote: {feedback}"
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    # Enhanced parsing logic to extract action reliably
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            state["feedback"] = f"The action '{action}' was recognized."
            return action
    # If no valid action, instruct to pay attention to admissible actions
    state["feedback"] = "Make sure to choose from the listed admissible actions."
    return "look"

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Update feedback based on the result of actions
    if "successfully" in next_observation:
        state["feedback"] = "Great job! Continue with similar actions."
    elif "cannot" in next_observation:
        state["feedback"] = "Re-evaluate and adjust your approach."