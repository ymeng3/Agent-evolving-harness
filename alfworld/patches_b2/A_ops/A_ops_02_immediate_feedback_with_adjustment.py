HISTORY_LENGTH = 7
TEMPERATURE = 0.5

def format_prompt(prompt: str, state: dict) -> str:
    memory_feedback = state.get("memory_feedback", "")
    if memory_feedback:
        prompt += f"\nNote: {memory_feedback}."
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            state["memory_feedback"] = f"Successful action '{action}'."
        else:
            state["memory_feedback"] = "Pick actions from the admissible list."
        return action
    return "look"

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        extra_instruction = (
            "The previous action was invalid."
            " Ensure you select an action listed as admissible."
            " Reason carefully about the current context."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.4}

    elif attempt == 2:
        return {"temperature": 0.3}
    return None