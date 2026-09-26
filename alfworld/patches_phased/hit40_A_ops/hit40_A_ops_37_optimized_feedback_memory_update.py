HISTORY_LENGTH = 7

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Store feedback based on the effectiveness of actions taken.
    success_indicators = ["successfully", "managed", "completed", "achieved"]
    failure_indicators = ["cannot", "failed", "stuck", "unsuccessful"]
    
    if any(word in next_observation.lower() for word in success_indicators):
        state["memory_feedback"] = f"The action '{action}' was effective. Continue similar actions."
    elif any(word in next_observation.lower() for word in failure_indicators):
        state["memory_feedback"] = f"The action '{action}' was ineffective. Consider alternative actions."
    else:
        state["memory_feedback"] = None

def format_prompt(prompt: str, state: dict) -> str:
    # Add memory feedback to the prompt to guide decision-making process.
    memory_feedback = state.get("memory_feedback")
    if memory_feedback:
        prompt += f"\nFeedback: {memory_feedback}"
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action not in admissible:
            # Providing context if the selected action is not admissible
            state["memory_feedback"] = f"Action '{action}' isn't viable. Choose from admissible actions."
        return action
    return ""