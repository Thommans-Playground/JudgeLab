"""A connector for OpenAI-compatible Chat Completions endpoints.

References:
* SDK defaults, retries, timeouts, errors, request IDs:
  https://github.com/openai/openai-python
* Request and response shape:
  https://developers.openai.com/api/reference/resources/chat
* Error codes, including billing errors sent as HTTP 429:
  https://developers.openai.com/api/docs/guides/error-codes
"""

import time

import openai
from openai import OpenAI
from openai.types.chat import ChatCompletion

from judgelab.connectors.credentials import read_secret
from judgelab.connectors.errors import (
    ConnectorAuthError,
    ConnectorError,
    ConnectorQuotaError,
    ConnectorRateLimitError,
    ConnectorRequestError,
    ConnectorResponseError,
    ConnectorUnavailableError,
)
from judgelab.connectors.response import ModelResponse

OPENAI_DEFAULT_BASE_URL = "https://api.openai.com/v1"

# HTTP 429 responses that mean "out of credit or over a limit", not "slow down".
QUOTA_ERROR_CODES = {
    "insufficient_quota",
    "credit_balance_exhausted",
    "organization_spend_limit_exceeded",
    "project_spend_limit_exceeded",
    "organization_usage_limit_exceeded",
}


class OpenAIConnector:
    """Sends one prompt to an OpenAI-compatible Chat Completions endpoint."""

    def __init__(
        self,
        *,
        model: str,
        api_key_env: str,
        base_url: str | None = None,
        timeout_s: float = 60.0,
        max_retries: int = 0,
        http_client=None,
    ) -> None:
        self.model = model
        self.base_url = base_url or OPENAI_DEFAULT_BASE_URL
        self._client = OpenAI(
            api_key=read_secret(api_key_env),
            base_url=self.base_url,
            timeout=timeout_s,
            max_retries=max_retries,
            http_client=http_client,
        )

    def __repr__(self) -> str:
        return f"OpenAIConnector(model={self.model!r}, base_url={self.base_url!r})"

    def generate(self, prompt: str) -> ModelResponse:
        messages = [{"role": "user", "content": prompt}]
        start = time.perf_counter()
        try:
            completion = self._client.chat.completions.create(model=self.model, messages=messages)
        except openai.APIError as e:
            raise translate_error(e) from e
        latency_ms = (time.perf_counter() - start) * 1000

        if not isinstance(completion, ChatCompletion):
            raise ConnectorResponseError(
                f"expected a chat completion, got {type(completion).__name__}"
            )

        request_id = completion._request_id

        if not completion.choices:
            raise ConnectorResponseError("response has no choices", request_id=request_id)
        choice = completion.choices[0]
        if choice.message.content is None and choice.message.refusal is None:
            raise ConnectorResponseError(
                "response has neither content nor refusal", request_id=request_id
            )

        usage = completion.usage
        return ModelResponse(
            text=choice.message.content,
            refusal=choice.message.refusal,
            requested_model=self.model,
            served_model=completion.model,
            finish_reason=choice.finish_reason,
            prompt_tokens=usage.prompt_tokens if usage else None,
            completion_tokens=usage.completion_tokens if usage else None,
            request_id=request_id,
            latency_ms=latency_ms,
        )


def translate_error(e: openai.APIError) -> ConnectorError:
    """Map the SDK's exception family onto JudgeLab's."""
    if isinstance(e, openai.APIConnectionError):  # includes APITimeoutError
        kind = "timed out" if isinstance(e, openai.APITimeoutError) else "connection failed"
        return ConnectorUnavailableError(f"request {kind}")
    if isinstance(e, openai.APIStatusError):
        status, request_id, code = e.status_code, e.request_id, e.code
        detail = f"HTTP {status}" + (f" ({code})" if code else "")
        kwargs = {"status_code": status, "request_id": request_id}
        if status in (401, 403):
            return ConnectorAuthError(detail, **kwargs)
        if status == 402 or code in QUOTA_ERROR_CODES:
            return ConnectorQuotaError(detail, **kwargs)
        if status == 429:
            return ConnectorRateLimitError(detail, **kwargs)
        if status >= 500 or status in (408, 409):
            return ConnectorUnavailableError(detail, **kwargs)
        return ConnectorRequestError(detail, **kwargs)
    return ConnectorResponseError(f"unexpected SDK error: {type(e).__name__}")
