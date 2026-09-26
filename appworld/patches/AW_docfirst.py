def format_prompt(prompt: str, state: dict) -> str:
    state["n"] = state.get("n", 0) + 1
    if state["n"] == 1:
        prompt += ("\n\nStart by finding which apps and APIs you need: call apis.api_docs.show_app_descriptions() and then "
                   "apis.api_docs.show_api_descriptions(app_name=...) for each relevant app, and read the doc of every API before calling it.")
    return prompt
