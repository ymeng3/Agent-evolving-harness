HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "feedback_memory" not in state:
        state["feedback_memory"] = []
    # Save the last action and the result of that action to the memory
    state["feedback_memory"].append((action, next_observation))

def format_prompt(prompt: str, state: dict) -> str:
    # Include memory feedback of past impact of actions
    feedback_memory = state.get("feedback_memory", [])
    if feedback_memory:
        feedback_statements = []
        feedback_statements = [f"{action} led to: {result}" for action, result in feedback_memory[-3:]]
        
        feedback_info = " Recent memory feedbacks: " + " | ".join(feedback_statements)
        prompt += feedback_info
    
    return prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        additional_instruction = (
            " Review the recent action impacts from the memory."
            " Make sure your next action is among the admissible ones and consider the previous results."
        )
        return {"extra_instruction": additional_instruction}
    return None

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>\s*(.*?)\s*</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            return action
    return "look"