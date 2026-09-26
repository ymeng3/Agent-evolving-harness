HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    state.setdefault("retry_attempts", 0)
    state["retry_attempts"] += 1
    
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    
    # Strip <think> and <action> tags for higher attempts to give a direct action focus
    if state["retry_attempts"] > 1:
        response_without_tags = response.replace("<think>", "").replace("</think>", "").replace("<action>", "").replace("</action>", "")
        state["response"] = response_without_tags
    else:
        state["response"] = response
    
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    
    return None

def format_prompt(prompt: str, state: dict) -> str:
    # If a response was tagged for retry, adjust the prompt to include the modified response
    return f"{prompt} Recent actions: {state['response']}" if "response" in state else prompt