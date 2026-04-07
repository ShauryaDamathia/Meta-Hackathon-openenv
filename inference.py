import os
import json
import urllib.request

API_BASE_URL = os.getenv(
    "API_BASE_URL",
    "https://shauryadamathia-security-log-analysis-openenv.hf.space"
)


def get(url):
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read().decode())


def post(url, data):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode())


def run():
    try:
        print("START")

        obs = get(f"{API_BASE_URL}/reset")
        print("STEP reset:", obs)

        action = {
            "category": "normal",
            "severity": "low",
            "action": "monitor activity",
        }

        result = post(f"{API_BASE_URL}/step", action)
        print("STEP result:", result)

        print("END")

    except Exception as e:
        print("ERROR:", str(e))


if __name__ == "__main__":
    run()