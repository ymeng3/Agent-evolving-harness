HISTORY_LENGTH = 7

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {
            "extra_instruction": "Your previous action was not valid. Please choose an action from the admissible list and ensure it is suitable for the current context.",
            "temperature": 0.3
        }
    elif attempt == 2:
        return {
            "extra_instruction": "It is crucial to select an action from the admissible list now.",
            "temperature": 0.25
        }
    return None

def format_prompt(prompt: str, state: dict) -> str:
    memory_feedback = state.get("memory_feedback", "")
    if memory_feedback:
        prompt += f"\nNote: {memory_feedback}."
    return prompt

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "successfully" in next_observation:
        state["memory_feedback"] = f"The action '{action}' was effective. Repeat similar actions for success."
    elif "cannot" in next_observation:
        state["memory_feedback"] = f"Consider revising your approach; the action '{action}' wasn't effective."