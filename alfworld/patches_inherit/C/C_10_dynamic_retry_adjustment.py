HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    import random
    extra_instruction_base = "Focus on selecting one of the admissible actions listed."
    dynamic_instruction = ""
    
    if "look" in admissible:
        dynamic_instruction += " Consider using 'look' to gather more information."
    if len(admissible) > 5:
        dynamic_instruction += " Narrow down your choices."

    complete_instruction = f"Your last action wasn't valid. {extra_instruction_base} {dynamic_instruction}"

    if attempt == 1:
        temperature_adjustment = random.choice([0.3, 0.35])  # Slight randomness to explore a different action space
        return {"extra_instruction": complete_instruction, "temperature": temperature_adjustment}
    elif attempt == 2:
        temperature_adjustment = random.choice([0.2, 0.25])
        return {"extra_instruction": complete_instruction, "temperature": temperature_adjustment}
    return None