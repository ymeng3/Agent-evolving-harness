def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1 and action not in admissible:
        # Provide a hint to focus on actions that might have been overlooked
        if "examine" not in response.lower():
            return {"extra_instruction": "Focus on actions like 'examine' or 'go to' to explore or observe objects.", "temperature": 0.3}
        elif "go to" not in response.lower():
            return {"extra_instruction": "Consider actions like 'go to' or 'open' to change your location or interact with objects.", "temperature": 0.3}
    return None