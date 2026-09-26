HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        # Extracts any reasoning within the <think></think> tags from the LLM response
        think_start = response.find('<think>')
        think_end = response.find('</think>')
        
        if think_start != -1 and think_end != -1:
            reasoning = response[think_start + 7:think_end].strip()
        else:
            reasoning = "No clear reasoning found."

        # Append extracted reasoning as a hint for the retry
        extra_instruction = f"Consider this context from your previous reasoning: {reasoning}. Make sure to select an action from the admissible actions list."
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None