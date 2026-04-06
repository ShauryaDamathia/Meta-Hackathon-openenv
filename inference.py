import os
import requests

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "https://shauryadamathia-security-log-analysis-openenv.hf.space"
)

def run():
    print("START")

    r = requests.get(f"{API_BASE_URL}/reset")
    obs = r.json()

    print("STEP reset:", obs)

    action = {
        "category": "normal",
        "severity": "low",
        "action": "monitor activity"
    }

    r = requests.post(f"{API_BASE_URL}/step", json=action)
    result = r.json()

    print("STEP result:", result)

    print("END")

if __name__ == "__main__":
    run()