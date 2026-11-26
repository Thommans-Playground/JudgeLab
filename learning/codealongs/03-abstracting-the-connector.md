# Codealong 3: Abstracting the Connector

You now have one connector that works, lives in a proper package and is covered by tests. In this codealong you are going to look at it with fresh eyes, separate the parts that are about OpenAI from the parts that would be true of any connector, and turn the general parts into an abstract base class called `ModelConnector`. Then you are going to build a second connector on top of it, `FakeConnector`, which answers from a script with no network, no key and no cost. Finally, you are going to write a set of *contract tests* that every connector, present and future, must pass.

By the end, JudgeLab will have a single, well-defined idea of what "a connector" is. That is what will let the Claude connector of the next chapter be built in the image of the first one, and what will let the rest of JudgeLab be tested without ever calling a real model.

> **AI-Assist level:** this is a guided codealong, so record this work as **AI-Assist L4**.

## 3.1 Before You Start

This chapter starts where chapter 2 ended, with the connector package merged into `main`. The work is mostly a restructuring of existing code, so the branch is a `refactor/` one:

```bash
$ git switch main && git pull --ff-only && git switch -c refactor/p1-connector-port-T003
```

Run the tests once before you change anything, and make sure you get the eight PASS lines and `29 passed` from the end of chapter 2. A refactor starts from green tests and must end with green tests, so you need to know they are green now.

## 3.2 Build Before Abstracting

In chapter 1, I said we would build a concrete connector first and discover the abstraction from working code instead of guessing it. Now is the time to do that.

There is a reason for this order. If you design an abstract connector before you have built any real one, you have to guess what every connector will need, and guesses tend to go in one of two directions. Either the abstraction is too small and the first real connector has to work around it, or it is too big and every connector has to carry things it doesn't need. With a working connector in front of you, you can go through it line by line and ask, for each piece: "would *any* connector need this?"

Let's do exactly that with `OpenAIConnector`:

| Part | Who needs it |
|---|---|
| `model`, the name of the model to call | Every connector |
| `base_url`, with a provider default | Every connector that has a URL (a fake one doesn't) |
| `generate(prompt) -> ModelResponse` | Every connector: this *is* the promise |
| A `repr()` that shows the model and URL but never a secret | Every connector |
| `api_key_env` and `read_secret()` | Connectors that call a remote service |
| `timeout_s`, `max_retries`, `http_client` | Connectors that call a remote service |
| The messages format, the `ChatCompletion` checks, `translate_error()` | OpenAI only |

The first four rows are the general part, and they are all that is going to go into the abstract class. The last row obviously stays in the OpenAI connector.

The middle rows are the interesting ones. The key, the timeout and the retries look general, and the Claude connector of the next chapter will need them too. But the fake connector you are about to write needs none of them: it has no key to read and no network to time out. If the base class held them, the fake would have to accept a key it never uses. So I'm going to leave them out, for now. The rule I follow is to wait until a pattern has actually repeated before abstracting it. Two connectors with similar constructors is a hint; it is not yet a design. If it is still a pattern after the Claude connector exists, it can be moved up then, with real code on both sides to guide the move.

## 3.3 The New Acceptance Criteria

As always, the requirements come first. Open [docs/releases/v0.1/tasks/T003.md](../../docs/releases/v0.1/tasks/T003.md) and add two criteria at the end of the acceptance criteria list, right after AC8:

_docs/releases/v0.1/tasks/T003.md_: Two new acceptance criteria

```markdown
- [ ] **T003-AC9**: Every connector implements the `ModelConnector` port and passes the shared contract tests.
- [ ] **T003-AC10**: A `FakeConnector` answers from a script (answers, refusals, errors) and records the prompts it receives, with no network or key.
```

(If you ticked AC1 to AC8 at the end of chapter 2, leave them ticked. The new ones start unticked.)

AC9 uses the word *port*. This comes from the "ports and adapters" style of architecture: the core of an application defines the *port*, the shape of the thing it needs ("something I can give a prompt to and get a `ModelResponse` back"), and each connector is an *adapter* that plugs a particular provider into that port. The core of JudgeLab will only ever talk to the port, never to OpenAI or Anthropic directly. This is the dependency inversion idea mentioned for T003 and T004 in the learning ledger of the [v0.1 release plan](../../docs/releases/v0.1/README.md).

## 3.4 The Port

Here is the abstract connector. Create a new module for it:

_src/judgelab/connectors/base.py_: The connector port

```python
"""The connector port: what every model connector promises the rest of JudgeLab."""

from abc import ABC, abstractmethod
from typing import ClassVar

from judgelab.connectors.response import ModelResponse


class ModelConnector(ABC):
    """Sends one prompt to a model and returns a ModelResponse.

    Contract for every subclass:
    * `generate()` returns a ModelResponse whose `text` or `refusal` is set, or
      raises a ConnectorError subclass. No other exception escapes.
    * Configuration comes only from constructor arguments.
    * Secrets never appear in `repr()`, responses or error messages.
    """

    provider: ClassVar[str]
    default_base_url: ClassVar[str | None] = None

    def __init__(self, *, model: str, base_url: str | None = None) -> None:
        if not model.strip():
            raise ValueError("model must not be empty")
        self.model = model
        self.base_url = base_url or self.default_base_url

    @abstractmethod
    def generate(self, prompt: str) -> ModelResponse:
        """Send `prompt` as one user message."""

    def __repr__(self) -> str:
        return f"{type(self).__name__}(model={self.model!r}, base_url={self.base_url!r})"
```

This is a short file, but almost every line in it is a decision, so let's go through them.

**The contract in the docstring.** Read the three bullet points and you will recognise them: they are the acceptance criteria of chapter 2 (a response or a JudgeLab error, configuration from arguments only, no secrets anywhere), rephrased so that they apply to every connector instead of just the OpenAI one. Python can't enforce most of them, which is why section 3.10 is going to enforce them with tests.

**The class variables.** `provider` and `default_base_url` are annotated with `ClassVar`, which tells readers and type checkers that they belong to the class itself, not to each instance. Every subclass sets them in its class body. `provider` is a short name for the kind of connector, such as `"openai_compatible"`. You won't use it in this chapter, but in chapter 5 it is what lets a connection profile name the connector it wants, and in chapter 9 it ends up in the evaluation report. Notice that `provider` has an annotation but no value: there is no sensible default, so each subclass must choose one. `default_base_url`, on the other hand, defaults to `None`, which is the right value for a connector that has no URL.

**The constructor.** It holds the two things every connector has, and nothing else. It also adds a check that the notebook never had: an empty (or blank) model name is rejected straight away. Without this check, `OpenAIConnector(model="")` would construct happily and fail later, at the first request, with an HTTP error from the provider that doesn't point at the real cause. Notice that this raises `ValueError`, not a `ConnectorError`. Passing an empty model is a mistake in the calling code, not a failure to talk to a model, and Python's standard exception for "this argument has a bad value" is `ValueError`.

The line `self.base_url = base_url or self.default_base_url` is the defaulting logic that used to be in the OpenAI connector, made general. It reads `self.default_base_url`, which Python looks up on the instance's class, so each subclass gets its own default without writing any code.

**The abstract method.** The `@abstractmethod` decorator marks `generate()` as a method that every subclass *must* implement. The base class has no implementation to give, so its body is only a docstring.

**The `__repr__()` method.** This is the one from the OpenAI connector, with one change: instead of the hard-coded name `OpenAIConnector`, it uses `type(self).__name__`, the name of whatever class the instance really is. Every connector now gets a `repr()` that shows its model and URL and, because it only ever reads those two attributes, can never show a secret.

## 3.5 Why an Abstract Base Class?

Python gives you two common ways to describe "a thing with a `generate()` method". One is an abstract base class (ABC), which is what you just wrote. The other is a `typing.Protocol`, which describes the methods a class must have without the class having to inherit from anything. The v0.1 release plan even mentions Protocols in its learning ledger, so it's worth explaining why I went with an ABC here.

The main reason is *when* a mistake is caught. With an ABC, Python itself refuses to create an instance of a class that is missing an abstract method. You can see it in a Python shell (`uv run python`) once you've written `base.py`:

```python
>>> from judgelab.connectors.base import ModelConnector
>>> ModelConnector(model='m')
TypeError: Can't instantiate abstract class ModelConnector without an implementation for abstract method 'generate'
>>> class Half(ModelConnector):
...     provider = 'half'
...
>>> Half(model='m')
TypeError: Can't instantiate abstract class Half without an implementation for abstract method 'generate'
```

A connector that forgot to implement `generate()` fails the moment you try to create it, with an error message that says exactly what is missing. With a Protocol, nothing at all happens at run time: the class is created, and the mistake is only reported if you run a static type checker over the code, or when something finally calls the missing method.

The second reason is that the base class has code to share. The constructor's model check, the `base_url` defaulting and the safe `__repr__()` are written once in `ModelConnector` and inherited by every connector. A Protocol only describes a shape; it can't hold shared code.

You would choose a Protocol when you want to accept classes you don't control, which can't be made to inherit from your base class. That isn't the case here: every connector is JudgeLab's own code. It is also how the reference system we study does it: Project Moonshot's connectors all derive from a `Connector` base class.

This choice is exactly the kind of decision that deserves an Architecture Decision Record, a short document in `docs/decisions` that says what was decided, which alternatives were considered and why. Writing it is one of the exercises at the end of this chapter.

## 3.6 Plugging In the OpenAI Connector

Now let's make `OpenAIConnector` a subclass of the port. There are four small changes to make in `src/judgelab/connectors/openai_connector.py`.

First, import the base class. Add this line to the JudgeLab imports, just above the `read_secret` import:

_src/judgelab/connectors/openai_connector.py_: New import

```python
from judgelab.connectors.base import ModelConnector
```

Second, change the `class` line so that the connector inherits from `ModelConnector`, and add the two class variables right below the docstring. Third, in the constructor, replace the two lines that set `self.model` and `self.base_url` with a call to the base class constructor. When you are done, the top of the class should look like this:

_src/judgelab/connectors/openai_connector.py_: The connector as a subclass

```python
class OpenAIConnector(ModelConnector):
    """Sends one prompt to an OpenAI-compatible Chat Completions endpoint."""

    provider = "openai_compatible"
    default_base_url = OPENAI_DEFAULT_BASE_URL

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
        super().__init__(model=model, base_url=base_url)
        self._client = OpenAI(
            api_key=read_secret(api_key_env),
            base_url=self.base_url,
            timeout=timeout_s,
            max_retries=max_retries,
            http_client=http_client,
        )
```

Fourth, delete the `__repr__()` method entirely. The connector now inherits it from `ModelConnector`.

The `generate()` method and `translate_error()` don't change at all.

The `provider` is `"openai_compatible"` rather than `"openai"`, because this connector works with anything that speaks OpenAI's Chat Completions format, including gateways and local model servers. The `super().__init__()` call runs the base class constructor, which checks the model and sets `self.model` and `self.base_url`. It has to come before the client is created, because the client is given `self.base_url`, which doesn't exist until the base constructor has set it.

Removing `__repr__()` deserves a second look, because one of the chapter 2 tests checks its exact output: `OpenAIConnector(model='asked-model', base_url='http://stub.local/v1')`. The inherited version builds the name from `type(self).__name__`, which for this class is `OpenAIConnector`, so the output is identical, and that test proves it.

Finally, export the port from the package. In `src/judgelab/connectors/__init__.py`, add this import as the first import line:

_src/judgelab/connectors/\_\_init\_\_.py_: Exporting the port

```python
from judgelab.connectors.base import ModelConnector
```

and add `"ModelConnector",` to the `__all__` list, just above `"ModelResponse",`, to keep the list in alphabetical order.

That's the whole refactor. Run the tests:

```bash
$ uv run pytest -q
.............................                                            [100%]
============================= acceptance criteria ==============================
PASS        T003-AC1   A missing or empty API-key variable raises an auth error that names th
PASS        T003-AC2   The client is configured only from its arguments; `OPENAI_API_KEY` and
PASS        T003-AC3   A successful reply returns the answer, requested and served model, fin
PASS        T003-AC4   A refusal is returned as a response, not raised as an error.
PASS        T003-AC5   A reply that cannot be trusted (not a chat completion, no choices, no 
PASS        T003-AC6   SDK failures map to JudgeLab errors: 401/403 auth, billing codes and 4
PASS        T003-AC7   No request is retried unless retries are configured.
PASS        T003-AC8   The API key never appears in the connector's repr or in any error mess
not tested  T003-AC9   Every connector implements the `ModelConnector` port and passes the sh
not tested  T003-AC10  A `FakeConnector` answers from a script (answers, refusals, errors) an
8 PASS · 2 not tested
29 passed in 0.20s
```

All 29 tests still pass without a single change to them. That is what makes this a refactor: the structure changed, the behaviour didn't, and the tests are the evidence. The two new criteria show up as "not tested", which is your to-do list for the rest of the chapter.

This is a good moment to make a commit, while the refactor is complete and the tests are green, and before you start adding new behaviour. Stage only the three files you changed (leave `T003.md` for the next commit, since its new criteria are about the work still to come):

```bash
$ git add src/judgelab/connectors/base.py src/judgelab/connectors/openai_connector.py src/judgelab/connectors/__init__.py
$ git commit
```

```text
refactor(connector): extract the ModelConnector port

OpenAIConnector was the only connector, so it held everything. The
parts any connector needs (model check, base_url default, generate(),
a repr that never shows secrets) move to an abstract base class.
Key, timeout and retries stay in OpenAIConnector: a fake connector
has none of them, so they are not general yet.

Chose an ABC over typing.Protocol: a subclass missing generate()
fails at construction, and the base class holds the shared code.

AI-Assist: L4
```

[CONTRIBUTING.md](../../CONTRIBUTING.md) asks for exactly this: keep refactors separate from behaviour changes, and commit the refactor first, with the tests still green.

## 3.7 A Connector That Never Leaves the Room

The core of JudgeLab, the parts you will write in the coming chapters, is going to send prompts to a target model, send answers to a judge model, and score the results. All of that code needs tests, and those tests must not call a real model. A real model costs money, needs a key, needs a network, and, worst of all for a test, doesn't give the same answer twice. Requirement REQ-012 in the release plan says it directly: JudgeLab must support deterministic tests with fake connectors.

So let's write a connector whose answers are completely under your control.

_src/judgelab/connectors/fake.py_: A scripted connector for tests

```python
"""A scripted connector for tests: no network, no key, fully deterministic."""

from collections.abc import Mapping
from dataclasses import dataclass

from judgelab.connectors.base import ModelConnector
from judgelab.connectors.errors import ConnectorError, ConnectorRequestError
from judgelab.connectors.response import ModelResponse


@dataclass(frozen=True)
class Refusal:
    """A scripted refusal: the fake model declines to answer."""

    message: str


Reply = str | Refusal | ConnectorError


class FakeConnector(ModelConnector):
    """Answers prompts from a script and records every prompt it receives.

    Each scripted reply is either the answer text, a Refusal, or a
    ConnectorError to raise. Prompts that are not in the script get
    `default`; without a default they raise ConnectorRequestError, so a test
    that sends an unexpected prompt fails loudly.
    """

    provider = "fake"

    def __init__(
        self,
        *,
        model: str = "fake-model",
        replies: Mapping[str, Reply] | None = None,
        default: Reply | None = None,
    ) -> None:
        super().__init__(model=model)
        self.replies = dict(replies or {})
        self.default = default
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> ModelResponse:
        self.prompts.append(prompt)
        reply = self.replies.get(prompt, self.default)
        if reply is None:
            raise ConnectorRequestError(f"fake connector has no reply for prompt {prompt!r}")
        if isinstance(reply, ConnectorError):
            raise reply
        refused = isinstance(reply, Refusal)
        return ModelResponse(
            text=None if refused else reply,
            refusal=reply.message if refused else None,
            requested_model=self.model,
            served_model=self.model,
            finish_reason="refusal" if refused else "stop",
            prompt_tokens=len(prompt.split()),
            completion_tokens=0 if refused else len(reply.split()),
            request_id=f"fake-{len(self.prompts)}",
            latency_ms=0.0,
        )
```

Think of the fake connector as an actor with a script. You hand it a dictionary of lines, "if you are asked *this*, say *that*", and it performs exactly that, every time.

**Three kinds of reply.** A real model can do three things with a prompt: answer it, refuse it, or fail. The script needs to be able to express all three, so a scripted reply can be:

- a string, which is the answer text,
- a `Refusal`, which carries the refusal message,
- a `ConnectorError` instance, which the fake raises, just as a real connector would on a failure.

Why a separate `Refusal` class instead of just a string? Because a string already means "the answer". The fake needs to tell the two apart with `isinstance()`, and that requires them to be different types. `Refusal` is a tiny frozen dataclass with a single field, which is all it needs to be.

**The `Reply` type alias.** The line `Reply = str | Refusal | ConnectorError` gives a name to "any of these three types". It doesn't create a new class; it's just a shorter way to write the union in the type hints that follow, so `Mapping[str, Reply]` reads as "a mapping from prompts to replies" instead of a long, noisy type expression.

**The constructor.** All three arguments are optional: the model name defaults to `"fake-model"`, and there may be no script at all. `replies` is copied into a new dictionary with `dict(replies or {})`. The copy means that if a test later modifies the dictionary it passed in, the fake's script doesn't change behind its back, and `or {}` turns `None` into an empty script. Notice that `super().__init__()` is called with the model only: the fake has no URL, so its `base_url` will be the inherited default, `None`. And notice what is *not* here: no key, no timeout, no retries. This is the connector that proved, in section 3.2, that those don't belong in the base class.

**Recording prompts.** The first thing `generate()` does is append the prompt to `self.prompts`, before it even looks at the script. That way a test can check afterwards exactly which prompts the code under test sent and in what order, including the ones that failed.

**Failing loudly.** If a prompt isn't in the script, the fake uses `default`. If there is no default either, it raises a `ConnectorRequestError` that quotes the prompt. This is deliberate. A fake that quietly returned some placeholder for unexpected prompts would let a broken test pass; one that raises makes the test fail with a message saying exactly which prompt nobody planned for. If a test really doesn't care about the prompts, it can say so explicitly by passing a `default`.

**Building the response.** The rest of the method builds a `ModelResponse` that respects the contract: either `text` or `refusal` is set, never both and never neither. The finish reason is `"refusal"` for a refusal and `"stop"` otherwise. The token counts are simply word counts, which is good enough for a fake, and the request ids are numbered `fake-1`, `fake-2` and so on, so each call in a test can be told apart. The latency is always zero, because nothing was waited for.

Here is the fake in action in a Python shell. It works even with no `.env` file and no network:

```python
>>> from judgelab.connectors.fake import FakeConnector, Refusal
>>> fake = FakeConnector(replies={'Capital of France?': 'Paris'}, default=Refusal('No.'))
>>> fake
FakeConnector(model='fake-model', base_url=None)
>>> fake.generate('Capital of France?')
ModelResponse(text='Paris', refusal=None, requested_model='fake-model', served_model='fake-model', finish_reason='stop', prompt_tokens=3, completion_tokens=1, request_id='fake-1', latency_ms=0.0)
>>> fake.generate('How do I pick a lock?')
ModelResponse(text=None, refusal='No.', requested_model='fake-model', served_model='fake-model', finish_reason='refusal', prompt_tokens=6, completion_tokens=0, request_id='fake-2', latency_ms=0.0)
>>> fake.prompts
['Capital of France?', 'How do I pick a lock?']
>>> FakeConnector().generate('hi')
ConnectorRequestError: fake connector has no reply for prompt 'hi'
```

Notice the `repr()`: you didn't write one for `FakeConnector`, but it inherited the safe one from the port, with its own class name and `base_url=None`.

## 3.8 Exporting the New Names

The fake and its `Refusal` class need to be on the package's front door too. Here is the complete `__init__.py` after this chapter. Compared to what you have after section 3.6, there is one new import line for `fake`, and two new names in `__all__`:

_src/judgelab/connectors/\_\_init\_\_.py_: Public names of the package

```python
"""Connectors: adapters that let JudgeLab call foundation models."""

from judgelab.connectors.base import ModelConnector
from judgelab.connectors.errors import (
    ConnectorAuthError,
    ConnectorError,
    ConnectorQuotaError,
    ConnectorRateLimitError,
    ConnectorRequestError,
    ConnectorResponseError,
    ConnectorUnavailableError,
)
from judgelab.connectors.fake import FakeConnector, Refusal
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
    "FakeConnector",
    "ModelConnector",
    "ModelResponse",
    "OpenAIConnector",
    "Refusal",
]
```

You may wonder why a test helper lives in the main package instead of under `tests/`. It's because the fake is not just for the connector tests. In the coming chapters, the tests for the runner, the judge, the report and the command line all use it in place of a real model, and anyone who builds on JudgeLab can use it to test their own code. Keeping it in the package makes it a supported part of JudgeLab, with the same port and the same contract as the real connectors.

## 3.9 Testing the Fake

Now let's verify AC10. Create a new test file:

_tests/connectors/test_fake_connector.py_: Tests for the fake connector

```python
import pytest

from judgelab.connectors import (
    ConnectorRateLimitError,
    ConnectorRequestError,
    FakeConnector,
    Refusal,
)


@pytest.mark.acceptance("T003-AC10")
def test_answers_from_the_script_and_records_prompts():
    fake = FakeConnector(replies={"2+2?": "4", "Capital of France?": "Paris"})
    assert fake.generate("Capital of France?").text == "Paris"
    assert fake.generate("2+2?").text == "4"
    assert fake.prompts == ["Capital of France?", "2+2?"]


@pytest.mark.acceptance("T003-AC10")
def test_scripted_refusal_is_a_response():
    response = FakeConnector(default=Refusal("I can't help with that.")).generate("anything")
    assert (response.text, response.refusal) == (None, "I can't help with that.")


@pytest.mark.acceptance("T003-AC10")
def test_scripted_error_is_raised():
    fake = FakeConnector(replies={"hi": ConnectorRateLimitError("HTTP 429", status_code=429)})
    with pytest.raises(ConnectorRateLimitError):
        fake.generate("hi")


@pytest.mark.acceptance("T003-AC10")
def test_unscripted_prompt_fails_loudly():
    with pytest.raises(ConnectorRequestError, match="no reply for prompt 'surprise'"):
        FakeConnector(replies={"hi": "hello"}).generate("surprise")
```

After the HTTP plumbing of chapter 2, these tests are refreshingly simple, and that is the whole point of a fake: no fixtures, no fake servers, no environment variables. Each test checks one sentence of the AC10 criterion. The first one asks the questions in a different order from the script, to show that `prompts` records the order in which they were *asked*. The last one checks not only that an unscripted prompt raises, but that the message names the prompt, since that message is what you will read when one of your future tests sends something unexpected.

## 3.10 The Contract Tests

The tests in chapter 2 check that the OpenAI connector behaves correctly, and the tests you just wrote check the fake. But neither checks the thing that matters most to the rest of JudgeLab: that every connector keeps the *same* promises, so that code written against `ModelConnector` works with any of them. That is what AC9 asks for, and it is the job of contract tests.

The idea is to write each test once, in terms of the port only, and run it against every connector. Create the file:

_tests/connectors/test_contract.py_: The connector contract

```python
"""The connector contract: every ModelConnector must pass these tests.

To add a connector to the contract, write a factory that returns two
connectors, one that answers PROMPT with "Paris" and one whose call fails,
and add it to FACTORIES.
"""

import httpx2
import pytest

from judgelab.connectors import (
    ConnectorError,
    ConnectorUnavailableError,
    FakeConnector,
    ModelConnector,
    ModelResponse,
    OpenAIConnector,
)

PROMPT = "What is the capital of France? One word."
SECRET = "sk-contract-SECRET-0000"


def fake_connectors(monkeypatch):
    answering = FakeConnector(replies={PROMPT: "Paris"})
    failing = FakeConnector(default=ConnectorUnavailableError("fake outage"))
    return answering, failing


def openai_connectors(monkeypatch):
    monkeypatch.setenv("CONTRACT_OPENAI_KEY", SECRET)

    def connector(status, body):
        transport = httpx2.MockTransport(lambda request: httpx2.Response(status, json=body))
        return OpenAIConnector(
            model="gpt-test",
            api_key_env="CONTRACT_OPENAI_KEY",
            base_url="http://stub.local/v1",
            http_client=httpx2.Client(transport=transport),
        )

    answer = {
        "id": "c",
        "object": "chat.completion",
        "created": 0,
        "model": "gpt-test-2026",
        "choices": [
            {
                "index": 0,
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": "Paris"},
            }
        ],
    }
    return connector(200, answer), connector(500, {"error": {"message": "down"}})


FACTORIES = {"fake": fake_connectors, "openai": openai_connectors}


@pytest.fixture(params=FACTORIES.values(), ids=FACTORIES.keys())
def connectors(request, monkeypatch):
    return request.param(monkeypatch)


@pytest.mark.acceptance("T003-AC9")
def test_is_a_model_connector(connectors):
    for connector in connectors:
        assert isinstance(connector, ModelConnector)


@pytest.mark.acceptance("T003-AC9")
def test_answers_with_a_model_response(connectors):
    answering, _ = connectors
    response = answering.generate(PROMPT)
    assert isinstance(response, ModelResponse)
    assert response.text == "Paris"
    assert response.requested_model == answering.model
    assert response.served_model
    assert response.finish_reason
    assert response.latency_ms >= 0


@pytest.mark.acceptance("T003-AC9")
def test_failures_are_connector_errors(connectors):
    _, failing = connectors
    with pytest.raises(ConnectorError):
        failing.generate(PROMPT)


@pytest.mark.acceptance("T003-AC9")
def test_repr_names_the_model_and_hides_secrets(connectors):
    for connector in connectors:
        assert connector.model in repr(connector)
        assert SECRET not in repr(connector)


@pytest.mark.acceptance("T003-AC9")
def test_the_port_cannot_be_used_directly():
    with pytest.raises(TypeError):
        ModelConnector(model="m")
```

This file is organised in two halves: the factories at the top, and the tests at the bottom. The `connectors` fixture in the middle joins them together.

**Factories.** Each connector type has a *factory*, a function that builds a pair of connectors: one that answers `PROMPT` with `"Paris"` and one whose call fails. How each factory does that is entirely its own business. The fake one just writes a script, with a `ConnectorUnavailableError` as the default reply for the failing one. The OpenAI one sets up a key in the environment and builds two connectors backed by `MockTransport`, one whose server replies with a valid completion and one whose server returns a 500. All factories take `monkeypatch` as an argument, even the fake one that doesn't use it, so that they can all be called the same way.

**A parametrized fixture.** The `connectors` fixture is declared with `params=FACTORIES.values()`. This makes pytest run every test that uses the fixture once for each factory, and inside the fixture, `request.param` is the factory for the current run. The `ids=FACTORIES.keys()` argument names each run after its dictionary key. You can see the result with `uv run pytest tests/connectors/test_contract.py -v`:

```text
tests/connectors/test_contract.py::test_is_a_model_connector[fake] PASSED [ 11%]
tests/connectors/test_contract.py::test_is_a_model_connector[openai] PASSED [ 22%]
tests/connectors/test_contract.py::test_answers_with_a_model_response[fake] PASSED [ 33%]
tests/connectors/test_contract.py::test_answers_with_a_model_response[openai] PASSED [ 44%]
tests/connectors/test_contract.py::test_failures_are_connector_errors[fake] PASSED [ 55%]
tests/connectors/test_contract.py::test_failures_are_connector_errors[openai] PASSED [ 66%]
tests/connectors/test_contract.py::test_repr_names_the_model_and_hides_secrets[fake] PASSED [ 77%]
tests/connectors/test_contract.py::test_repr_names_the_model_and_hides_secrets[openai] PASSED [ 88%]
tests/connectors/test_contract.py::test_the_port_cannot_be_used_directly PASSED [100%]
```

Four contract tests, two connectors, eight runs, plus one test about the port itself.

**Tests that only know the port.** Look at the four contract tests and you will notice they never mention OpenAI or the fake. They only use what `ModelConnector` promises: `generate()`, `model`, `repr()`, a `ModelResponse` on success and a `ConnectorError` on failure. The assertions are deliberately general, too. The answering test checks that `served_model` and `finish_reason` are present, not what their values are, because the fake reports its own model name as the served model while OpenAI reports a dated version. Each connector's own test file is where the precise values are checked.

**The port itself.** The last test isn't parametrized. It is the `TypeError` you saw in section 3.5, written as a test, so that if someone ever changes `ModelConnector` in a way that makes it instantiable, the suite says so.

**Adding a connector.** The module docstring explains how a new connector joins the contract: write a factory and add it to `FACTORIES`. That's all. You don't write a single new test, and every existing contract test runs against the new connector automatically. This is what I meant at the start of the chapter when I said the next connector would be built "in the image" of the first: in chapter 4, the Claude connector will join this dictionary, and it will have to keep every promise the OpenAI connector keeps before AC9 says PASS.

## 3.11 Running the Tests

Time to see the whole suite:

```bash
$ uv run pytest -q
..........................................                               [100%]
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
10 PASS
42 passed in 0.93s
```

Ten out of ten. The 42 tests are the 29 from chapter 2, the 4 fake connector tests, and the 9 runs of the contract tests. Notice also that AC10 is listed after AC9 and not after AC1. That is the `sort_key()` function from chapter 2 earning its keep.

## 3.12 Troubleshooting

- **`TypeError: Can't instantiate abstract class FakeConnector without an implementation for abstract method 'generate'`.** The method name or its indentation is wrong, so Python doesn't see it as part of the class. It must be called `generate` exactly and be indented inside `class FakeConnector`.
- **`AttributeError: 'OpenAIConnector' object has no attribute 'base_url'`.** The `super().__init__()` call is missing, or it comes after the `OpenAI(...)` client is created. It must be the first line of the constructor.
- **`ImportError: cannot import name 'FakeConnector' from 'judgelab.connectors'`.** The import line or the `__all__` entry in `__init__.py` is missing, or the file is not named `fake.py`.
- **The OpenAI contract tests fail with `environment variable CONTRACT_OPENAI_KEY is not set`.** The factory must call `monkeypatch.setenv()` before it creates the connectors, and the fixture must pass its `monkeypatch` to the factory.
- **`fixture 'connectors' not found`.** Check the spelling: the fixture is `connectors`, plural, because it returns a pair.

## 3.13 Exercises

1. Write a class `Broken(ModelConnector)` with `provider = "broken"` and a `generate()` method that raises `RuntimeError`. Add a factory for it to `FACTORIES` and run the contract tests. Which test catches it, and what does the acceptance table say about AC9? Remove it afterwards.
2. Use `FakeConnector` to write a test for this small function, which you can put in the test file itself:

   ```python
   def ask_all(connector, prompts):
       return [connector.generate(p).text for p in prompts]
   ```

   Check both the returned answers and the connector's `prompts`.
3. Record the ABC-versus-Protocol decision from section 3.5 as an Architecture Decision Record. Ask Claude Code to help with the `vbench-docs` skill, which knows how ADRs are numbered and indexed in this repository. Fill in the alternatives table with the pros and cons from section 3.5.
4. `ModelConnector.__init__()` raises `ValueError` for an empty model. Why is that not a `ConnectorError`? Explain it out loud in one or two sentences.
5. Without looking, list the four rows of the table in section 3.2 that went into the port, and say why the key and the timeout didn't.

## 3.14 Committing Your Work

You already committed the refactor in section 3.6. What is left is new behaviour: the fake connector, the tests and the two new criteria. Tick AC9 and AC10 in `T003.md`. All ten criteria now pass, so set **Status** to `Done`, and update **Branch** to this chapter's branch, `refactor/p1-connector-port-T003`. Check the docs, then stage and commit:

```bash
$ python3 .claude/skills/vbench-docs/scripts/docids.py check
34 IDs defined · 0 error(s) · 0 warning(s)
$ git add docs/releases/v0.1/tasks/T003.md src/judgelab/connectors/fake.py src/judgelab/connectors/__init__.py tests/connectors/test_fake_connector.py tests/connectors/test_contract.py
$ git commit
```

```text
feat(connector): add FakeConnector and connector contract tests

FakeConnector answers from a script (text, Refusal or a ConnectorError
to raise) and records prompts, so the core can be tested with no
network, key or cost (REQ-012). Unscripted prompts fail loudly.

The contract tests run against every connector in FACTORIES; a new
connector joins by adding a factory.

AI-Assist: L4
```

Then push the branch and open the pull request with the `vbench-pr` skill, pasting the acceptance table into "How it was verified". This time the branch has two commits that each make sense on their own, a refactor followed by a feature, so instead of the default squash merge, this is the case where [CONTRIBUTING.md](../../CONTRIBUTING.md) suggests a rebase merge, which keeps both commits on `main`.

## 3.15 Wrapping Up

Congratulations, JudgeLab now knows what a connector is! The `ModelConnector` port holds only what has proven to be general: a model, an optional URL, a `generate()` method, and a `repr()` that can't leak secrets. Python refuses to create a connector that doesn't implement the port, the contract tests check that every connector keeps the port's promises, and the `FakeConnector` gives the rest of JudgeLab a model to talk to that is free, instant and does exactly what it's told.

In the next codealong you are going to put all of this to work by writing a second real connector, for Anthropic's Claude. You'll find that the port and the contract tests make it a much more guided job than the first one was: once its factory is in `FACTORIES` and AC9 says PASS, you'll know it keeps every promise the OpenAI connector does. And with two real connectors side by side, you'll be able to judge for yourself whether the key, timeout and retries from section 3.2 have earned a place in the port.
