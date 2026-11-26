# Codealong 4: A Claude Connector

In the last codealong you split the OpenAI connector into an abstract `ModelConnector` port and an OpenAI-specific adapter. That split looked good on paper, but so far only one real provider lives behind it, and an abstraction with a single implementation hasn't really been tested. In this codealong you are going to give it its first real test. By the end you will have an `AnthropicConnector` that talks to Claude through the official `anthropic` SDK, passes the same contract tests as the OpenAI connector, and maps Claude's own errors onto JudgeLab's error family.

Along the way you are going to discover something about the abstraction you built in chapter 3: it still had a little bit of OpenAI hiding inside it. A second implementation is the best way to find out what the first one was quietly assuming, and you'll fix that too.

> **AI-Assist level:** this is a guided codealong, so record this work as **AI-Assist L4**.

## 4.1 Before You Start

Start from an up-to-date `main`, with chapter 3 merged, and create the topic branch for this chapter:

```bash
$ git switch main && git pull --ff-only && git switch -c feat/p1-claude-connector-T014
```

You don't need a Claude API key for this chapter. Everything is tested against a fake HTTP server, the same way you tested the OpenAI connector, so none of the tests cost anything. If you do have a key, there is an optional live check at the end of section 4.8.

As always, I strongly recommend that you type the code yourself instead of copying and pasting it.

## 4.2 A New Task: T014

The v0.1 release plan has tasks T001 to T013, and none of them is "add a second provider". This is new work, so it gets its own task. You never invent a task id by hand. The `vbench-docs` skill has a script that picks the next free one and creates the file from the template:

```bash
$ python3 .claude/skills/vbench-docs/scripts/docids.py new T --title "Anthropic (Claude) connector" --release v0.1
T014
Created docs/releases/v0.1/tasks/T014.md
Next: list T014 in docs/releases/v0.1/README.md and add a row to docs/traceability.md
```

The script is telling you that it has done only part of the job. A task id that isn't listed anywhere is an orphan, so let's register it in the two places the message mentions. First, open [docs/releases/v0.1/README.md](../../docs/releases/v0.1/README.md), find the release plan table (the one with the `| Task | UC | Deliverable | Verification |` header), and add this row at the end, right after the T013 row:

_docs/releases/v0.1/README.md_: New row in the release plan table

```markdown
| T014 | UC-001 | Anthropic (Claude) connector | Fake HTTP + contract tests + live smoke test |
```

Next, in [docs/traceability.md](../../docs/traceability.md), three requirements are delivered by the connector tasks: REQ-003, REQ-004 and REQ-013. Add `T014` to the tasks column of each one, so the three rows look like this:

_docs/traceability.md_: Updated rows

```markdown
| REQ-003 | UC-001 | v0.1 | T001, T002, T003, T004, T014 | Config, connector, secret tests | Not started |
| REQ-004 | UC-001 | v0.1 | T001, T002, T003, T004, T014 | Config, connector, secret tests | Not started |
```

```markdown
| REQ-013 | UC-001 | v0.1 | T001, T002, T003, T004, T014 | Config, connector, secret tests | Not started |
```

REQ-013 is further down the table than the other two, which is why it's in its own block.

Now open the new task file. The script filled in the title and left the rest of the template empty. Fill in the use case, the requirements, the objective and, most importantly, the acceptance criteria. When you are done, the whole file should look like this:

_docs/releases/v0.1/tasks/T014.md_: The task file

```markdown
# T014: Anthropic (Claude) connector

| Field | Value |
|---|---|
| Release | v0.1 |
| Use case | UC-001 |
| Requirements | REQ-003, REQ-004, REQ-005, REQ-013 |
| Branch | `<type>/<prefix>-<slug>` |
| Status | Todo |
| AI-Assist | |

## Objective

A second, genuinely different provider behind the same `ModelConnector` port: Claude through the official `anthropic` SDK.

## Acceptance criteria

- [ ] **T014-AC1**: The client is configured only from its arguments; a missing key variable raises an auth error naming it, and `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN` and `ANTHROPIC_BASE_URL` in the environment have no effect.
- [ ] **T014-AC2**: A successful reply returns the text blocks joined (thinking blocks skipped), requested and served model, stop reason, token counts and request id.
- [ ] **T014-AC3**: A `refusal` stop reason is returned as a refusal response, not an error.
- [ ] **T014-AC4**: Truncation is reported the same way for every provider: `truncated` is true for OpenAI `length` and Claude `max_tokens`.
- [ ] **T014-AC5**: A reply with no text and no refusal raises a response error.
- [ ] **T014-AC6**: Failures map like the OpenAI connector's, including 402 billing and the spend-cap 429 as quota, and 529 overloaded as unavailable.
- [ ] **T014-AC7**: The Claude connector passes the shared connector contract tests.

## Approach

<!-- Plan, DSA/patterns to apply -->

## Verification

<!-- Tests to write / run -->

## Notes & lessons learned

-
```

Writing the acceptance criteria before any code is the most useful habit in this whole project. Each line is a promise that a test will keep, and every test you write later in this chapter carries a marker pointing back to one of these ids. Read them through once now. You'll notice that T014-AC4 talks about a `truncated` field that doesn't exist yet. That is the abstraction fix I mentioned in the introduction, and we'll get to it in section 4.5.

Finally, confirm that the docs are consistent:

```bash
$ python3 .claude/skills/vbench-docs/scripts/docids.py check
35 IDs defined · 0 error(s) · 0 warning(s)
```

If you forget the README row, the check reports `ERROR   T014: not listed in docs/releases/v0.1/README.md`, and if you forget traceability, you get a warning. The same check runs in CI, so it's better to see it fail here.

## 4.3 How Claude Is Different

Before writing any code, let's compare the two APIs. Both providers do the same basic job, take a list of messages and send back an answer, but the details differ in ways that matter. I find it helpful to think of the connector as a power adapter for travelling: the appliance (the rest of JudgeLab) is always the same, and each country's socket has a different shape. The adapter's job is to know about the socket so that the appliance never has to.

Here are the differences you'll handle in this chapter, and where each one lands in the code:

| Topic | OpenAI Chat Completions | Claude Messages API | Where it lands |
|---|---|---|---|
| Answer length limit | optional | `max_tokens` is **required** | constructor, default `16000` |
| Instructions | a `system` message in the list | a top-level `system` field | not needed yet (chapter 8) |
| The answer | one string in `message.content` | `content` is a **list of blocks**, which can include `thinking` blocks before the `text` ones | `generate()` joins only the `text` blocks |
| Why it stopped | `finish_reason`: `stop`, `length`, ... | `stop_reason`: `end_turn`, `max_tokens`, `refusal`, ... | `finish_reason` and the new `truncated` field |
| A refusal | `message.refusal` | `stop_reason == "refusal"`, with the reason in `stop_details.explanation` | `generate()` |
| Request id | `x-request-id` header | `request-id` header | `message._request_id` in both SDKs |
| Base URL | `https://api.openai.com/v1` | `https://api.anthropic.com` (the SDK adds `/v1/messages`) | `ANTHROPIC_DEFAULT_BASE_URL` |
| Errors | 429 can mean quota | 402 `billing_error`, spend-cap 429, 529 `overloaded_error` | `translate_error()` |

The first row deserves an explanation. On current Claude models thinking is always on, which means the model reasons for a while before it writes the answer, and the thinking tokens count toward `max_tokens`. If you set `max_tokens` to something small, like 100, the model can spend the whole budget thinking and never get to the answer. That's why the default is a generous 16000. It's a limit, not a target, and you only pay for the tokens the model actually uses.

The same reasoning explains the default timeout. A reply with a long thinking phase can take minutes, not seconds, so this connector waits up to 300 seconds instead of the 60 that the OpenAI connector uses.

## 4.4 Installing the SDK

Let's add Anthropic's official SDK to the project:

```bash
$ uv add anthropic
```

This command adds a line to the `dependencies` list in `pyproject.toml` and updates `uv.lock`. The version I'm using is 2.14.0, so your `pyproject.toml` should now include this:

_pyproject.toml_: The dependencies

```toml
dependencies = [
    "anthropic>=2.14.0",
    "openai>=3.60.0",
]
```

If `uv` installs a newer version for you, that's fine, the lower bound will just be different.

Just like the OpenAI SDK, this one has a habit of looking around your computer for configuration. If you don't give it a key, it reads `ANTHROPIC_API_KEY`, and then `ANTHROPIC_AUTH_TOKEN`, from the environment. If you don't give it a base URL, it reads `ANTHROPIC_BASE_URL`. You already know the fix: the connector passes everything explicitly, so that it behaves the same on every computer. You'll write a test that proves the environment has no effect.

There's a small surprise here, too. If you remember the curl experiment in your first notebook, Anthropic's API takes the key in an `x-api-key` header. When I watched the requests that version 2.14.0 of the SDK sends, it put the key in an `Authorization: Bearer` header instead. The connector doesn't care, and it shouldn't. How the key travels is the SDK's business, and it's one more thing that the rest of JudgeLab never needs to know.

## 4.5 A Second Implementation Changes the First

Here is the discovery I promised you. When an answer is cut off because it hit the length limit, OpenAI says `finish_reason == "length"`, and Claude says `stop_reason == "max_tokens"`. Right now, the only way for the rest of JudgeLab to detect truncation is to look at `finish_reason` and know which provider uses which word. That is exactly the kind of provider knowledge that the port was supposed to hide, but you couldn't see the leak when OpenAI was the only provider, because "length" seemed like the obvious word.

The fix is to add a provider-neutral field to `ModelResponse`. Open [src/judgelab/connectors/response.py](../../src/judgelab/connectors/response.py) and change the `finish_reason` line, adding a new line below it:

_src/judgelab/connectors/response.py_: The `truncated` field

```python
    finish_reason: str  # the provider's own value, e.g. "stop" or "end_turn"
    truncated: bool  # the answer was cut off by a length limit
```

The `finish_reason` field stays, because the provider's own value is still useful evidence when you are debugging, but the comment now makes clear that it's in the provider's words. The `truncated` field is in JudgeLab's words, and it means the same thing no matter who answered.

Notice that I didn't give `truncated` a default value. With `truncated: bool = False`, a connector that forgot about truncation would still work, and it would report every cut-off answer as complete. Without a default, forgetting is impossible, because Python refuses to build the response. Let's prove it right now. Run the tests:

```bash
$ uv run pytest -q
...
E       TypeError: ModelResponse.__init__() missing 1 required positional argument: 'truncated'
...
10 failed, 32 passed in 1.27s
```

I've cut most of the output, but this is what you should see: every test that builds a `ModelResponse` is broken. That's the compiler-style safety net you just bought, so let's fix the two connectors that build responses.

In [src/judgelab/connectors/openai_connector.py](../../src/judgelab/connectors/openai_connector.py), find the `return ModelResponse(...)` at the end of `generate()` and add one line after `finish_reason`:

_src/judgelab/connectors/openai_connector.py_: Setting `truncated` (inside `generate()`)

```python
            finish_reason=choice.finish_reason,
            truncated=choice.finish_reason == "length",
```

In [src/judgelab/connectors/fake.py](../../src/judgelab/connectors/fake.py), the fake connector never truncates anything, so it can say so directly:

_src/judgelab/connectors/fake.py_: Setting `truncated` (inside `generate()`)

```python
            finish_reason="refusal" if refused else "stop",
            truncated=False,
```

The OpenAI connector's tests also need to know about the new field. In [tests/connectors/test_openai_connector.py](../../tests/connectors/test_openai_connector.py), `test_returns_answer_and_metadata()` compares the whole response with an expected `ModelResponse`, so add the field there, after `finish_reason`:

_tests/connectors/test_openai_connector.py_: In `test_returns_answer_and_metadata()`

```python
        finish_reason="stop",
        truncated=False,
```

And the truncation test can now check the new field. It also verifies T014-AC4, so it gets a second marker. Replace the whole test with this version:

_tests/connectors/test_openai_connector.py_: The truncation test

```python
@pytest.mark.acceptance("T003-AC3", "T014-AC4")
def test_truncated_answer_keeps_its_finish_reason(connect):
    response = connect(server(body=completion("Par", finish="length"))).generate("hi")
    assert (response.text, response.finish_reason, response.truncated) == ("Par", "length", True)
```

Run `uv run pytest -q` again, and everything should pass. You haven't written a line of Claude code yet, but the abstraction is already better. This is the lesson of this chapter, and it's worth saying plainly: you can't design a good abstraction from one example. The second implementation shows you what the first one was hiding.

## 4.6 The Claude Connector

Now you are ready to write the new connector. It goes in a new file, and I'm going to show it to you in three parts. Let's start with the imports and the constructor.

_src/judgelab/connectors/anthropic_connector.py_: The connector, part 1 of 3

```python
"""A connector for Claude through the official `anthropic` SDK (Messages API).

References:
* Messages API request and response:
  https://platform.claude.com/docs/en/api/messages/create
* Errors, including 402 billing and the spend-cap 429:
  https://platform.claude.com/docs/en/api/errors
"""

import time

import anthropic
from anthropic import Anthropic
from anthropic.types import Message

from judgelab.connectors.base import ModelConnector
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

ANTHROPIC_DEFAULT_BASE_URL = "https://api.anthropic.com"

# HTTP 429 responses that mean "over a spend limit", not "slow down".
QUOTA_ERROR_CODES = {"enforced_spend_limit_reached"}


class AnthropicConnector(ModelConnector):
    """Sends one prompt to a Claude model through the Messages API."""

    provider = "anthropic"
    default_base_url = ANTHROPIC_DEFAULT_BASE_URL

    def __init__(
        self,
        *,
        model: str,
        api_key_env: str,
        base_url: str | None = None,
        timeout_s: float = 300.0,
        max_retries: int = 0,
        max_tokens: int = 16000,
        http_client=None,
    ) -> None:
        super().__init__(model=model, base_url=base_url)
        if max_tokens < 1:
            raise ValueError("max_tokens must be at least 1")
        self.max_tokens = max_tokens
        self._client = Anthropic(
            api_key=read_secret(api_key_env),
            base_url=self.base_url,
            timeout=timeout_s,
            max_retries=max_retries,
            http_client=http_client,
        )
```

If you put this side by side with `OpenAIConnector`, you'll see that it's almost the same. That's the port doing its job. The `provider` and `default_base_url` class variables fill in the two slots that `ModelConnector` declares. The call to `super().__init__()` validates the model name and picks the base URL, `read_secret()` looks up the key by the name of its environment variable (and raises an auth error naming the variable if it's missing), and every SDK setting is passed explicitly. Once again, `max_retries=0` means nothing is retried behind your back.

In section 3.2 I left the key, the timeout and the retries out of the base class, and promised to look at that decision again once a second real connector existed. Here it is, and the two constructors do share `api_key_env`, `timeout_s`, `max_retries` and `http_client`. But look at the defaults: 60 seconds for OpenAI, 300 for Claude, because the providers behave differently. And the fake connector still needs none of them. Moving them up would make the base class carry settings that some connectors don't use, and with defaults that would be wrong for one of the two real ones. So I'm keeping them in each connector. What *is* shared is the names, and in the next chapter you'll see that the registry depends on exactly those names, so the shape of the constructors will be checked there, where it matters.

There is only one new argument, `max_tokens`, for the reason you saw in section 4.3. It's stored on `self` because `generate()` needs to send it with every request. A value below 1 is a programming mistake, not a provider failure, so it raises a plain `ValueError` right away instead of waiting for the API to reject it.

The docstring at the top of the file links to the two pages of Anthropic's documentation that this code is based on. When the API changes, those are the pages you'll want to re-read, so it's worth keeping the links next to the code.

## 4.7 Reading Claude's Reply

Add the `generate()` method to the class, right after the constructor:

_src/judgelab/connectors/anthropic_connector.py_: The connector, part 2 of 3 (inside the class)

```python
    def generate(self, prompt: str) -> ModelResponse:
        messages = [{"role": "user", "content": prompt}]

        start = time.perf_counter()
        try:
            message = self._client.messages.create(
                model=self.model, max_tokens=self.max_tokens, messages=messages
            )
        except anthropic.APIError as e:
            raise translate_error(e) from e
        latency_ms = (time.perf_counter() - start) * 1000

        if not isinstance(message, Message):
            raise ConnectorResponseError(f"expected a message, got {type(message).__name__}")
        request_id = message._request_id

        refusal = None
        if message.stop_reason == "refusal":
            details = message.stop_details
            refusal = (details.explanation if details else None) or "the model declined to answer"
        text_parts = [block.text for block in message.content if block.type == "text"]
        text = None if refusal else ("".join(text_parts) or None)
        if text is None and refusal is None:
            raise ConnectorResponseError(
                f"response has no text and no refusal (stop_reason={message.stop_reason})",
                request_id=request_id,
            )

        usage = message.usage
        return ModelResponse(
            text=text,
            refusal=refusal,
            requested_model=self.model,
            served_model=message.model,
            finish_reason=message.stop_reason or "unknown",
            truncated=message.stop_reason == "max_tokens",
            prompt_tokens=usage.input_tokens if usage else None,
            completion_tokens=usage.output_tokens if usage else None,
            request_id=request_id,
            latency_ms=latency_ms,
        )
```

This is the same four-step pattern you learned in chapter 1: translate the request, send it, check the reply, translate the reply. The first two steps need little explanation. The request has the model, the `max_tokens` budget and one user message, and any SDK exception is translated into a JudgeLab error, with `from e` keeping the original attached for debugging.

The interesting part is the middle, where the reply is checked and read.

First, the `isinstance()` check confirms that the SDK really gave you a `Message`. This is the same paranoia you applied to OpenAI's chat completion, for the same reason: a misbehaving gateway can return something that isn't a real reply. The request id comes from the `request-id` header through `message._request_id`, which, as with OpenAI, is documented as public in the SDK's README despite its leading underscore.

Next comes the refusal. When Claude declines to answer, `stop_reason` is `"refusal"`, and `stop_details.explanation` may describe why. The code uses the explanation when there is one, and a generic message otherwise. Like in the OpenAI connector, a refusal is a normal `ModelResponse` with `refusal` set and `text` left as `None`, because refusing is an outcome to record, not a failure.

Then the text. Claude's `content` is a list of blocks, and on current models the list can start with one or more `thinking` blocks before the answer. The list comprehension keeps only the blocks whose `type` is `"text"` and joins them. Why join, instead of taking the first text block? Because nothing in the API promises that the answer comes as a single block, and if you took only the first one you could silently drop half of an answer. The `or None` at the end turns an empty string into `None`, so that a reply that was all thinking and no text is treated as "no text".

That leads to the last check, which is the Claude version of the "neither content nor refusal" check from chapter 1. If there is no text and no refusal, we don't know what the model did, and that's a `ConnectorResponseError`. The message includes the stop reason, which is a short, safe value that will help you figure out what happened.

Finally, the reply is translated into a `ModelResponse`. Claude calls the token counts `input_tokens` and `output_tokens`, and they are mapped to JudgeLab's `prompt_tokens` and `completion_tokens`. The provider's own stop reason goes into `finish_reason`, and `truncated` is set from `"max_tokens"`, which is the Claude word for what OpenAI calls `"length"`.

## 4.8 Translating Claude's Errors

The last part of the file goes below the class, at the module level:

_src/judgelab/connectors/anthropic_connector.py_: The connector, part 3 of 3 (below the class)

```python
def translate_error(e: anthropic.APIError) -> ConnectorError:
    """Map the SDK's exception family onto JudgeLab's."""
    if isinstance(e, anthropic.APIConnectionError):  # includes APITimeoutError
        kind = "timed out" if isinstance(e, anthropic.APITimeoutError) else "connection failed"
        return ConnectorUnavailableError(f"request {kind}")
    if isinstance(e, anthropic.APIStatusError):
        status, request_id = e.status_code, e.request_id
        error_type, error_code = _error_type_and_code(e.body)
        label = error_code or error_type
        detail = f"HTTP {status}" + (f" ({label})" if label else "")
        kwargs = {"status_code": status, "request_id": request_id}
        if status in (401, 403):
            return ConnectorAuthError(detail, **kwargs)
        if status == 402 or error_code in QUOTA_ERROR_CODES:
            return ConnectorQuotaError(detail, **kwargs)
        if status == 429:
            return ConnectorRateLimitError(detail, **kwargs)
        if status >= 500 or status in (408, 409):  # includes 529 overloaded
            return ConnectorUnavailableError(detail, **kwargs)
        return ConnectorRequestError(detail, **kwargs)
    return ConnectorResponseError(f"unexpected SDK error: {type(e).__name__}")


def _error_type_and_code(body: object) -> tuple[str | None, str | None]:
    """Read error.type and error.details.error_code from an error body, if present."""
    error = body.get("error") if isinstance(body, dict) else None
    if not isinstance(error, dict):
        return None, None
    details = error.get("details")
    code = details.get("error_code") if isinstance(details, dict) else None
    return error.get("type"), code
```

The `anthropic` SDK organizes its exceptions in the same kind of tree as the OpenAI SDK, with `APIConnectionError` for "the server never answered" and `APIStatusError` for "the server answered with an error code". That's not a coincidence, both SDKs are generated by the same tool, but you shouldn't count on it with other providers.

The triage is the same as in the OpenAI connector, so the rest of JudgeLab sees the same error for the same situation, whichever provider caused it. What changes is how Claude reports each situation. According to Anthropic's [error documentation](https://platform.claude.com/docs/en/api/errors):

- **402 `billing_error`** means there's a problem with billing or the account is out of credit. Every call will fail until a human acts, so it's a `ConnectorQuotaError`.
- **429** usually means "slow down", a `ConnectorRateLimitError`. But when the error body has `error.details.error_code` set to `enforced_spend_limit_reached`, you've hit a spend cap. Waiting won't help there, so that 429 is a quota error too. This is why the quota check comes *before* the 429 check.
- **529 `overloaded_error`** means Anthropic's servers are temporarily overloaded. It's caught by the `status >= 500` rule, which is why the comment mentions it, and it becomes a `ConnectorUnavailableError` that a later retry might fix.

To make these decisions, the function needs the error's type and code from the response body, and that's what the `_error_type_and_code()` helper does. Notice how defensive it is. It checks that the body is a dictionary, that `error` is a dictionary, and that `details` is a dictionary, before reading anything from them. The reason is that you can't trust an error body any more than a success body. A proxy in the middle can return an HTML page, an empty body, or JSON in some other shape, and a function that is supposed to *report* an error must never crash while doing it. When anything is missing, it returns `None`, and the message falls back to the plain status code.

As in chapter 1, the message includes the short `label` (the error code, or the error type when there's no code), but never the provider's free-text `message`, which could echo part of your key.

The connector is complete, and the rest of the project needs to be able to import it. Open [src/judgelab/connectors/\_\_init\_\_.py](../../src/judgelab/connectors/__init__.py) and add an import at the top of the import list:

_src/judgelab/connectors/\_\_init\_\_.py_: Exporting the new connector

```python
from judgelab.connectors.anthropic_connector import AnthropicConnector
```

Then add `"AnthropicConnector",` as the first entry of the `__all__` list, which is kept in alphabetical order.

Let's see the connector in action against a fake server. Create a scratch script, `sandbox/claude_demo.py`, with this code. It's a throwaway, so it doesn't need to be tidy, and it stays out of your commit:

_sandbox/claude_demo.py_: A quick demo, part 1

```python
import os, httpx2
from judgelab.connectors import *
os.environ["K"]="sk-ant-demo"
seen=[]
def h(r):
    seen.append(r)
    return httpx2.Response(200, json={"id":"m","type":"message","role":"assistant","model":"claude-served","content":[{"type":"thinking","thinking":"","signature":"s"},{"type":"text","text":"Paris"}],"stop_reason":"end_turn","stop_sequence":None,"usage":{"input_tokens":3,"output_tokens":1}}, headers={"request-id":"req_demo"})
c=AnthropicConnector(model="claude-x", api_key_env="K", base_url="http://stub.local", http_client=httpx2.Client(transport=httpx2.MockTransport(h)))
print(c)
r=c.generate("hi")
print(r)
print(seen[0].url, {k:v for k,v in seen[0].headers.items() if k in ("authorization","x-api-key","anthropic-version")})
```

The fake server answers with a thinking block followed by a text block, and records the request it received so you can look at it. Run it with `uv run python sandbox/claude_demo.py`, and you should see this:

```text
AnthropicConnector(model='claude-x', base_url='http://stub.local')
ModelResponse(text='Paris', refusal=None, requested_model='claude-x', served_model='claude-served', finish_reason='end_turn', truncated=False, prompt_tokens=3, completion_tokens=1, request_id='req_demo', latency_ms=5.332624999937252)
http://stub.local/v1/messages {'authorization': 'Bearer sk-ant-demo', 'anthropic-version': '2026-10-21'}
```

Your latency will be different. Notice that the thinking block was skipped, that the SDK added `/v1/messages` to the base URL, and that the key went out as a `Bearer` token, as I mentioned in section 4.4.

Now let's try the error triage. Add this code to the end of the same script:

_sandbox/claude_demo.py_: A quick demo, part 2

```python
def fake(status, code=None, etype="x"):
    err={"type":etype,"message":"m"}
    if code: err["details"]={"error_code":code}
    return httpx2.Client(transport=httpx2.MockTransport(lambda r: httpx2.Response(status, json={"type":"error","error":err}, headers={"request-id":"req_demo"})))
cases={"402":fake(402,etype="billing_error"),"429 cap":fake(429,"enforced_spend_limit_reached","rate_limit_error"),"429":fake(429,etype="rate_limit_error"),"529":fake(529,etype="overloaded_error"),"timeout":httpx2.Client(transport=httpx2.MockTransport(lambda r: (_ for _ in ()).throw(httpx2.ReadTimeout("t", request=r))))}
for name, client in cases.items():
    try:
        AnthropicConnector(model="m", api_key_env="K", base_url="http://stub.local", http_client=client).generate("hi")
    except ConnectorError as e:
        print(f"{name:8} → {type(e).__name__}: {e}")
```

The odd-looking `(_ for _ in ()).throw(...)` is a trick to raise an exception from inside a `lambda`, which can't contain a `raise` statement. Run the script again. After the same three lines as before, you should see this:

```text
402      → ConnectorQuotaError: HTTP 402 (billing_error)
429 cap  → ConnectorQuotaError: HTTP 429 (enforced_spend_limit_reached)
429      → ConnectorRateLimitError: HTTP 429 (rate_limit_error)
529      → ConnectorUnavailableError: HTTP 529 (overloaded_error)
timeout  → ConnectorUnavailableError: request timed out
```

Compare the two 429 lines. Same status code, different errors, and the code in parentheses tells you why.

If you have a Claude API key and want to see a real answer, put it in `ANTHROPIC_API_KEY` and call `AnthropicConnector(model="<a Claude model id>", api_key_env="ANTHROPIC_API_KEY").generate("What is the capital of France? One word.")`. Look at `served_model`, `finish_reason` and the token counts. A one-word question costs a tiny fraction of a cent, but the output tokens include any thinking the model did, so the completion count may be larger than you expect.

## 4.9 A Feature I Left Out on Purpose

Anthropic offers a server-side "fallback" option, where a request that one model refuses can be retried automatically on a different model. For a chat application that can be convenient. For JudgeLab it would be a disaster, so the connector doesn't enable it.

An evaluation has to measure the model you configured. If the target model refuses a question and a different model quietly answers it, the result is recorded against the wrong model, and the refusal, which may be exactly the behaviour a safety benchmark is looking for, disappears. The `served_model` field would reveal the switch if you went looking for it, but by then the benchmark is already contaminated. It's the same principle as `max_retries=0`: nothing happens behind your back. If a model refuses, the refusal is the result.

## 4.10 Testing the Claude Connector

Let's write the tests. They follow the same approach as the OpenAI tests, with a fake HTTP server built on `httpx2.MockTransport`, so the real SDK runs unchanged and only the network is fake. Here is the complete file:

_tests/connectors/test_anthropic_connector.py_: The Claude connector tests

```python
"""AnthropicConnector tests against a fake HTTP server (httpx2.MockTransport)."""

import json

import httpx2
import pytest

from judgelab.connectors import (
    AnthropicConnector,
    ConnectorAuthError,
    ConnectorQuotaError,
    ConnectorRateLimitError,
    ConnectorRequestError,
    ConnectorResponseError,
    ConnectorUnavailableError,
)

KEY_ENV = "JUDGELAB_TEST_ANTHROPIC_KEY"
SECRET = "sk-ant-test-SECRET-5678"


def message(*blocks, stop="end_turn", stop_details=None):
    body = {
        "id": "msg_1",
        "type": "message",
        "role": "assistant",
        "model": "claude-served-2026",
        "content": list(blocks),
        "stop_reason": stop,
        "stop_sequence": None,
        "usage": {"input_tokens": 20, "output_tokens": 5},
    }
    if stop_details:
        body["stop_details"] = stop_details
    return body


def text(value):
    return {"type": "text", "text": value}


THINKING = {"type": "thinking", "thinking": "", "signature": "sig"}


def server(status=200, *, body=None, raises=None, seen=None):
    def handler(request):
        if seen is not None:
            seen.append(request)
        if raises:
            raise raises(request)
        return httpx2.Response(status, json=body, headers={"request-id": "req_anth_1"})

    return httpx2.Client(transport=httpx2.MockTransport(handler))


def error_body(error_type, error_code=None):
    error = {"type": error_type, "message": f"bad key {SECRET[:9]}..."}
    if error_code:
        error["details"] = {"error_code": error_code}
    return {"type": "error", "error": error, "request_id": "req_anth_1"}


@pytest.fixture
def connect(monkeypatch):
    monkeypatch.setenv(KEY_ENV, SECRET)

    def make(client, **kwargs):
        return AnthropicConnector(
            model="claude-asked",
            api_key_env=KEY_ENV,
            base_url="http://stub.local",
            http_client=client,
            **kwargs,
        )

    return make


@pytest.mark.acceptance("T014-AC1")
def test_missing_key_names_the_variable(monkeypatch):
    monkeypatch.delenv("NOT_SET_ANYWHERE", raising=False)
    with pytest.raises(ConnectorAuthError, match="NOT_SET_ANYWHERE is not set"):
        AnthropicConnector(model="m", api_key_env="NOT_SET_ANYWHERE")


@pytest.mark.acceptance("T014-AC1")
def test_environment_defaults_have_no_effect(connect, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "http://somewhere-else.example")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-wrong-from-env")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "token-wrong-from-env")
    seen = []
    connect(server(body=message(text("Paris")), seen=seen)).generate("hi")
    assert str(seen[0].url) == "http://stub.local/v1/messages"
    assert SECRET in (
        seen[0].headers.get("authorization", "") + seen[0].headers.get("x-api-key", "")
    )
    assert "wrong-from-env" not in str(seen[0].headers)


@pytest.mark.acceptance("T014-AC1")
def test_default_base_url_is_anthropic(monkeypatch):
    monkeypatch.setenv(KEY_ENV, SECRET)
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "http://somewhere-else.example")
    assert (
        AnthropicConnector(model="m", api_key_env=KEY_ENV).base_url == "https://api.anthropic.com"
    )


@pytest.mark.acceptance("T014-AC2")
def test_returns_text_skipping_thinking_blocks(connect):
    response = connect(server(body=message(THINKING, text("Par"), text("is")))).generate("hi")
    assert response.text == "Paris"
    assert (response.requested_model, response.served_model) == (
        "claude-asked",
        "claude-served-2026",
    )
    assert (response.finish_reason, response.truncated) == ("end_turn", False)
    assert (response.prompt_tokens, response.completion_tokens) == (20, 5)
    assert response.request_id == "req_anth_1"


@pytest.mark.acceptance("T014-AC2")
def test_sends_model_max_tokens_and_one_user_message(connect):
    seen = []
    connect(server(body=message(text("ok")), seen=seen), max_tokens=512).generate("hello")
    assert json.loads(seen[0].content) == {
        "model": "claude-asked",
        "max_tokens": 512,
        "messages": [{"role": "user", "content": "hello"}],
    }


@pytest.mark.acceptance("T014-AC3")
def test_refusal_is_a_response(connect):
    details = {"type": "refusal", "category": "cyber", "explanation": "I can't help with that."}
    body = message(stop="refusal", stop_details=details)
    response = connect(server(body=body)).generate("hi")
    assert (response.text, response.refusal) == (None, "I can't help with that.")
    assert response.finish_reason == "refusal"


@pytest.mark.acceptance("T014-AC4")
def test_max_tokens_is_truncated(connect):
    response = connect(server(body=message(text("Par"), stop="max_tokens"))).generate("hi")
    assert (response.text, response.truncated) == ("Par", True)


@pytest.mark.acceptance("T014-AC5")
def test_no_text_and_no_refusal_raises(connect):
    with pytest.raises(ConnectorResponseError, match="no text and no refusal"):
        connect(server(body=message(THINKING, stop="end_turn"))).generate("hi")


@pytest.mark.acceptance("T014-AC6")
@pytest.mark.parametrize(
    "status, error_type, error_code, expected",
    [
        (401, "authentication_error", None, ConnectorAuthError),
        (403, "permission_error", None, ConnectorAuthError),
        (402, "billing_error", None, ConnectorQuotaError),
        (429, "rate_limit_error", "enforced_spend_limit_reached", ConnectorQuotaError),
        (429, "rate_limit_error", None, ConnectorRateLimitError),
        (500, "api_error", None, ConnectorUnavailableError),
        (529, "overloaded_error", None, ConnectorUnavailableError),
        (400, "invalid_request_error", None, ConnectorRequestError),
        (404, "not_found_error", None, ConnectorRequestError),
    ],
)
def test_http_errors_are_translated(connect, status, error_type, error_code, expected):
    with pytest.raises(expected) as caught:
        connect(server(status, body=error_body(error_type, error_code))).generate("hi")
    assert caught.value.status_code == status
    assert caught.value.request_id == "req_anth_1"
    assert SECRET[:9] not in str(caught.value)


@pytest.mark.acceptance("T014-AC6")
def test_timeout_is_unavailable(connect):
    client = server(raises=lambda request: httpx2.ReadTimeout("slow", request=request))
    with pytest.raises(ConnectorUnavailableError, match="timed out"):
        connect(client).generate("hi")
```

There are a few techniques in this file worth pointing out.

The small builder functions at the top, `message()`, `text()` and `error_body()`, let each test describe only what makes it special. A test that cares about thinking blocks writes `message(THINKING, text("Par"), text("is"))`, and everything else in the body gets a sensible default. When a test is short, it's easy to see what it's checking.

The `server()` function has a `seen` argument. When you pass a list, the fake server appends every request it receives to it, which lets a test look at what the connector *sent*, not only at what it returned. `test_sends_model_max_tokens_and_one_user_message()` uses this to check the exact JSON body, including `max_tokens`, and `test_environment_defaults_have_no_effect()` uses it to check the URL and the headers.

That environment test is the proof I promised in section 4.4. It fills `ANTHROPIC_BASE_URL`, `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` with wrong values, sends a request, and checks that the request went to the configured URL, carrying the configured key, and that nothing from the environment leaked into the headers. Notice that it accepts the key in either `authorization` or `x-api-key`. The test checks what JudgeLab promises, that the right key is sent, not how the current SDK version happens to send it. If a future SDK goes back to `x-api-key`, this test will still pass, as it should.

The `connect` fixture returns a function instead of a connector. This is the "factory as fixture" pattern, which lets each test create a connector against its own fake server, with extra arguments like `max_tokens=512` when it needs them. `monkeypatch.setenv()` sets the key variable for the duration of one test only, and pytest restores the environment afterwards.

The `error_body()` function puts the first nine characters of the secret into the error message, just like a real provider might. Every error test then asserts that those characters do *not* appear in the JudgeLab error. And the parametrized error test runs nine cases from a single function, with the two 429 rows side by side, which makes the spend-cap rule easy to see.

## 4.11 Joining the Contract

The OpenAI connector and the fake connector both pass the shared contract tests in `test_contract.py`. The Claude connector has to pass them too, which is what T014-AC7 is about. Adding a connector to the contract means writing a factory function that returns two connectors, one that answers with "Paris" and one that fails, and adding it to `FACTORIES`.

Open [tests/connectors/test_contract.py](../../tests/connectors/test_contract.py) and add `AnthropicConnector` to the imports:

_tests/connectors/test_contract.py_: The imports

```python
from judgelab.connectors import (
    AnthropicConnector,
    ConnectorError,
    ConnectorUnavailableError,
    FakeConnector,
```

Then replace the `FACTORIES = ...` line with the new factory function and a longer dictionary:

_tests/connectors/test_contract.py_: The Claude factory

```python
def anthropic_connectors(monkeypatch):
    monkeypatch.setenv("CONTRACT_ANTHROPIC_KEY", SECRET)

    def connector(status, body):
        transport = httpx2.MockTransport(lambda request: httpx2.Response(status, json=body))
        return AnthropicConnector(
            model="claude-test",
            api_key_env="CONTRACT_ANTHROPIC_KEY",
            base_url="http://stub.local",
            http_client=httpx2.Client(transport=transport),
        )

    answer = {
        "id": "m",
        "type": "message",
        "role": "assistant",
        "model": "claude-test-2026",
        "content": [{"type": "text", "text": "Paris"}],
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {"input_tokens": 1, "output_tokens": 1},
    }
    overloaded = {"type": "error", "error": {"type": "overloaded_error", "message": "busy"}}
    return connector(200, answer), connector(529, overloaded)


FACTORIES = {
    "fake": fake_connectors,
    "openai": openai_connectors,
    "anthropic": anthropic_connectors,
}
```

The failing connector uses a 529 overloaded error, which is the most Claude-specific failure there is. The contract only promises that it raises *some* `ConnectorError`, and that's all the test checks.

The four contract tests now verify T014-AC7 as well as T003-AC9, so change the marker on each of them, `test_is_a_model_connector()`, `test_answers_with_a_model_response()`, `test_failures_are_connector_errors()` and `test_repr_names_the_model_and_hides_secrets()`, to this:

_tests/connectors/test_contract.py_: The new marker (on all four tests)

```python
@pytest.mark.acceptance("T003-AC9", "T014-AC7")
```

Finally, `truncated` is now part of the port, so the contract should say so. In `test_answers_with_a_model_response()`, add this line right after `assert response.finish_reason`:

_tests/connectors/test_contract.py_: In `test_answers_with_a_model_response()`

```python
    assert response.truncated is False
```

I used `is False` on purpose, instead of `not response.truncated`. A connector that set `truncated` to `None` or `0` would pass a `not` check, and `is False` insists on a real boolean. Every connector, present and future, now has to report truncation in JudgeLab's words.

## 4.12 Running the Tests

Let's run the whole suite:

```bash
$ uv run pytest
```

At the end of the output you should see the acceptance criteria table:

```text
============================= acceptance criteria ==============================
PASS        T003-AC1   A missing or empty API-key variable raises an auth error that names th
PASS        T003-AC2   The client is configured only from its arguments; `OPENAI_API_KEY` and
PASS        T003-AC3   A successful reply returns the answer, requested and served model, fin
PASS        T003-AC4   A refusal is returned as a response, not raised as an error.
PASS        T003-AC5   A reply that cannot be trusted (not a chat completion, no choices, no 
PASS        T003-AC6   SDK failures map to JudgeLab errors: 401/403 auth, billing codes and 4
PASS        T003-AC7   No request is retried unless retries are configured.
PASS        T003-AC8   The API key never appears in the connector's repr or in any error mess
PASS        T003-AC9   Every connector implements the `ModelConnector` port and passes the sh
PASS        T003-AC10  A `FakeConnector` answers from a script (answers, refusals, errors) an
PASS        T014-AC1   The client is configured only from its arguments; a missing key variab
PASS        T014-AC2   A successful reply returns the text blocks joined (thinking blocks ski
PASS        T014-AC3   A `refusal` stop reason is returned as a refusal response, not an erro
PASS        T014-AC4   Truncation is reported the same way for every provider: `truncated` is
PASS        T014-AC5   A reply with no text and no refusal raises a response error.
PASS        T014-AC6   Failures map like the OpenAI connector's, including 402 billing and th
PASS        T014-AC7   The Claude connector passes the shared connector contract tests.
17 PASS
64 passed in 2.25s
```

All seven T014 criteria pass, and so do all the T003 ones, which tells you that the `truncated` change didn't break the OpenAI connector. Your timing will be different.

## 4.13 Troubleshooting

- **`ModuleNotFoundError: No module named 'anthropic'`.** The `uv add anthropic` step didn't run, or your editor is using a different Python. Run `uv sync`, and make sure you run the tests with `uv run pytest`.
- **`TypeError: ModelResponse.__init__() missing 1 required positional argument: 'truncated'`.** One of the places that builds a `ModelResponse` doesn't set the new field yet. The traceback tells you which file. There are three: the OpenAI connector, the fake connector and the Claude connector.
- **`test_environment_defaults_have_no_effect` fails with the wrong URL.** You probably wrote `base_url=base_url` instead of `base_url=self.base_url` when creating the client. With `None`, the SDK falls back to `ANTHROPIC_BASE_URL`. Passing `self.base_url`, which the base class has already resolved to the default, closes that door.
- **The 429 spend-cap test gets a `ConnectorRateLimitError`.** The quota check must come *before* the `status == 429` check in `translate_error()`. The first matching `if` wins.
- **`docids.py check` reports `T014: not listed in docs/releases/v0.1/README.md`.** Add the row from section 4.2 to the release plan table.

## 4.14 Exercises

1. Write a fake reply whose `content` is `[text("Hello, "), THINKING, text("world")]`. What does `generate()` return, and why is joining the text blocks a better choice than taking the first one?
2. Create an `AnthropicConnector` with `max_tokens=0`. What happens, and why is it better to fail here than to let the API reject the request?
3. Make the fake server return a 429 whose body is the plain text `Too Many Requests` (use `httpx2.Response(429, text=...)`). Which JudgeLab error do you get, and which line of `_error_type_and_code()` saves you from a crash?
4. Send a refusal with `stop_reason` set to `"refusal"` but no `stop_details` at all. What does `refusal` contain?
5. Without looking at the code, list the places where the Claude connector differs from the OpenAI connector. Then explain why `truncated` belongs in `ModelResponse` but `max_tokens` belongs only in the Claude connector.

## 4.15 Committing Your Work

Before committing, update the task file to reflect what you've done. In `docs/releases/v0.1/tasks/T014.md`, tick every acceptance criterion that passed (change `- [ ]` to `- [x]`), set **Status** to `Done`, **Branch** to `` `feat/p1-claude-connector-T014` ``, and **AI-Assist** to `L4`. If you learned something worth remembering, such as the `truncated` discovery, write it under "Notes & lessons learned". Run `docids.py check` once more after editing.

Now commit everything as one logical change. Review what you are about to commit with `git status` and `git diff` first, and make sure no `.env` file sneaks in:

```bash
$ git add docs pyproject.toml uv.lock src tests
$ git commit
```

Here is the commit message I would write. The subject follows Conventional Commits, the body explains *why*, and the `AI-Assist` trailer records how the work was done:

```text
feat(connector): add Claude connector behind the ModelConnector port

Claude is the second, genuinely different provider: max_tokens is
required, content is a list of blocks that can include thinking,
truncation is stop_reason "max_tokens", and errors include 402
billing, the spend-cap 429 and 529 overloaded.

Adding it exposed an OpenAI detail in the port: truncation was only
visible as finish_reason "length". ModelResponse now has a
provider-neutral truncated flag, set by every connector and checked
by the contract tests.

AI-Assist: L4
```

Then push the branch and open a pull request. The `vbench-pr` skill walks through the whole checklist from `CONTRIBUTING.md` for you: it reads your commits and diff, self-reviews them, runs the tests, and drafts the title and body from the PR template. In Claude Code, just ask it to "open a PR for this branch". The PR title should match the commit subject, and the "AI assistance" section should say `Highest level: L4`.

## 4.16 Wrapping Up

Congratulations, JudgeLab now speaks to two very different model providers! The Claude connector handles a required `max_tokens`, answers that arrive as blocks with thinking mixed in, refusals with explanations, and Claude's own error codes, and from the outside it looks exactly like the OpenAI connector. You also made the port itself more honest: `truncated` means the same thing for every provider, and the contract tests enforce it.

There is one thing that is still awkward. To create a connector, you have to know its class and call its constructor with the right arguments. In the next codealong you are going to separate the *description* of a connection (which provider, which model, which URL, which environment variable holds the key) from the connector that does the work, and that will let you switch the target or the judge model by changing configuration alone.
