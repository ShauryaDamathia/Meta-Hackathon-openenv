import os
import requests

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "https://shauryadamathia-security-log-analysis-openenv.hf.space"
)

MODEL_NAME = os.getenv("MODEL_NAME", "baseline")


def run():
    # reset
    r = requests.get(f"{API_BASE_URL}/reset")
    obs = r.json()

    # simple baseline response
    action = {
        "category": "normal",
        "severity": "low",
        "action": "monitor"
    }

    # step
    r = requests.post(f"{API_BASE_URL}/step", json=action)
    result = r.json()

    print("Observation:", obs)
    print("Result:", result)


if __name__ == "__main__":
    run()