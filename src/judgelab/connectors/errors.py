"""Connector errors: a call failed, so we don't know what the model did (ERROR)."""


class ConnectorError(Exception):
    """Base class for every connector failure.

    Messages carry the status code, the provider's short error code and the
    request id, but never the API key or the provider's free-text message,
    which can echo part of the key.
    """

    def __init__(
        self, message: str, *, status_code: int | None = None, request_id: str | None = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.request_id = request_id


class ConnectorAuthError(ConnectorError):
    """Missing, invalid or unauthorised credentials. Fix the configuration."""


class ConnectorQuotaError(ConnectorError):
    """Out of credit or over a spend limit. Every call will fail until a human acts."""


class ConnectorRateLimitError(ConnectorError):
    """Too many requests. Retrying later may help."""


class ConnectorUnavailableError(ConnectorError):
    """Timeout, connection failure or server error. Retrying may help."""


class ConnectorRequestError(ConnectorError):
    """The provider rejected the request itself, e.g. an unknown model."""


class ConnectorResponseError(ConnectorError):
    """The provider replied, but not with something we can trust as an answer."""
