"""Wraps calls to the Anthropic API.

Only Claude is wired up for now. If other LLM providers are added later, this is the
one file that changes -- tabs never call the SDK directly.
"""
import anthropic

# Used only if a live model list can't be fetched (e.g. no API key yet, or a network error).
FALLBACK_MODELS = [
    "claude-sonnet-4-6",
    "claude-opus-4-1-20250805",
    "claude-haiku-4-5-20251001",
]


def get_client(api_key: str) -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=api_key)


def list_models(api_key: str) -> list[str]:
    """Return available Claude model IDs from the API so the app doesn't go stale.
    Falls back to a static list if there's no key yet or the call fails.
    """
    if not api_key:
        return FALLBACK_MODELS
    try:
        client = get_client(api_key)
        response = client.models.list(limit=20)
        models = [m.id for m in response.data]
        return models or FALLBACK_MODELS
    except Exception:
        return FALLBACK_MODELS


def send_prompt(api_key: str, model: str, system: str, user_content: str, max_tokens: int = 4096) -> str:
    """Single-turn call to Claude. Returns the concatenated text of the response.

    Always streams rather than using messages.create(). The API requires streaming for any
    request that might take a long time to generate (the SDK raises an explicit error for
    this on large max_tokens / long input rather than silently hanging), and a non-streaming
    call that runs long can also come back with an empty or partial response instead of a
    clean error. Streaming avoids both failure modes and works identically for short calls
    too, so there's one code path regardless of how big the request is.
    """
    client = get_client(api_key)
    text_parts = []
    with client.messages.stream(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user_content}],
    ) as stream:
        for text in stream.text_stream:
            text_parts.append(text)
    return "".join(text_parts)
