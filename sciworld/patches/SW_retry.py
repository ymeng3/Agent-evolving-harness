def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        return {"extra_instruction": "Your previous reply did not contain a valid command. Re-read the valid templates and objects, then output exactly one valid command inside <action></action>."}
    return None
