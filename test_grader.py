import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request
from urllib.parse import urlparse

from environment import SecurityEnv


ENV_FILE = Path(__file__).resolve().parent / ".env"
PREFERRED_MODELS = [
    "llama-3.3-70b-versatile",
    "groq/compound-mini",
    "openai/gpt-oss-120b",
    "llama-3.1-8b-instant",
    "groq/compound",
    "openai/gpt-oss-20b",
]
NON_CHAT_MODEL_MARKERS = [
    "whisper",
    "tts",
    "transcribe",
    "transcription",
    "speech",
    "vision-preview",
]
_RESOLVED_MODEL = None


def load_dotenv(dotenv_path):
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        os.environ.setdefault(key, value)


load_dotenv(ENV_FILE)


AGENT_CONFIG = {
    "api_url": os.getenv("AGENT_API_URL", "https://api.openai.com/v1/chat/completions"),
    "api_key": os.getenv("AGENT_API_KEY", ""),
    "temperature": 0,
    "max_tokens": 300,
    "timeout_seconds": 60,
    "send_feedback_to_agent": True,
    "runs": 1,
    "log_file": Path(__file__).resolve().parent / "agent_eval_log.jsonl",
}


def normalize_chat_completions_url(api_url):
    normalized = api_url.rstrip("/")
    if normalized.endswith("/chat/completions"):
        return normalized
    if normalized.endswith("/v1"):
        return f"{normalized}/chat/completions"
    if normalized.endswith("/openai/v1"):
        return f"{normalized}/chat/completions"
    return normalized


def build_models_url(api_url):
    chat_url = normalize_chat_completions_url(api_url)
    if chat_url.endswith("/chat/completions"):
        return f"{chat_url[:-len('/chat/completions')]}/models"
    return f"{chat_url}/models"


def get_provider_host():
    return urlparse(normalize_chat_completions_url(AGENT_CONFIG["api_url"])).netloc.lower()


def build_headers():
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Meta-Hackathon-OpenEnv/1.0",
    }
    if AGENT_CONFIG["api_key"]:
        headers["Authorization"] = f"Bearer {AGENT_CONFIG['api_key']}"
    return headers


def is_chat_model(model_id):
    lowered = model_id.lower()
    return not any(marker in lowered for marker in NON_CHAT_MODEL_MARKERS)


def choose_model(model_items):
    active_ids = [item["id"] for item in model_items if item.get("active")]
    if not active_ids:
        raise RuntimeError("The provider returned no active models.")

    for model_id in PREFERRED_MODELS:
        if model_id in active_ids:
            return model_id

    for model_id in active_ids:
        if is_chat_model(model_id):
            return model_id

    return active_ids[0]


def resolve_model():
    global _RESOLVED_MODEL
    if _RESOLVED_MODEL:
        return _RESOLVED_MODEL

    models_url = build_models_url(AGENT_CONFIG["api_url"])
    http_request = request.Request(
        models_url,
        headers=build_headers(),
        method="GET",
    )

    try:
        with request.urlopen(http_request, timeout=AGENT_CONFIG["timeout_seconds"]) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Model discovery failed with HTTP {exc.code}: {body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Could not reach model discovery endpoint: {exc}") from exc

    _RESOLVED_MODEL = choose_model(payload.get("data", []))
    return _RESOLVED_MODEL


def build_messages(observation):
    return [
        {
            "role": "system",
            "content": observation["instructions"],
        },
        {
            "role": "user",
            "content": (
                f"System: {observation['system']}\n"
                f"Log: {observation['log']}\n\n"
                "Return only JSON with this shape:\n"
                f"{json.dumps(observation['response_example'])}"
            ),
        },
    ]


def build_feedback_message(observation, expected, predicted, score):
    return {
        "role": "user",
        "content": (
            "Your previous answer has been graded.\n"
            f"Original system: {observation['system']}\n"
            f"Original log: {observation['log']}\n"
            f"Expected answer: {json.dumps(expected)}\n"
            f"Your answer: {json.dumps(predicted)}\n"
            f"Score: {score}\n\n"
            "Use this feedback to improve future answers while keeping the exact same JSON-only format."
        ),
    }


def build_request_payload(messages):
    payload = {
        "model": resolve_model(),
        "messages": messages,
        "temperature": AGENT_CONFIG["temperature"],
    }

    if "groq.com" in get_provider_host():
        payload["max_completion_tokens"] = AGENT_CONFIG["max_tokens"]
        payload["response_format"] = {"type": "json_object"}
    else:
        payload["max_tokens"] = AGENT_CONFIG["max_tokens"]

    return payload


def call_agent(messages):
    payload = json.dumps(build_request_payload(messages)).encode("utf-8")
    http_request = request.Request(
        normalize_chat_completions_url(AGENT_CONFIG["api_url"]),
        data=payload,
        headers=build_headers(),
        method="POST",
    )

    try:
        with request.urlopen(
            http_request,
            timeout=AGENT_CONFIG["timeout_seconds"],
        ) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Agent API returned HTTP {exc.code}: {body}") from exc
    except error.URLError as exc:
        raise RuntimeError(f"Could not reach agent API: {exc}") from exc


def extract_response_text(response_json):
    choices = response_json.get("choices") or []
    if not choices:
        raise RuntimeError(f"Agent response does not contain choices: {response_json}")

    message = choices[0].get("message") or {}
    content = message.get("content", "")

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))
        return "\n".join(text_parts).strip()

    return str(content).strip()


def extract_first_json_block(text):
    start_index = text.find("{")
    if start_index == -1:
        return None

    depth = 0
    for index in range(start_index, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start_index:index + 1]

    return None


def parse_prediction(raw_text):
    cleaned = raw_text.strip()

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed, None
    except json.JSONDecodeError:
        pass

    json_block = extract_first_json_block(cleaned)
    if json_block:
        try:
            parsed = json.loads(json_block)
            if isinstance(parsed, dict):
                return parsed, None
        except json.JSONDecodeError:
            pass

    fallback = {
        "category": "",
        "severity": "",
        "action": cleaned,
    }
    return fallback, "Agent response was not valid JSON; using raw text as action."


def append_log(record):
    log_file = AGENT_CONFIG["log_file"]
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def validate_config():
    if not AGENT_CONFIG["api_url"]:
        raise RuntimeError("Set AGENT_CONFIG['api_url'] before running this script.")
    if not AGENT_CONFIG["api_key"]:
        raise RuntimeError("Set AGENT_API_KEY in .env before running this script.")


def run_single_evaluation():
    env = SecurityEnv()
    observation = env.reset()
    expected = env.current_sample["expected"]
    selected_model = resolve_model()

    messages = build_messages(observation)
    response_json = call_agent(messages)
    raw_response = extract_response_text(response_json)
    predicted, parse_warning = parse_prediction(raw_response)

    result = env.step(predicted)
    score = result["reward"]

    feedback_response = None
    if AGENT_CONFIG["send_feedback_to_agent"]:
        feedback_messages = messages + [
            {
                "role": "assistant",
                "content": raw_response,
            },
            build_feedback_message(observation, expected, predicted, score),
        ]
        feedback_json = call_agent(feedback_messages)
        feedback_response = extract_response_text(feedback_json)

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": {
            "system": observation["system"],
            "log": observation["log"],
        },
        "prompt": observation["agent_prompt"],
        "expected": expected,
        "predicted": predicted,
        "raw_response": raw_response,
        "score": score,
        "parse_warning": parse_warning,
        "feedback_response": feedback_response,
        "provider": get_provider_host(),
        "model_used": selected_model,
    }
    append_log(record)
    return record


def main():
    validate_config()

    for run_number in range(1, AGENT_CONFIG["runs"] + 1):
        record = run_single_evaluation()
        print(f"Run {run_number}")
        print(f"Provider: {record['provider']}")
        print(f"Model used: {record['model_used']}")
        print(f"Query system: {record['query']['system']}")
        print(f"Query log: {record['query']['log']}")
        print(f"Expected: {json.dumps(record['expected'])}")
        print(f"Predicted: {json.dumps(record['predicted'])}")
        print(f"Score: {record['score']}")
        print(f"Log file: {AGENT_CONFIG['log_file']}")
        if record["parse_warning"]:
            print(f"Warning: {record['parse_warning']}")
        if record["feedback_response"]:
            print(f"Feedback response: {record['feedback_response']}")
        print("-" * 60)


if __name__ == "__main__":
    main()
