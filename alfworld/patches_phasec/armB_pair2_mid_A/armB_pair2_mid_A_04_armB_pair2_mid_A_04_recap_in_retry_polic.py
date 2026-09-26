HISTORY_LENGTH = 7
TEMPERATURE = 0.4

def format_prompt(prompt: str, state: dict) -> str:
    return prompt
    
def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re 
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        return match.group(1).strip().lower()
    return ""

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Provide a concise recap of recent thought processes and change temperature
    recent_thoughts = state.get('recent_thoughts', [])
    recent_thoughts_text = " ".join(recent_thoughts[-3:])  # Use last 3 thoughts for recap

    if attempt == 1:
        return {
            "extra_instruction": f"Previous thoughts recap: {recent_thoughts_text}. Try to reason carefully and choose from the provided admissible actions.",
            "temperature": 0.5
        }
    elif attempt == 2:
        return {
            "extra_instruction": f"Consider previous thoughts: {recent_thoughts_text}. Focus on selecting actions distinctly different from previous attempts.",
            "temperature": 0.3
        }
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    import re 
    # Extract thoughts and store them
    thought_match = re.search(r"<think>(.*?)</think>", observation, re.IGNORECASE)
    if thought_match:
        recent_thoughts = state.setdefault('recent_thoughts', [])
        recent_thoughts.append(thought_match.group(1).strip())
        # Keep thoughts limited to last 10 entries to avoid excessive memory use
        if len(recent_thoughts) > 10:
            recent_thoughts.pop(0)