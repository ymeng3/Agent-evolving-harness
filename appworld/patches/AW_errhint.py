def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    state["last_err"] = next_observation.startswith("Execution failed")
    state["n_err"] = state.get("n_err", 0) + int(state["last_err"])

def format_prompt(prompt: str, state: dict) -> str:
    if state.get("last_err"):
        prompt += ("\n\nThe last code cell raised an error. Before retrying, read the exact error message, and if it is about "
                   "arguments or an unknown API, call apis.api_docs.show_api_doc(app_name=..., api_name=...) for that API and then fix the call.")
    return prompt
