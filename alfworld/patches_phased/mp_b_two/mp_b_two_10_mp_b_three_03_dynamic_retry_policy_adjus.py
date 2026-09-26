HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "The action you selected was not valid. Please choose one among the admissible actions provided."
    
    # Analyze current observation to tailor retry
    observation_importance = ["important", "critical", "urgent"]
    current_observation = response.lower()
    is_critical = any(phrase in current_observation for phrase in observation_importance)

    if attempt == 1:
        # Adjust based on critical observations
        temp_adjustment = 0.1 if is_critical else 0.0
        return {"extra_instruction": extra_instruction, "temperature": 0.3 + temp_adjustment}
    elif attempt == 2:
        temp_adjustment = 0.05 if is_critical else 0.0
        return {"extra_instruction": extra_instruction, "temperature": 0.2 + temp_adjustment}
        
    return None