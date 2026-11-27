"""Connectors: adapters that let JudgeLab call foundation models."""

from judgelab.connectors.errors import (
    ConnectorAuthError,
    ConnectorError,
    ConnectorQuotaError,
    ConnectorRateLimitError,
    ConnectorRequestError,
    ConnectorResponseError,
    ConnectorUnavailableError,
)
from judgelab.connectors.openai_connector import OpenAIConnector
from judgelab.connectors.response import ModelResponse

__all__ = [
    "ConnectorAuthError",
    "ConnectorError",
    "ConnectorQuotaError",
    "ConnectorRateLimitError",
    "ConnectorRequestError",
    "ConnectorResponseError",
    "ConnectorUnavailableError",
    "ModelResponse",
    "OpenAIConnector",
]
