# Meta Hackathon Openenv

This environment serves random cybersecurity log-analysis tasks.

The agent must return only JSON in this shape:

```json
{
  "category": "brute_force",
  "severity": "high",
  "action": "block source IP and enable rate limiting"
}
```

Scoring uses cosine similarity between vectorized predicted and expected responses.
The raw cosine value is mapped from `[-1, 1]` into a reward in `[0, 1]`, so:

- aligned vectors score `1`
- opposite vectors score `0`

`GET /reset` now includes `instructions`, `response_example`, and `agent_prompt`
so an OpenAI runner can pass the exact answer contract to the model together
with the sampled log.
