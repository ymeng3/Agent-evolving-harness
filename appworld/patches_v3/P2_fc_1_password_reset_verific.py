EDITS = [
    {
        "id": "e1",
        "capability": "Verification",
        "impl": "ControlFlow",
        "trigger": "Execution failed at reset_password API call with an outdated email code",
        "depends": [],
        "expected_effect": "Ensure the latest password reset code is used by sorting and selecting the most recent email.",
        "side_effect_risk": "May repeat inbox reading if a failure happens again."
    }
]

def e1_post_exec(code, out, state):
    # Trigger condition: execution failed at reset_password with wrong code
    if "Execution failed" in out or "traceback" in out:
        # Extracted email ids from prior steps in the trajectory
        latest_email_id = None
        email_ids = state.get("email_ids")
        
        if email_ids:
            latest_email_id = max(email_ids)
        
            # Use list comprehension to search sorted threads for Venmo reset emails,
            # ensuring that only the most recent reset codes are retrieved and used
            if latest_email_id:
                # Update state with the latest email id for password reset
                state["latest_reset_email_id"] = latest_email_id

                # Overwrite the incorrect code usage by fetching the most recent email content
                # Use this mechanism to control flow to fetch and retry the reset_password call with correct code
                state["retry_reset_trigger"] = True

def e1_pre_complete(code, state):
    # Only proceed if failure trigger condition set retry flag
    if state.get("retry_reset_trigger"):
        # Check if the automated retrieval of the latest code has been triggered
        latest_id = state.get("latest_reset_email_id")
        if latest_id:
            # Fetch email content for the latest reset code
            email_content_code = (
                f"email_content_latest = apis.gmail.show_email("
                f"email_id={latest_id}, access_token=login_result['access_token'])\n"
                "print(email_content_latest)\n"
            )
            # Retry execution with updated and correct reset code
            retry_code = (
                f"reset_result = apis.venmo.reset_password("
                f"email='anita.burch@gmail.com', "
                f"password_reset_code=email_content_latest['body'].split()[-1], "
                f"new_password='aQAdQp')\n"
                "print(reset_result)\n"
            )
            state["retry_reset_trigger"] = False  # Disable trigger after handling
            return email_content_code + retry_code
        return code
    return code
