HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction_template = ("Your last action wasn't valid. Carefully re-evaluate and choose one of the "
                                  "admissible actions listed.")

    def enhance_instruction(attempt: int):
        if attempt == 1:
            return extra_instruction_template + " It's critical to pay attention to the task context."
        elif attempt == 2:
            return extra_instruction_template + " Consider the consequences of each action before selection."

    if attempt in {1, 2}:
        return {"extra_instruction": enhance_instruction(attempt)}
    return None