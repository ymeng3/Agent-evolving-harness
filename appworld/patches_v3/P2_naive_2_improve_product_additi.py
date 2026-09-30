EDITS = [
    {
        "id": "e1",
        "capability": "ToolUse",
        "impl": "State",
        "trigger": "after executing a failed API call to apis.api_docs.show_api_doc for amazon",
        "depends": [],
        "expected_effect": "Increase reliability in fetching API documentation by removing repeated failures at the start",
        "side_effect_risk": "Minimal; improved performance in correctly identifying usable APIs."
    },
    {
        "id": "e2",
        "capability": "Recovery",
        "impl": "ControlFlow",
        "trigger": "after a failed API call to find api documentation",
        "depends": [],
        "expected_effect": "Retry fetching the API documentation once in case of a failure",
        "side_effect_risk": "Minimal; harmless retry attempt mitigates transient issues."
    }
]

import itertools

def e1_post_exec(code, out, state):
    # Increment an error counter in state for a specific type of failed API call
    if "apis.api_docs.show_api_doc" in code and "Execution failed" in out:
        state['failed_api_doc_calls'] = state.get('failed_api_doc_calls', 0) + 1

def e2_pre_call(prompt, state):
    # If there was a recent failure with fetching API documentation, allow a retry
    retry_limit = 1
    if state.get('failed_api_doc_calls', 0) > 0:
        if state.setdefault('api_doc_retry_count', 0) < retry_limit:
            state['api_doc_retry_count'] += 1
            return prompt  # Retrying the call
        else:
            # Once retry limit is reached, reset
            state['failed_api_doc_calls'] = 0
            state['api_doc_retry_count'] = 0
    return prompt
