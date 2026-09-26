HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = (
            "Your action was not among the admissible ones."
            " Fully reassess the situation, examining your reasoning."
            " Ensure your action is taken from the admissible actions list."
        )
        return {"extra_instruction": extra_instruction}
    return None

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    
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