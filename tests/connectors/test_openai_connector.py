"""OpenAIConnector tests against a fake HTTP server (httpx2.MockTransport).

The real `openai` SDK runs unchanged; only the network is replaced.
"""

import httpx2
import pytest

from judgelab.connectors import (
    OpenAIConnector,
)
from judgelab.connectors.errors import ConnectorAuthError

KEY_ENV = "JUDGELAB_TEST_OPENAI_KEY"
SECRET = "sk-test-SECRET-VALUE-1234"


def completion(content="Paris", *, refusal=None, finish="stop", choices=True, usage=True):
    message = {"role": "assistant", "content": content, "refusal": refusal}
    body = {
        "id": "chatcmpl-1",
        "object": "chat.completion",
        "created": 0,
        "model": "served-model-v2",
        "choices": [{"index": 0, "finish_reason": finish, "message": message}] if choices else [],
    }
    if usage:
        body["usage"] = {"prompt_tokens": 12, "completion_tokens": 1, "total_tokens": 13}
    return body


def server(status=200, *, body=None, text=None, raises=None, seen=None):
    """A fake OpenAI server. Records each request in `seen` if given."""

    def handler(request):
        if seen is not None:
            seen.append(request)
        if raises:
            raise raises(request)
        headers = {"x-request-id": "req_1"}
        if text is not None:
            return httpx2.Response(status, text=text, headers=headers)
        return httpx2.Response(status, json=body, headers=headers)

    return httpx2.Client(transport=httpx2.MockTransport(handler))


def error_body(code=None):
    return {"error": {"message": f"Incorrect key: {SECRET[:7]}****", "type": "x", "code": code}}


@pytest.fixture
def connect(monkeypatch):
    monkeypatch.setenv(KEY_ENV, SECRET)

    def make(client, **kwargs):
        return OpenAIConnector(
            model="asked-model",
            api_key_env=KEY_ENV,
            base_url="http://stub.local/v1",
            http_client=client,
            **kwargs,
        )

    return make


# --- construction ---------------------------------------------------------------


@pytest.mark.acceptance("AC-001-01", "AC-001-08")
@pytest.mark.parametrize("value", [None, "", "   "])
def test_missing_key_names_the_variable(monkeypatch, value):
    if value is None:
        monkeypatch.delenv("NOT_SET_ANYWHERE", raising=False)
    else:
        monkeypatch.setenv("NOT_SET_ANYWHERE", value)
    with pytest.raises(ConnectorAuthError, match="NOT_SET_ANYWHERE is not set"):
        OpenAIConnector(model="m", api_key_env="NOT_SET_ANYWHERE")
