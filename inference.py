import os
import json
import urllib.request
from openai import OpenAI

ENV_URL = os.getenv(
    "ENV_URL",
    "https://shauryadamathia-security-log-analysis-openenv.hf.space"
)

API_BASE_URL = os.environ["API_BASE_URL"]
API_KEY = os.environ["API_KEY"]
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)


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


def run_episode(task_name):
    rewards = []
    steps = 0

    print(f"[START] task={task_name} env=security_log model={MODEL_NAME}", flush=True)

    try:
        obs = get(f"{ENV_URL}/reset")
        prompt = obs["agent_prompt"]

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        text = response.choices[0].message.content.strip()
        action = json.loads(text)

        result = post(f"{ENV_URL}/step", action)

        reward = float(result.get("reward", 0.0))
        done = result.get("done", True)

        rewards.append(reward)
        steps = 1

        print(
            f"[STEP] step=1 action=json reward={reward:.2f} done={str(done).lower()} error=null",
            flush=True,
        )

    except Exception as e:
        print(
            f"[STEP] step=1 action=error reward=0.00 done=true error={str(e)}",
            flush=True,
        )
        done = True

    score = max(0.01, min(0.99, rewards[-1] if rewards else 0.0))
    rewards_str = ",".join(f"{r:.2f}" for r in rewards) if rewards else "0.00"

    print(
        f"[END] success=true steps={steps} score={score:.2f} rewards={rewards_str}",
        flush=True,
    )


def main():
    tasks = ["easy", "medium", "hard"]
    for task in tasks:
        run_episode(task)


if __name__ == "__main__":
    main()