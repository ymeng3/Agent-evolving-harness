HISTORY_LENGTH = 10

def format_prompt(prompt: str, state: dict) -> str:
    # Integrate memory feedback into the prompt to guide decision making
    memory_feedback = state.get("memory_feedback", "")
    if memory_feedback:
        prompt += f"\nNote: {memory_feedback}."
    return prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = (
        "Ensure to select an action strictly from the admissible list and avoid repetition."
    )
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Update memory feedback based on the observation state changes
    if action and "successfully" in next_observation:
        state["memory_feedback"] = f"Action '{action}' succeeded. Continue to choose wisely."
    elif "cannot" in next_observation:
        state["memory_feedback"] = f"Reassess the situation, as '{action}' was not effective."