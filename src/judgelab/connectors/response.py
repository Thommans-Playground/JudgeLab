"""The result of one model call, in JudgeLab's own terms."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelResponse:
    """What JudgeLab keeps from one model call.

    Either `text` or `refusal` is set. A refusal is a real model outcome
    (the judge decides whether refusing was right), not an error.
    """

    text: str | None
    refusal: str | None
    requested_model: str
    served_model: str
    finish_reason: str
    prompt_tokens: int | None
    completion_tokens: int | None
    request_id: str | None
    latency_ms: float
