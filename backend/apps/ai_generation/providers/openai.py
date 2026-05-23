import json

from django.conf import settings


class AIProviderError(Exception):
    """Raised when the configured AI provider cannot return a usable response."""


def call_openai_question_suggestion(*, prompt, response_schema, model_name=None):
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise AIProviderError(
            "The OpenAI package is not installed. Install requirements/base.txt."
        ) from exc

    if not settings.OPENAI_API_KEY:
        raise AIProviderError("OPENAI_API_KEY is not configured.")

    client = OpenAI(
        api_key=settings.OPENAI_API_KEY,
        timeout=settings.OPENAI_TIMEOUT_SECONDS,
    )

    try:
        response = client.responses.create(
            model=model_name or settings.OPENAI_MODEL,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You support a reviewed educational question bank. "
                        "Return only structured JSON matching the supplied schema. "
                        "Do not create new topics; choose from the supplied topic list "
                        "when possible."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "question_intelligence_suggestion",
                    "strict": True,
                    "schema": response_schema,
                }
            },
        )
    except Exception as exc:
        raise AIProviderError(str(exc)) from exc

    output_text = getattr(response, "output_text", None)
    if not output_text:
        raise AIProviderError("OpenAI response did not include output_text.")

    try:
        payload = json.loads(output_text)
    except json.JSONDecodeError as exc:
        raise AIProviderError("OpenAI response was not valid JSON.") from exc

    raw_response = None
    if hasattr(response, "model_dump"):
        raw_response = response.model_dump(mode="json")

    return payload, raw_response
