"""Provider definitions and query helpers for OpenAI-compatible and Anthropic LLM APIs."""

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

from anthropic import Anthropic
from openai import OpenAI

QUERY_TIMEOUT = 30.0
MAX_INPUT_LENGTH = 2000


@dataclass
class Provider:
    """Configuration for a single LLM provider, including model, API endpoint, and auth details."""

    name: str
    model: str
    kind: Literal["openai", "anthropic"]
    env_var: str
    optional: bool = True
    base_url: str | None = None
    api_key_value: str | None = None
    max_tokens: int = 1000

    def has_api_key(self) -> bool:
        """Return True if an API key is available for this provider."""
        if self.api_key_value is not None:
            return True
        if not self.env_var:
            return False
        return bool(os.getenv(self.env_var))


@lru_cache(maxsize=None)
def _get_openai_client(base_url: str | None, api_key: str | None) -> OpenAI:
    """Return a cached OpenAI client for the given base_url and api_key."""
    kwargs: dict[str, str] = {}
    if base_url:
        kwargs["base_url"] = base_url
    if api_key:
        kwargs["api_key"] = api_key
    return OpenAI(**kwargs)


@lru_cache(maxsize=None)
def _get_anthropic_client(api_key: str | None) -> Anthropic:
    """Return a cached Anthropic client for the given api_key."""
    return Anthropic(api_key=api_key)


def validate_api_keys(providers: list["Provider"]) -> None:
    """Print API key status for each unique env_var across the given providers."""
    seen: set[str] = set()
    for provider in providers:
        env_var = provider.env_var
        if not env_var or env_var in seen:
            continue
        seen.add(env_var)

        key = os.getenv(env_var)
        if key:
            print(f"{env_var} is set")
        elif provider.optional:
            print(f"{env_var} not set (optional)")
        else:
            print(f"{env_var} not set")


def query_provider(provider: Provider, question: str) -> str | None:
    """Query a provider and return the answer, or None if the key is missing."""
    api_key = provider.api_key_value or os.getenv(provider.env_var)

    if not api_key and provider.env_var:
        return None

    messages: list[dict[str, str]] = [{"role": "user", "content": question}]

    if provider.kind == "anthropic":
        client = _get_anthropic_client(api_key=api_key)
        response = client.messages.create(
            model=provider.model,
            messages=messages,
            max_tokens=provider.max_tokens,
        )
        if not response.content:
            return None
        return response.content[0].text

    if provider.kind == "openai":
        client = _get_openai_client(base_url=provider.base_url, api_key=api_key)
        response = client.chat.completions.create(
            model=provider.model,
            messages=messages,
        )
        content = response.choices[0].message.content
        return content if content else None

    raise ValueError(f"Unknown provider kind: {provider.kind!r}")
