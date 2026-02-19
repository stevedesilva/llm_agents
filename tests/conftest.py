"""Shared fixtures for arena tests."""

import pytest
from unittest.mock import MagicMock

from arena.providers import Provider, _get_anthropic_client, _get_openai_client


@pytest.fixture(autouse=True)
def clear_provider_caches():
    """Clear lru_cache between tests to prevent cross-test contamination."""
    _get_openai_client.cache_clear()
    _get_anthropic_client.cache_clear()
    yield
    _get_openai_client.cache_clear()
    _get_anthropic_client.cache_clear()


@pytest.fixture
def openai_provider():
    return Provider(name="gpt-test", model="gpt-4o", kind="openai", env_var="", api_key_value="sk-test")


@pytest.fixture
def anthropic_provider():
    return Provider(name="claude-test", model="claude-opus-4-6", kind="anthropic", env_var="", api_key_value="sk-ant-test")


@pytest.fixture
def mock_openai_response():
    """Returns a MagicMock shaped like an OpenAI chat completion response."""
    response = MagicMock()
    response.choices = [MagicMock()]
    response.choices[0].message.content = "mocked openai response"
    return response


@pytest.fixture
def mock_anthropic_response():
    """Returns a MagicMock shaped like an Anthropic messages response."""
    response = MagicMock()
    block = MagicMock()
    block.text = "mocked anthropic response"
    response.content = [block]
    return response
