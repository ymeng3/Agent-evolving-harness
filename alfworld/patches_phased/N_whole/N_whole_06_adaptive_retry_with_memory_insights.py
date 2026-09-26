HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    
    if attempt == 1:
        state['retry_attention'] = True
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.6}
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
    if action == "look" and "retry_attention" in state:
        del state["retry_attention"]