def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Updates the state with feedback based on the success or failure indicated in the next observation.
    """
    if 'feedback' not in state:
        state['feedback'] = []
    
    def analyze_feedback(obs: str) -> str:
        # Provide positive or corrective feedback depending on the result of the action
        if "successfully" in obs or "completed" in obs:
            return "success"
        elif "fail" in obs or "cannot" in obs or "not" in obs:
            return "failure"
        return "neutral"

    feedback = analyze_feedback(next_observation)
    state['feedback'].append((action, feedback))

def format_prompt(prompt: str, state: dict) -> str:
    """
    Formats the prompt by including feedback gathered from previous actions to guide the agent.
    """
    feedback_summary = ""
    success_actions = [action for action, result in state.get('feedback', []) if result == "success"]
    failure_actions = [action for action, result in state.get('feedback', []) if result == "failure"]

    if success_actions:
        feedback_summary += f"Previous successful actions include: {', '.join(success_actions)}. "
    if failure_actions:
        feedback_summary += f"Actions that did not succeed: {', '.join(failure_actions)}. Focus on avoiding these errors."

    if feedback_summary:
        prompt += f"\nFeedback from previous steps: {feedback_summary}"

    return prompt