HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction_base = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed: {}."
    formatted_admissibles = ', '.join(f'"{a}"' for a in admissible)

    if attempt in (1, 2):
        extra_instruction = extra_instruction_base.format(formatted_admissibles)
        return {"extra_instruction": extra_instruction}
    return None