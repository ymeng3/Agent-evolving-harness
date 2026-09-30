EDITS = [
    {
        "id": "e1",
        "capability": "Verification",
        "impl": "Code",
        "trigger": "after updating an alarm, verify the alarm details match the update request",
        "depends": [],
        "expected_effect": "Ensure that the alarm update is successfully verified, preventing premature task completion in case of mismatch.",
        "side_effect_risk": "Low - Only affects alarm update verification."
    }
]

def e1_post_exec(code, out, state):
    if "apis.phone.update_alarm" in code and "Alarm updated successfully" in out:
        # Extract the update parameters from the code string
        import re
        alarm_update_match = re.search(r"apis\.phone\.update_alarm\(.*?alarm_id=(\d+).*?time=[\"'](.*?)[\"'].*?repeat_days=\[(.*?)\]", code, re.DOTALL)
        if alarm_update_match:
            alarm_id = alarm_update_match.group(1)
            expected_time = alarm_update_match.group(2)
            expected_repeat_days = [day.strip(" '\"") for day in alarm_update_match.group(3).split(",")]
            
            # Fetch the updated alarm details
            verify_code = f'updated_alarm = apis.phone.show_alarm(alarm_id={alarm_id}, access_token=phone_login["access_token"])\nprint(updated_alarm)'
            exec(verify_code, globals())

            if 'updated_alarm' in globals():
                updated_alarm = globals()['updated_alarm']
                if updated_alarm['time'] != expected_time or set(updated_alarm['repeat_days']) != set(expected_repeat_days):
                    raise AssertionError("Verified alarm does not match expected time or repeat_days")
