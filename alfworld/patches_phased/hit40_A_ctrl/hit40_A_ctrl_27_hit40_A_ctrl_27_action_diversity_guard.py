HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Initialize or update action history in state
    if "action_history" not in state:
        state["action_history"] = []
    state["action_history"].append(action)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        # Focus on not repeating the same action too frequently
        additional_instruction = " Consider varying your actions as previous attempts might have failed due to excessive repetition."
        
        # Recognize recent actions
        recent_actions = state.get("action_history", [])
        
        # If action is repeated frequently, emphasize variety
        if recent_actions.count(action) > 2:
            additional_instruction += f" Note: The recent action '{action}' has been repeated often."
        
        return {"extra_instruction": additional_instruction, "temperature": 0.4}
    return None