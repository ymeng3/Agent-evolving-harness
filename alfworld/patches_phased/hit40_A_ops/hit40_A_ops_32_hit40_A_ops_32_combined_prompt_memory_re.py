HISTORY_LENGTH = 6
TEMPERATURE = 0.45

def format_prompt(prompt: str, state: dict) -> str:
    memory_feedback = state.get("memory_feedback", "")
    if memory_feedback:
        prompt += f"\nConsider this feedback from your past actions: {memory_feedback}."
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    action_regex = re.compile(r"<action>\s*(.*?)\s*</action>", re.IGNORECASE)
    match = action_regex.search(response)
    
    if match:
        action_choice = match.group(1).strip().lower()
        if action_choice in admissible:
            return action_choice
    
    # Fall back to default action extraction
    for action in admissible:
        if action in response.lower():
            return action.lower()
    
    return "look"

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        extra_instruction = (
            "Your previous action was not admissible. "
            "Focus on selecting an action from the provided admissible actions."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    elif attempt == 2:
        extra_instruction = (
            "It's critical to choose an action from the admissible list. "
            "Consider the context carefully and ensure your reasoning aligns with the task objectives."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.35}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "successfully" in next_observation:
        state["memory_feedback"] = "Repeat similar actions that lead to success."
    elif "cannot" in next_observation:
        state["memory_feedback"] = "Adjust your strategy, analyze previous actions and avoid repetition."