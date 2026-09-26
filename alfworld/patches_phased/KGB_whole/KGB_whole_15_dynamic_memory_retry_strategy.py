HISTORY_LENGTH = 10


def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Adjust the retry based on memory about past failed actions
    if "failed_actions" not in state:
        state["failed_actions"] = set()
        
    state["failed_actions"].add(action)
    
    extra_instruction = (
        f"Your last action '{action}' wasn't valid. "
        "Actions that have failed often: " + ", ".join(state["failed_actions"]) + ". "
        "Focus on selecting one of the admissible actions listed."
    )
    
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None


import re

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    def extract_action(text: str) -> str:
        action_match = re.search(r"<action>\s*(.*?)\s*</action>", text, re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip().lower()
            if action in admissible:
                return action
        
        for action in admissible:
            if action in text.lower():
                return action
        
        return "look"

    return extract_action(response)


def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Initialize history if not existed
    if "observation_history" not in state:
        state["observation_history"] = []
    
    if "action_history" not in state:
        state["action_history"] = []
        
    # Track observation and action history
    state["observation_history"].append(observation)
    state["action_history"].append(action)
    
    # Keep only the most recent HISTORY_LENGTH entries
    if len(state["observation_history"]) > HISTORY_LENGTH:
        state["observation_history"].pop(0)
    
    if len(state["action_history"]) > HISTORY_LENGTH:
        state["action_history"].pop(0)