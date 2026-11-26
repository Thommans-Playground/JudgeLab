# Codealong 1: Building an OpenAI Connector

In this codealong you are going to build your first connector, the piece of JudgeLab that sends a prompt to a foundation model and brings back an answer. By the end you will have an `OpenAIConnector` class running in your notebook that talks to OpenAI (or anything that speaks OpenAI's Chat Completions format), returns its results in JudgeLab's own terms, and turns every way a call can fail into an error you understand.

This is a concrete connector, written for one provider only. That is on purpose. Once it works, we will look at it together and pull out the parts that would be true for *any* provider, and that will become the abstract connector. Building the concrete version first means the abstraction is discovered from working code instead of being guessed.

> **AI-Assist level:** this is a guided codealong, so record your work as **L4**.

## 1.1 Before You Start

You are going to work in `sandbox/2_openai_sdk.ipynb`. Make sure the notebook is using the project's virtual environment. The kernel picker in the top-right corner should say `.venv (Python 3.14.7)`. You also need a `.env` file in the root of the project with two variables in it:

```text
OPENAI_API_KEY=your-key
OPENAI_MODEL=a-model-id
```

I strongly recommend that you type the code yourself instead of copying and pasting it. It is slower, but your fingers will remember things your eyes skip over, and the typos you make (and fix) are part of the learning.

## 1.2 The Setup Cell

Let's start by clearing out the first cell of the notebook and replacing it with the imports the connector needs.

_sandbox/2_openai_sdk.ipynb_: Setup cell

```python
import os
import time
from dataclasses import dataclass

import openai
from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletion

load_dotenv()
```

The `load_dotenv()` call reads your `.env` file and copies its values into `os.environ`, the dictionary where Python keeps environment variables. That is all it does.

If you compare this with your earlier version, you will notice that something is missing: there are no `OPENAI_API_KEY = os.environ.get(...)` lines at the top. This is a deliberate change. When you store the key in a global variable and then use that variable as a default argument, Python evaluates the default once, when the function is defined, and stores the actual key inside the function's signature. Anyone who runs `help(OpenAIConnector)` would see your key printed on the screen. From now on, the connector itself is going to look up the key, at the moment it needs it, and nowhere else.

## 1.3 A Home for the Results

Before the connector can return anything, it needs a type to return. You could just return the response object that the OpenAI SDK gives you, but then every other part of JudgeLab would have to know what an OpenAI response looks like. The day you add a second provider, all that code would break. So instead, let's define a small class in JudgeLab's own language.

_sandbox/2_openai_sdk.ipynb_: Result and error types

```python
@dataclass(frozen=True)
class ModelResponse:
    text: str | None
    refusal: str | None
    requested_model: str
    served_model: str
    finish_reason: str
    prompt_tokens: int | None
    completion_tokens: int | None
    request_id: str | None
    latency_ms: float


class ConnectorError(Exception):
    def __init__(self, message: str, *, status_code: int | None = None,
                 request_id: str | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.request_id = request_id


class ConnectorAuthError(ConnectorError): ...
class ConnectorRateLimitError(ConnectorError): ...
class ConnectorUnavailableError(ConnectorError): ...
class ConnectorRequestError(ConnectorError): ...
class ConnectorResponseError(ConnectorError): ...
```

The `ModelResponse` class is a dataclass, which means Python writes the constructor and the `__repr__()` method for you based on the fields. The `frozen=True` option makes instances read-only after they are created. A model's answer is evidence in an evaluation, and evidence should not be quietly edited later.

Two of the fields deserve a closer look. There is a `requested_model` and a `served_model`, because the model you ask for and the model that actually answers are not always the same. Providers resolve aliases to specific versions, and gateways sometimes route requests elsewhere. And there is a `refusal` field next to `text`, because a model that declines to answer has still *done something*. In a safety evaluation, refusing is often exactly the behavior you are hoping to see, so it is an outcome to record, not an error.

The errors are organized as a small family. All five subclasses inherit from `ConnectorError`, which means that code calling the connector can catch the whole family with a single `except ConnectorError`, or a specific member when it cares about the difference. You can verify this in a new cell:

```python
>>> issubclass(ConnectorRateLimitError, ConnectorError)
True
```

Each error carries an optional `status_code` and `request_id`. The request id is the reference number the provider gives every call, and it is the first thing their support team asks for when you report a problem.

## 1.4 Creating the Connector

Now you are ready to write the connector class itself, starting with its constructor.

_sandbox/2_openai_sdk.ipynb_: The connector class

```python
OPENAI_DEFAULT_BASE_URL = "https://api.openai.com/v1"


class OpenAIConnector:
    def __init__(self, *, model: str, api_key_env: str = "OPENAI_API_KEY",
                 base_url: str | None = None, timeout_s: float = 30.0,
                 max_retries: int = 0, http_client=None) -> None:
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise ConnectorAuthError(f"environment variable {api_key_env} is not set")

        self.model = model
        self.base_url = base_url or OPENAI_DEFAULT_BASE_URL
        self._client = OpenAI(
            api_key=api_key,
            base_url=self.base_url,
            timeout=timeout_s,
            max_retries=max_retries,
            http_client=http_client,
        )

    def __repr__(self) -> str:
        return f"OpenAIConnector(model={self.model!r}, base_url={self.base_url!r})"
```

There is a lot going on in these few lines, so let's go through it.

The `*` at the start of the argument list makes every argument keyword-only. You cannot write `OpenAIConnector("gpt-x", "OPENAI_API_KEY")`, you have to write `OpenAIConnector(model="gpt-x", api_key_env="OPENAI_API_KEY")`. With two string arguments next to each other, it would be very easy to pass them in the wrong order, and Python would never warn you.

The `api_key_env` argument does not receive a key. It receives the *name* of the environment variable where the key lives. The constructor looks up that name, and if the variable is not set, it raises a `ConnectorAuthError` whose message names the variable, but never shows a value.

Next, the constructor creates the SDK's client and stores it in `self._client`. The leading underscore is a Python convention that says "this is internal, please don't touch it from outside." Note that every setting is passed explicitly, even the ones that have defaults. This is because the SDK's defaults turned out to be surprising when we studied it: it silently retries failed requests twice, it waits up to ten minutes for a reply, and it reads `OPENAI_API_KEY` and `OPENAI_BASE_URL` from the environment on its own if you don't give it values. By passing everything in, the connector behaves the same way on every computer, regardless of what environment variables happen to be lying around. The `max_retries=0` default in particular means that no request will ever be retried behind your back.

The `http_client` argument is there for testing. If you pass nothing, the SDK uses its normal network client. Later in this codealong you are going to pass a fake one to simulate failures that are hard to produce on demand.

Finally, notice what the constructor does *not* do: it never stores the key on `self`. It hands it straight to the SDK client and forgets about it. And the `__repr__()` method, which controls what you see when you print the connector, only shows the model and the URL.

Let's see if all of this works. Add a new cell:

```python
>>> c = OpenAIConnector(model=os.environ["OPENAI_MODEL"])
>>> print(c)
OpenAIConnector(model='your-model-id', base_url='https://api.openai.com/v1')
>>> OpenAIConnector(model="x", api_key_env="DOES_NOT_EXIST")
ConnectorAuthError: environment variable DOES_NOT_EXIST is not set
```

You should see your own model id in the first output. The second command raises an error on purpose, and if you look carefully at the message, it tells you exactly which variable is missing without revealing anything secret. No requests have been sent to OpenAI yet, so this step costs nothing.

## 1.5 Sending a Prompt

Believe it or not, you are only one method away from getting an answer from a model. Add the `generate()` method to the class, below `__repr__()`:

_sandbox/2_openai_sdk.ipynb_: The `generate()` method (inside the class)

```python
    def generate(self, prompt: str) -> ModelResponse:
        messages = [{"role": "user", "content": prompt}]

        start = time.perf_counter()
        completion = self._client.chat.completions.create(
            model=self.model, messages=messages)
        latency_ms = (time.perf_counter() - start) * 1000

        choice = completion.choices[0]
        usage = completion.usage
        return ModelResponse(
            text=choice.message.content,
            refusal=choice.message.refusal,
            requested_model=self.model,
            served_model=completion.model,
            finish_reason=choice.finish_reason,
            prompt_tokens=usage.prompt_tokens if usage else None,
            completion_tokens=usage.completion_tokens if usage else None,
            request_id=completion._request_id,
            latency_ms=latency_ms,
        )
```

This method follows a pattern that you are going to see in every connector you ever write, including the ones in Project Moonshot. First, it translates JudgeLab's request into the provider's format, which for Chat Completions is a list of messages with roles. Then it sends the request. Finally, it translates the provider's reply back into a `ModelResponse`.

The `time.perf_counter()` calls measure how long the request took, in milliseconds. And you may be wondering about `completion._request_id`, since I told you before that names that start with an underscore are internal. In general that is true, but the OpenAI SDK's README makes an explicit exception for this one: it is documented as public, so it is safe to use. When in doubt, the README's "Request IDs" section is where you can confirm this.

The `usage` attribute can be `None` with some OpenAI-compatible servers, which is why the token counts are only read when it exists.

Are you ready to talk to a real model? Add a new cell:

```python
>>> c = OpenAIConnector(model=os.environ["OPENAI_MODEL"])
>>> c.generate("What is the capital of France? One word.")
ModelResponse(text='Paris', refusal=None, requested_model='your-model-id', served_model='your-model-id-2026-11-01', finish_reason='stop', prompt_tokens=16, completion_tokens=1, request_id='req_abc123', latency_ms=812.4)
```

Your model names, token counts, request id and latency will be different, but the shape should match. Take a moment to compare `requested_model` and `served_model`. If they are different, you are seeing in practice why both fields exist.

This request costs a tiny fraction of a cent.

## 1.6 Not Trusting a Successful Reply

The version of `generate()` that you have now works fine when everything goes well, but it trusts the reply completely. When we studied the SDK, two things came up that make this a bad idea. A misbehaving gateway sent back an HTML page with a `200 OK` status, and the SDK returned it as a plain string, without raising any error. And a perfectly valid reply can have `None` as its content.

Let's add some checks. Insert these lines in `generate()`, right after the `latency_ms` line and before `choice = completion.choices[0]`:

_sandbox/2_openai_sdk.ipynb_: Reply checks (inside `generate()`)

```python
        if not isinstance(completion, ChatCompletion):
            raise ConnectorResponseError(
                f"expected a chat completion, got {type(completion).__name__}")
        if not completion.choices:
            raise ConnectorResponseError(
                "response has no choices", request_id=completion._request_id)
        message = completion.choices[0].message
        if message.content is None and message.refusal is None:
            raise ConnectorResponseError(
                "response has neither content nor refusal", request_id=completion._request_id)
```

The first check confirms that the SDK really gave you a chat completion and not something else. The second makes sure there is at least one choice to read from. The third is the most interesting one. Notice that a reply with no content but with a refusal is allowed through. That is the refusal outcome we discussed in section 1.3, and it reaches the caller as a normal `ModelResponse`. Only a reply that has *neither* an answer nor a refusal is rejected, because in that case we really don't know what the model did.

## 1.7 Translating Errors

There is one big piece left. When something goes wrong, the OpenAI SDK raises its own exceptions: `openai.AuthenticationError`, `openai.RateLimitError` and so on. If you let those escape from the connector, every caller would need to know about them, and the day you add a Claude connector, the callers would also need to know about Anthropic's exceptions. The connector's job is to absorb these differences, so let's write a function that translates the SDK's exceptions into JudgeLab's.

Add this function in a new cell, below the class:

_sandbox/2_openai_sdk.ipynb_: Error translation

```python
def translate_error(e: openai.APIError) -> ConnectorError:
    if isinstance(e, openai.APIConnectionError):
        kind = "timed out" if isinstance(e, openai.APITimeoutError) else "connection failed"
        return ConnectorUnavailableError(f"request {kind}")
    if isinstance(e, openai.APIStatusError):
        status, rid = e.status_code, e.request_id
        detail = f"HTTP {status}" + (f" ({e.code})" if e.code else "")
        if status in (401, 403):
            return ConnectorAuthError(detail, status_code=status, request_id=rid)
        if status == 429:
            return ConnectorRateLimitError(detail, status_code=status, request_id=rid)
        if status >= 500 or status in (408, 409):
            return ConnectorUnavailableError(detail, status_code=status, request_id=rid)
        return ConnectorRequestError(detail, status_code=status, request_id=rid)
    return ConnectorResponseError(f"unexpected SDK error: {type(e).__name__}")
```

The SDK organizes its exceptions in a tree, which is described in the "Handling errors" section of its README. Problems where the server never answered, such as a dropped connection or a timeout, are subclasses of `APIConnectionError`. Problems where the server did answer but with an error code are subclasses of `APIStatusError`, and these have a `status_code` attribute. The function walks down this tree and picks the matching JudgeLab error.

One aspect that may seem odd at first is that the error message only includes the status code and the provider's short error code, such as `invalid_api_key`. It does not include the provider's full error message. This is not an oversight. When you send a bad key, OpenAI's message repeats part of the key back to you, and that is not something you want to end up in a log file or a report.

Now you need to use this function. In `generate()`, replace the line that calls `chat.completions.create()` with this version:

_sandbox/2_openai_sdk.ipynb_: Wrapping the request (inside `generate()`)

```python
        try:
            completion = self._client.chat.completions.create(
                model=self.model, messages=messages)
        except openai.APIError as e:
            raise translate_error(e) from e
```

The `from e` at the end chains the two exceptions together. The caller sees a `ConnectorError`, but if you ever need to debug a problem, the original SDK exception is still attached to it as its cause.

Remember to re-run the cell with the class after you change it. The notebook keeps the old version of the class in memory until you do.

## 1.8 Seeing the Errors in Action

It would be nice to see every kind of failure before calling this done, but some of them are hard to produce on purpose. You can't easily make OpenAI rate-limit you or have one of its servers crash on demand. This is where the `http_client` argument comes in. The `httpx2` package, which the OpenAI SDK uses to talk to the network, has a `MockTransport` class that answers requests by calling a function of yours instead of going out to the internet. The real SDK runs unchanged, only the network is fake.

Add this cell:

_sandbox/2_openai_sdk.ipynb_: A fake server

```python
import httpx2

def fake_server(status=None, raise_exc=None):
    def handler(request):
        if raise_exc:
            raise raise_exc(request)
        return httpx2.Response(status, json={"error": {"message": "x", "code": "c"}},
                               headers={"x-request-id": "req_demo"})
    return httpx2.Client(transport=httpx2.MockTransport(handler))

cases = {
    "429": fake_server(429),
    "500": fake_server(500),
    "timeout": fake_server(raise_exc=lambda r: httpx2.ReadTimeout("t", request=r)),
}
for name, client in cases.items():
    try:
        OpenAIConnector(model="m", http_client=client, base_url="http://stub/v1").generate("hi")
    except ConnectorError as e:
        print(f"{name:8} → {type(e).__name__}: {e}")
```

When you run this cell, you should see this output:

```text
429      → ConnectorRateLimitError: HTTP 429 (c)
500      → ConnectorUnavailableError: HTTP 500 (c)
timeout  → ConnectorUnavailableError: request timed out
```

Do you see how fast that was? Every case came back instantly, after a single attempt. If you had used the SDK's defaults, the 429 and the 500 would each have been retried twice, with pauses in between, before you heard anything about them.

You can also produce two failures with the real OpenAI service, and these two are free, because the request is rejected before any text is generated:

```python
>>> OpenAIConnector(model="no-such-model-xyz").generate("hi")
ConnectorRequestError: HTTP 404 (model_not_found)
>>> os.environ["BAD_KEY"] = "sk-wrong"
>>> OpenAIConnector(model=os.environ["OPENAI_MODEL"], api_key_env="BAD_KEY").generate("hi")
ConnectorAuthError: HTTP 401 (invalid_api_key)
```

If you catch these errors and print their `status_code` and `request_id` attributes, you will see that both are filled in.

## 1.9 Troubleshooting

Did you have trouble getting the connector to work? These are the most common problems:

- **`KeyError: 'OPENAI_MODEL'`, or `environment variable OPENAI_API_KEY is not set`.** The notebook can't see your `.env` file. Make sure `load_dotenv()` ran in the setup cell, and that `.env` is in the root folder of the project.
- **`ModuleNotFoundError: No module named 'dotenv'`** (or `httpx2`). The notebook is using the wrong Python. Select the `.venv` kernel and restart it.
- **Your changes to the class don't seem to have any effect.** You edited the class but did not re-run its cell, or you re-ran the class but not the cells that create the connector. When in doubt, use "Restart Kernel and Run All".
- **Saving the notebook removed an import you just added.** Ruff's fix-on-save deletes imports that are not used yet. Write the code that uses the import, then save.

## 1.10 Exercises

1. Write a fake server that returns `200 OK` with the body `<html>gateway</html>` (use `httpx2.Response(200, text=...)`), and confirm that you get a `ConnectorResponseError` instead of a crash.
2. Write a fake server that returns a valid completion where `content` is `null`, `refusal` is `"I can't help with that."`, and `finish_reason` is `"content_filter"`. Check that `generate()` returns a `ModelResponse` and does not raise.
3. Set `OPENAI_BASE_URL` to `http://somewhere-else.example/v1` in `os.environ` and create a connector without a `base_url` argument. Print it. Which URL does it use, and why?
4. Without looking at the code, explain out loud the four steps that `generate()` follows. If you get stuck on one of them, that is the part to reread.

## 1.11 Wrapping Up

Congratulations, you now have a working connector! It sends a prompt to an OpenAI-compatible model, records which model actually answered and how, treats refusals as answers instead of failures, refuses to trust a reply it can't make sense of, and turns every failure into a JudgeLab error that does not leak your key.

Right now everything lives in a notebook, and everything is OpenAI-specific. In the next codealong you are going to move this code into the `src/judgelab/connectors` package with proper pytest tests, and then look at it with fresh eyes to separate the OpenAI-specific parts from the ones that any provider would need. That second group is the abstract connector.
