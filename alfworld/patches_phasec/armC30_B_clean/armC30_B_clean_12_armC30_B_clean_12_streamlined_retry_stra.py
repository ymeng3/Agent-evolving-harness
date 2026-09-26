HISTORY_LENGTH = 8
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction_template = "Your previous action wasn't valid. Carefully select an action from the admissible list: {}."
    if attempt == 1:
        return {
            "extra_instruction": extra_instruction_template.format(', '.join(admissible)),
            "temperature": 0.6
        }
    elif attempt == 2:
        return {
            "extra_instruction": extra_instruction_template.format(', '.join(admissible)),
            "temperature": 0.7
        }
    return None