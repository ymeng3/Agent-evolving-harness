HISTORY_LENGTH = 10
TEMPERATURE = 0.3

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {"extra_instruction": "Remember to choose an action from the admissible actions list.", "temperature": 0.35}
    elif attempt == 2:
        return {"extra_instruction": "Check if your previous reasoning steps fully consider the current observation and task goal.", "temperature": 0.3}
    return None

def format_prompt(prompt: str, state: dict) -> str:
    return prompt.replace("admissible actions of the current situation are", "admissible actions you MUST choose from are")

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "repeated_actions" not in state:
        state["repeated_actions"] = []
    if action in state["repeated_actions"]:
        state["repeated_actions"].remove(action)
    state["repeated_actions"].append(action)
    if len(state["repeated_actions"]) > 10:
        state["repeated_actions"].pop(0)
    
def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prefer the 'look' action if it's admissible to help re-evaluate the situation
    for action in admissible:
        if action.startswith("look"):
            return action
    return admissible[0]