"""Credential resolution: the only place JudgeLab reads a secret."""

import os

from judgelab.connectors.errors import ConnectorAuthError


def read_secret(env_name: str) -> str:
    """Return the value of the environment variable named `env_name`.
    Errors name the variable, never a value.
    """
    value = os.environ.get(env_name, "").strip()
    if not value:
        raise ConnectorAuthError(f"environment variable {env_name} is not set")
    return value
