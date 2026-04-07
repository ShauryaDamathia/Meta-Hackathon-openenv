import os
import json
from openai import OpenAI
import urllib.request


ENV_API_BASE = os.environ["API_BASE_URL"]
ENV_API_KEY = os.environ["API_KEY"]

# OpenAI client routed through LiteLLM proxy
client = OpenAI(
    base_url=ENV_API_BASE,
    api_key=ENV_API_KEY,
)

# your env URL (not the LLM proxy)
ENV_URL = os.getenv(
    "ENV_URL",
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
        task = "security_log_analysis"
        print(f"[START] task={task}", flush=True)

        obs = get(f"{ENV_URL}/reset")

        prompt = obs["agent_prompt"]

        # call their proxy LLM
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )

        text = response.choices[0].message.content.strip()

        action = json.loads(text)

        result = post(f"{ENV_URL}/step", action)

        reward = result.get("reward", 0.0)

        print(f"[STEP] step=1 reward={reward}", flush=True)
        print(f"[END] task={task} score={reward} steps=1", flush=True)

    except Exception as e:
        print(f"[ERROR] {str(e)}", flush=True)


if __name__ == "__main__":
    run()