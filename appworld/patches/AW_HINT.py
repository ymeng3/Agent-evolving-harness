def format_prompt(prompt: str, state: dict) -> str:
    if state.get("_hint"):
        prompt += "\n\nRule for this task: " + str(state["_hint"])
    return prompt
