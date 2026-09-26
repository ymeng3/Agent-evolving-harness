HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    def build_extra_instruction(attempt: int) -> str:
        if attempt == 1:
            return "Your previous action wasn't among the admissible ones. Carefully review the admissible actions and choose the most appropriate one."
        elif attempt == 2:
            return "This is your last attempt. Make sure to select an action from the listed admissible actions."
        return ""

    extra_instruction = build_extra_instruction(attempt)
    return {"extra_instruction": extra_instruction} if attempt in {1, 2} else None