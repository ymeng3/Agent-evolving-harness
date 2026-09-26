HISTORY_LENGTH = 7

def format_prompt(prompt: str, state: dict) -> str:
    memo_feedback = state.get("memo_feedback", "")
    if memo_feedback:
        prompt += f"\nNote: {memo_feedback}."
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    action_match = re.search(r"<action>\s*(.*?)\s*</action>", response, re.IGNORECASE)
    
    action = action_match.group(1).strip().lower() if action_match else ""
    if action not in admissible:
        state["memo_feedback"] = f"Must choose from admissible actions: {admissible}."
        return "look"

    if action in admissible:
        state["memo_feedback"] = f"Chose '{action}' successfully."
        return action
    
    return "look"

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if action not in state.get('action_usage', {}):
        state.setdefault('action_usage', {})[action] = 0
    state['action_usage'][action] += 1

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    instruction = (
        "Ensure the action is one of the admissible options."
        " Consider previous steps and adjust accordingly."
    )
    if attempt < 2:
        return {"extra_instruction": instruction, "temperature": 0.3}
    return None