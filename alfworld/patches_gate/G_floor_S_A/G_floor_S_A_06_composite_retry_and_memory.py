def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {
            "extra_instruction": "Focus on choosing an action from the admissible actions provided."
        }
    elif attempt == 2:
        return {
            "extra_instruction": "Ensure your chosen action is from the admissible list.",
            "temperature": 0.3
        }
    return None

def format_prompt(prompt: str, state: dict) -> str:
    memory_feedback = state.get("memory_feedback", "")
    if memory_feedback:
        prompt += f"\nPrioritized information: {memory_feedback}."
    split_prompt = (
        prompt.replace("Now it's your turn to take an action.",
                       "Now it's your turn to reason and take an action.")
              .replace("You should first reason step-by-step about the current situation. This reasoning process MUST be enclosed within <think> </think> tags.",
                       "First, reason step-by-step about the current situation, considering the goal and admissible actions. Enclose this reasoning within <think> </think> tags.")
              .replace("Once you've finished your reasoning, you should choose an admissible action for current step and present it within <action> </action> tags.",
                       "After reasoning, review admissible actions again, then decide and clearly specify your action within <action> </action> tags.")
    )
    return split_prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        state["memory_feedback"] = f"Last chosen action: '{action}'." if action in admissible else "Choose only from admissible actions."
        return action if action in admissible else ""
    return ""

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "successfully" in next_observation:
        state["memory_feedback"] = f"The action '{action}' was effective. Consider similar strategies."
    elif "cannot" in next_observation:
        state["memory_feedback"] = f"Action '{action}' was ineffective. Rethink your approach."