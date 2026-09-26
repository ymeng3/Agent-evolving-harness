HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        extra_instruction = (
            "Your previous action was not admissible."
            " Please ensure your selected action is one of the admissible actions."
            " Think carefully about the context and try again."
        )
        # Increase temperature slightly on first retry to encourage exploration
        new_temperature = TEMPERATURE + 0.1
        return {"extra_instruction": extra_instruction, "temperature": new_temperature}
    elif attempt == 2:
        extra_instruction = (
            "Your previous attempt was also not admissible."
            " Make sure to choose an action exactly from the list of admissible actions."
            " Consider the environment and objects again thoughtfully."
        )
        # Reduce temperature on second retry to focus model on considering more recently observed actions
        new_temperature = TEMPERATURE - 0.1
        return {"extra_instruction": extra_instruction, "temperature": new_temperature}
    return None