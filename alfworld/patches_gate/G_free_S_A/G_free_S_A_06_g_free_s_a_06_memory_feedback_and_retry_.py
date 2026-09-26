HISTORY_LENGTH = 7

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            state["memory_feedback"] = f"Action '{action}' was successful."
        else:
            state["memory_feedback"] = "Remember to choose actions from the admissible list."
        return action
    return ""

def format_prompt(prompt: str, state: dict) -> str:
    memory_feedback = state.get("memory_feedback", "")
    if memory_feedback:
        prompt += f"\nRemember: {memory_feedback}."
    return prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {
            "extra_instruction": "Focus on the admissible actions provided and choose from them.",
            "temperature": 0.3 
        }
    elif attempt == 2:
        return {
            "extra_instruction": "It's crucial to select an action from the admissible list now.",
            "temperature": 0.25 
        }
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "successfully" in next_observation:
        state["memory_feedback"] = f"The action '{action}' was effective. Keep up similar efforts."
    elif "cannot" in next_observation:
        state["memory_feedback"] = f"Re-evaluate the objectives or method, the last action '{action}' didn't work as expected."