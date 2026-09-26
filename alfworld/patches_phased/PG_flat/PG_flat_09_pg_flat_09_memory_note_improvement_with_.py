HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def format_prompt(prompt: str, state: dict) -> str:
    # Add loop detection note to the prompt if needed
    if state.get("loop_detected"):
        loop_instruction = "Note: Avoid repeating the same action multiple times unless necessary."
        prompt += f"\n{loop_instruction}"
    return prompt

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Track the actions and use them to detect loops
    if "action_history" not in state:
        state["action_history"] = collections.deque(maxlen=5)
    
    state["action_history"].append(action)
    
    # Detect loop if the last three actions are the same, set a flag in state
    if len(state["action_history"]) >= 3 and len(set(state["action_history"])) == 1:
        state["loop_detected"] = True
    else:
        state["loop_detected"] = False