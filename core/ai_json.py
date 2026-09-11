"""Parses the JSON that tabs ask Claude to return, giving a clear diagnosis when the
response was cut off before finishing -- the most common cause of a JSON parse failure
here, almost always because max_tokens was too low for how much the model had to say.
"""
import json
import re


class ResponseTruncatedError(Exception):
    """The response looks like it was cut off mid-JSON (ends inside a string or without
    a closing brace) rather than being malformed for some other reason."""


def parse_json_response(raw: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        if not cleaned.endswith("}"):
            raise ResponseTruncatedError(
                f"Response was cut off before it finished ({len(cleaned)} characters received, "
                f"doesn't end with a closing brace). Try raising max output tokens or switching "
                f"to a model with a higher output limit."
            ) from e
        raise
