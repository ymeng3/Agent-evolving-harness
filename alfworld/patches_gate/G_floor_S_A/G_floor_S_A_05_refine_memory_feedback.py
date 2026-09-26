def format_prompt(prompt: str, state: dict) -> str:
    # Add memory feedback to guide the model, but refine it to be more concise and clear.
    memory_feedback = state.get("memory_feedback", "")
    if memory_feedback:
        prompt += f"\nNote: {memory_feedback}"
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            state["memory_feedback"] = "The last action was correct."
        else:
            state["memory_feedback"] = "Choose from the admissible actions list."
        return action
    return ""

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Refine memory update to provide clearer guidance while minimizing verbosity.
    if "successfully" in next_observation:
        state["memory_feedback"] = f"'{action}' was a successful action."
    elif "cannot" in next_observation:
        state["memory_feedback"] = f"Reassess: '{action}' didn't work, check goals and methods."