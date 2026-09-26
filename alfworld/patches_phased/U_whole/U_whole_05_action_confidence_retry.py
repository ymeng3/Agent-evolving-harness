HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    import re

    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    def extract_confidence(response: str) -> float:
        match = re.search(r'confidence: (\d+(\.\d+)?)', response)
        return float(match.group(1)) if match else 0.0

    confidence = extract_confidence(response)
    
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": max(0.1, 0.3 * (1 - confidence))}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": max(0.05, 0.2 * (1 - confidence))}
    return None