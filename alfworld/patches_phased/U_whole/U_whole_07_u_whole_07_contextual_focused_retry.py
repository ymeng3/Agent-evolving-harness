HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    def extract_relevant_information(response: str) -> str:
        import re
        think_content = re.search(r'<think>(.*?)</think>', response, re.DOTALL)
        if think_content:
            return think_content.group(1).strip()
        return ""

    if attempt == 1:
        relevant_info = extract_relevant_information(response)
        if relevant_info:
            extra_instruction = (
                f"Your reasoning contained relevant thoughts: '{relevant_info}'. "
                "However, your last action wasn't valid. Please refine your choice by selecting one of the admissible actions listed."
            )
        else:
            extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        extra_instruction = "This is your final attempt. Ensure the action is one of the admissible actions listed."
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None