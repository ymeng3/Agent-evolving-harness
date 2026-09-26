def format_prompt(prompt: str, state: dict) -> str:
    if "retry_instruction_effective" in state:
        retry_instruction = state.get("retry_instruction", "")
        return prompt + " " + retry_instruction
    return prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 3:
        retry_instruction = "Based on past mistakes, ensure the action matches one from the list of admissible actions."
        state["retry_instruction"] = retry_instruction
        state["retry_instruction_effective"] = False
        return {"extra_instruction": retry_instruction, "temperature": 0.4}
    return None

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    action_match = re.search(r"<action>(.*?)</action>", response.lower())
    action = action_match.group(1).strip() if action_match else ""
    if action in admissible:
        if "retry_instruction" in state:
            state["retry_instruction_effective"] = True
        return action
    return ""