"""OpenAIConnector tests against a fake HTTP server (httpx2.MockTransport).

The real `openai` SDK runs unchanged; only the network is replaced.
"""

import httpx2
import pytest

from judgelab.connectors import (
    OpenAIConnector,
)
from judgelab.connectors.errors import ConnectorAuthError
from judgelab.connectors.response import ModelResponse

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


@pytest.mark.acceptance("AC-001-02")
def test_environment_defaults_have_no_effect(connect, monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", "http://somewhere-else.example/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-wrong-key-from-env")
    seen = []
    connect(server(body=completion(), seen=seen)).generate("hi")
    assert str(seen[0].url) == "http://stub.local/v1/chat/completions"
    assert seen[0].headers["authorization"] == f"Bearer {SECRET}"


@pytest.mark.acceptance("AC-001-02")
def test_default_base_url_is_openai(monkeypatch):
    monkeypatch.setenv(KEY_ENV, SECRET)
    monkeypatch.setenv("OPENAI_BASE_URL", "http://somewhere-else.example/v1")
    connector = OpenAIConnector(model="m", api_key_env=KEY_ENV)
    assert connector.base_url == "https://api.openai.com/v1"


@pytest.mark.acceptance("AC-001-08")
def test_repr_shows_model_and_url_only(connect):
    connector = connect(server(body=completion()))
    assert (
        repr(connector) == "OpenAIConnector(model='asked-model', base_url='http://stub.local/v1')"
    )


# --- successful replies --------------------------------------------------------------
@pytest.mark.acceptance("AC-001-03")
def test_returns_answer_and_metadata(connect):
    response = connect(server(body=completion())).generate("Capital of France?")
    assert response == ModelResponse(
        text="Paris",
        refusal=None,
        requested_model="asked-model",
        served_model="served-model-v2",
        finish_reason="stop",
        prompt_tokens=12,
        completion_tokens=1,
        request_id="req_1",
        latency_ms=response.latency_ms,
    )
    assert response.latency_ms >= 0
