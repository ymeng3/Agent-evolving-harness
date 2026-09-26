def format_prompt(prompt: str, state: dict) -> str:
    # Offer improved memory feedback integrated into the prompt to assist better decision making
    memory_feedback = state.get("memory_feedback", "")
    if memory_feedback:
        prompt += f"\nReminder: {memory_feedback}"
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            state["memory_feedback"] = f"The action '{action}' was valid and considered successful."
        else:
            state["memory_feedback"] = "Focus on choosing actions from the admissible list."
        return action
    return "look"

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Update memory feedback according to the observed success or need for refinement
    if "completed" in next_observation.lower():
        state["memory_feedback"] = f"The action '{action}' effectively led to task completion."
    elif "blocked" in next_observation.lower():
        state["memory_feedback"] = f"Analyze the goals and methods as '{action}' encountered a challenge."