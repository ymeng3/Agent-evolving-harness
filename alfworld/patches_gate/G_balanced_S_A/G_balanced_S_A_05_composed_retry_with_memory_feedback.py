HISTORY_LENGTH = 7
TEMPERATURE = 0.4

def format_prompt(prompt: str, state: dict) -> str:
    # Add a memory feedback to the prompt to guide the agent better
    memory_feedback = state.get("memory_feedback", "")
    if memory_feedback:
        prompt += f"\nRemember: {memory_feedback}."
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            state["memory_feedback"] = f"Action '{action}' was successful."
        else:
            state["memory_feedback"] = f"Remember to pick actions from the admissible list."
        return action
    return ""

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Combine retry strategy with memory feedback to improve action selection accuracy.
    """
    extra_instruction = (
        "Your previous action was not admissible."
        " Ensure your selected action is one of the admissible actions."
        " Reason carefully and ensure you're considering the environment context."
    )
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": "Focus on the admissible actions provided and choose from them.", "temperature": 0.25}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Store a feedback in memory depending on the success or refinement needed
    if "successfully" in next_observation:
        state["memory_feedback"] = f"The action '{action}' was effective. Keep up similar efforts."
    elif "cannot" in next_observation:
        state["memory_feedback"] = f"Re-evaluate the objectives or method, the last action '{action}' didn't work as expected."