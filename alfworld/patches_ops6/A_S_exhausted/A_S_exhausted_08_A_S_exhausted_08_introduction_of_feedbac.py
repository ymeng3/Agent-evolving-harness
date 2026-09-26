HISTORY_LENGTH = 10

def format_prompt(prompt: str, state: dict) -> str:
    # Introduce a feedback loop in the prompt to encourage the model to reflect on previous missteps
    # and successes. This may increase effective decision-making.
    feedback = state.get("feedback", "")
    if feedback:
        feedback_instruction = f"Consider this feedback from your recent actions: {feedback} "
        prompt = feedback_instruction + prompt
    return prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Update feedback based on observation mismatch from expected outcomes. For simplicity,
    # we'll store feedback information in the state with either success or action correction advice.
    if action in next_observation:
        feedback = "Your action matched the observation correctly. Keep up similar assessments."
    else:
        feedback = "Your action didn't match the expected observation. Adjust your actions accordingly."
    state["feedback"] = feedback