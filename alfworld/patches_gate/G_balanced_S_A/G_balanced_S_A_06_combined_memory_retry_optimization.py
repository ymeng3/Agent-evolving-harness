HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def format_prompt(prompt: str, state: dict) -> str:
    # Incorporate important memory feedback from past observations to inform current actions
    memory_feedback = state.get("memory_feedback", "")
    if memory_feedback:
        return f"{prompt}\nRemember from past actions: {memory_feedback}."
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        potential_action = match.group(1).strip().lower()
        if potential_action in admissible:
            state["last_successful_action"] = potential_action
            return potential_action
    return ""

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        # Provide feedback focusing on invalid action and a reminder of successful actions
        hint = "Focus on selecting one of the admissible actions. "
        if "last_successful_action" in state:
            hint += f"Consider repeating or modifying the successful action: {state['last_successful_action']}."
        return {
            "extra_instruction": hint,
            "temperature": 0.3
        }
    elif attempt == 2:
        # Increase emphasis on choosing from admissible actions
        return {
            "extra_instruction": "It's crucial to choose from the given admissible actions.",
            "temperature": 0.25
        }
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Update memory feedback based on new observations and outcomes
    if "successfully" in next_observation:
        state["memory_feedback"] = f"The action '{action}' was beneficial."
    elif "fail" in next_observation:
        state["memory_feedback"] = f"Avoid the action '{action}' as it led to failure."