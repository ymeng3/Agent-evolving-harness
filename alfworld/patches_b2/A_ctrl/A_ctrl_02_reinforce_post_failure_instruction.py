TEMPERATURE = 0.6

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Reinforce and expand instructions on retries after invalid actions, adjusting temperature to encourage exploration.
    if attempt == 1:
        return {
            "extra_instruction": (
                "You selected an invalid action previously. Carefully review the admissible actions list. "
                "Re-evaluate the environment's context, focusing on completing your specific task objectives."
            ),
            "temperature": 0.5
        }
    elif attempt == 2:
        return {
            "extra_instruction": (
                "Attention: You must select an action strictly from the admissible actions. "
                "Consider alternative strategies and reason through the choices thoroughly."
            ),
            "temperature": 0.4
        }
    return None