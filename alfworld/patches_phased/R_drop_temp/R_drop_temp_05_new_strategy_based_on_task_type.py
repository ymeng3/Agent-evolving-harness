HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Prepare different messages for different types of tasks
    extra_instruction_general = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    extra_instruction_specific = "Based on the task, ensure that the action corresponds to the task type and context."

    # Access the task description from the previous response
    task_description = response.split("Your task is to: ")[1].split("\n")[0]

    if attempt == 1:
        if "pick" in task_description and "place" in task_description:
            return {"extra_instruction": extra_instruction_specific}
        else:
            return {"extra_instruction": extra_instruction_general}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction_general}
    return None