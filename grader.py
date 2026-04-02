import hashlib
import json
import math
import re


CATEGORIES = ["brute_force", "malware", "phishing", "dos_attack", "normal"]
SEVERITY_ANGLES = {
    "low": math.radians(150),
    "medium": math.radians(90),
    "high": math.radians(30),
}

CATEGORY_WEIGHT = 0.3
SEVERITY_WEIGHT = 0.2
ACTION_WEIGHT = 0.5
ACTION_VECTOR_SIZE = 128
TOKEN_PATTERN = re.compile(r"[a-z0-9_]+")


def _safe_text(value):
    return str(value or "").strip().lower()


def _normalize_payload(payload):
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            payload = {"action": payload}

    if not isinstance(payload, dict):
        payload = {}

    return {
        "category": _safe_text(payload.get("category")),
        "severity": _safe_text(payload.get("severity")),
        "action": _safe_text(payload.get("action")),
    }


def _normalize_vector(values):
    norm = math.sqrt(sum(value * value for value in values))
    if norm == 0.0:
        return values

    return [value / norm for value in values]


def _centered_one_hot(value, vocabulary):
    if value not in vocabulary:
        return [0.0] * len(vocabulary)

    off_value = -1.0 / (len(vocabulary) - 1)
    vector = [off_value] * len(vocabulary)
    vector[vocabulary.index(value)] = 1.0
    return _normalize_vector(vector)


def _severity_vector(value):
    angle = SEVERITY_ANGLES.get(value)
    if angle is None:
        return [0.0, 0.0]

    return [math.cos(angle), math.sin(angle)]


def _hash_feature(feature):
    digest = hashlib.sha256(feature.encode("utf-8")).digest()
    index = int.from_bytes(digest[:4], "big") % ACTION_VECTOR_SIZE
    sign = 1.0 if digest[4] % 2 == 0 else -1.0
    return index, sign


def _action_vector(action):
    tokens = TOKEN_PATTERN.findall(action)
    if not tokens:
        return [0.0] * ACTION_VECTOR_SIZE

    vector = [0.0] * ACTION_VECTOR_SIZE

    for token in tokens:
        index, sign = _hash_feature(token)
        vector[index] += sign

    for left, right in zip(tokens, tokens[1:]):
        index, sign = _hash_feature(f"{left}_{right}")
        vector[index] += 0.5 * sign

    return _normalize_vector(vector)


def response_to_vector(payload):
    normalized = _normalize_payload(payload)
    category_vector = [
        value * CATEGORY_WEIGHT
        for value in _centered_one_hot(normalized["category"], CATEGORIES)
    ]
    severity_vector = [
        value * SEVERITY_WEIGHT
        for value in _severity_vector(normalized["severity"])
    ]
    action_vector = [
        value * ACTION_WEIGHT
        for value in _action_vector(normalized["action"])
    ]

    return category_vector + severity_vector + action_vector


def cosine_similarity(left, right):
    dot = sum(left_value * right_value for left_value, right_value in zip(left, right))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))

    if left_norm == 0.0 or right_norm == 0.0:
        return 0.0

    cosine = dot / (left_norm * right_norm)
    return max(-1.0, min(1.0, cosine))


def grade_response(predicted, expected):
    predicted_vector = response_to_vector(predicted)
    expected_vector = response_to_vector(expected)
    cosine = cosine_similarity(predicted_vector, expected_vector)

    # Maps cosine similarity from [-1, 1] into the required reward range [0, 1].
    return round((cosine + 1.0) / 2.0, 4)
