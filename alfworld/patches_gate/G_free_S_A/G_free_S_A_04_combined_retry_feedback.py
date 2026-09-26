HISTORY_LENGTH = 7

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {
            "extra_instruction": (
                "Your previous action was not admissible. "
                "Remember to choose actions from the provided admissible actions list and ensure your reasoning is tied to the task's goals."
            ),
            "temperature": 0.3
        }
    elif attempt == 2:
        return {
            "extra_instruction": (
                "It's crucial to select an action from the admissible list now. "
                "Read through the goals and admissible actions carefully."
            ),
            "temperature": 0.2
        }
    return None

def format_prompt(prompt: str, state: dict) -> str:
    memory_feedback = state.get("memory_feedback", "")
    if memory_feedback:
        prompt += f"\nMemory note: {memory_feedback}."
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            state["memory_feedback"] = f"Action '{action}' was successful. Good choice!"
        else:
            state["memory_feedback"] = "Select only from admissible actions."
        return action
    return ""

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "successfully" in next_observation:
        state["memory_feedback"] = f"The action '{action}' was effective. Keep up similar efforts."
    elif "cannot" in next_observation:
        state["memory_feedback"] = "The last action didn't work. Focus more on achieving the task with admissible actions."