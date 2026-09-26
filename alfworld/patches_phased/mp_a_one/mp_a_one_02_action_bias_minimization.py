HISTORY_LENGTH = 10
TEMPERATURE = 0.6

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if action.lower() not in [adm.lower() for adm in admissible]:
        if attempt == 1:
            return {"extra_instruction": "Your last action wasn't valid. Consider the context carefully and choose only from the provided admissible actions.", "temperature": 0.4}
        elif attempt == 2:
            return {"extra_instruction": "Your last action wasn't valid again. Ensure you're selecting actions strictly from the admissible list.", "temperature": 0.3}
    return None

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # Return the best matching admissible action
    response_action = "".join(
        response.split("<action>")[1].split("</action>")[0].strip().lower()
    ) if "<action>" in response and "</action>" in response else ""
    return next((adm for adm in admissible if adm.lower() == response_action), admissible[0])