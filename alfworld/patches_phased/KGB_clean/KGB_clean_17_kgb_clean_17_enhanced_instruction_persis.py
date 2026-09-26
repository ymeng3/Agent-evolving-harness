HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction_base = "Your previous action was invalid. Please choose carefully among the admissible actions: "
    extra_instruction_specific = f"Consider actions such as {', '.join(admissible[:3])}, depending on the situation."
    
    if attempt == 1:
        return {
            "extra_instruction": f"{extra_instruction_base}{extra_instruction_specific}",
            "temperature": 0.4
        }
    elif attempt == 2:
        return {
            "extra_instruction": f"{extra_instruction_base}{extra_instruction_specific}",
            "temperature": 0.3
        }
    return None