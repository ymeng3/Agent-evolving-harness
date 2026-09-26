HISTORY_LENGTH = 10

def format_prompt(prompt: str, state: dict) -> str:
    # Append history to the prompt to provide more context for each decision.
    if "extra_history" in state:
        return prompt + state["extra_history"]
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # Capture the response and the parsed action, storing the extra history needed.
    start_tag = "<action>"
    end_tag = "</action>"
    start_idx = response.find(start_tag)
    end_idx = response.find(end_tag)

    action = response[start_idx + len(start_tag):end_idx].strip() if start_idx != -1 and end_idx != -1 else ""
    state["last_response"] = response
    state["last_action"] = action
    return action

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # On an invalid action, we incorporate additional history into the prompt to give more context.
    if attempt == 1:
        state["extra_history"] = "\nAdditional history provided to aid decision:\n" + state.get("last_response", "")
        return {"extra_instruction": "Reflect on previous decisions to improve action choice."}
    elif attempt == 2:
        return {"temperature": 0.3}
        
    return None