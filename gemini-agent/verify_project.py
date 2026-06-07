import os
import json
from fraud_agent.system_health import check_system_health

def run_verification():
    print("==================================================")
    print("       Omnichannel Anti-Fraud Agent Verification")
    print("==================================================")

    health_report = check_system_health()

    print("\n--- System Health Report ---")
    for component, data in health_report.items():
        status = data["status"]
        color_code = "\033[92m" if status == "CONNECTED" else ("\033[93m" if status == "MOCK_MODE" else "\033[91m")
        print(f"  {component.replace('_', ' ').title()}: {color_code}{status}\033[0m")

    print("\n--- Production Mode Settings ---")
    strict_production_mode = os.getenv("STRICT_PRODUCTION_MODE", "false").lower() == "true"
    if strict_production_mode:
        print(f"  STRICT_PRODUCTION_MODE: \033[92mTrue\033[0m (No fallback to mocks for MongoDB/Elasticsearch)")
    else:
        print(f"  STRICT_PRODUCTION_MODE: \033[93mFalse\033[0m (Mocks allowed for MongoDB/Elasticsearch if real services are unavailable)")

    fraud_alert_threshold = os.getenv("FRAUD_ALERT_THRESHOLD")
    if fraud_alert_threshold:
        print(f"  FRAUD_ALERT_THRESHOLD: \033[92m{fraud_alert_threshold}\033[0m (Threat score for triggering alerts)")
    else:
        print(f"  FRAUD_ALERT_THRESHOLD: \033[91mNot Set\033[0m (Defaulting to 0.8 in guardian_alert_service)")

    print("\n--- Overall Status ---")
    all_connected = True
    has_mocks = False
    has_misconfigured = False
    has_disconnected = False

    for component, data in health_report.items():
        status = data["status"]
        if status != "CONNECTED":
            all_connected = False
        if status == "MOCK_MODE":
            has_mocks = True
        if status == "MISCONFIGURED":
            has_misconfigured = True
        if status == "DISCONNECTED":
            has_disconnected = True

    if all_connected and not has_mocks:
        print("\033[92mPASS: All components are CONNECTED and no mocks are in use. Project is production ready.\033[0m")
    elif has_disconnected or has_misconfigured:
        print("\033[91mFAIL: Some components are DISCONNECTED or MISCONFIGURED. Project is NOT production ready.\033[0m")
        if strict_production_mode:
            print("      (Note: STRICT_PRODUCTION_MODE is enabled, which will prevent fallback to mocks.)")
    elif has_mocks:
        print("\033[93mWARNING: Some components are in MOCK_MODE. Project is NOT production ready, but can be used for demo/development.\033[0m")
        if strict_production_mode:
            print("      (Note: STRICT_PRODUCTION_MODE is enabled, but mocks are explicitly configured for some services.)")
    else:
        print("\033[91mFAIL: Unexpected system health status. Project is NOT production ready.\033[0m")

    print("\n==================================================")
    print("Verification Complete.")
    print("==================================================")

if __name__ == "__main__":
    run_verification()
