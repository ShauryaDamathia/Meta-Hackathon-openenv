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
        task_name = "security_log_analysis"

        print(f"[START] task={task_name}", flush=True)

        obs = get(f"{API_BASE_URL}/reset")

        action = {
            "category": "normal",
            "severity": "low",
            "action": "monitor activity",
        }

        result = post(f"{API_BASE_URL}/step", action)

        reward = result.get("reward", 0.0)

        print(
            f"[STEP] step=1 reward={reward}",
            flush=True
        )

        print(
            f"[END] task={task_name} score={reward} steps=1",
            flush=True
        )

    except Exception as e:
        print(f"[ERROR] {str(e)}", flush=True)


if __name__ == "__main__":
    run()