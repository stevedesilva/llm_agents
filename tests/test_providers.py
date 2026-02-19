"""Tests for arena.providers — Provider.has_api_key and query_provider edge cases."""

import os
from unittest.mock import MagicMock, patch

from arena.providers import Provider, query_provider


class TestHasApiKey:
    def test_has_api_key_value(self):
        p = Provider(name="t", model="m", kind="openai", env_var="", api_key_value="key")
        assert p.has_api_key() is True

    def test_no_env_var_required(self):
        p = Provider(name="t", model="m", kind="openai", env_var="")
        assert p.has_api_key() is True

    def test_env_var_set(self):
        p = Provider(name="t", model="m", kind="openai", env_var="TEST_KEY")
        with patch.dict(os.environ, {"TEST_KEY": "sk-123"}):
            assert p.has_api_key() is True

    def test_env_var_not_set(self):
        p = Provider(name="t", model="m", kind="openai", env_var="MISSING_KEY")
        with patch.dict(os.environ, {}, clear=True):
            assert p.has_api_key() is False


class TestQueryProvider:
    def test_returns_none_when_no_key(self):
        p = Provider(name="t", model="m", kind="openai", env_var="MISSING")
        with patch.dict(os.environ, {}, clear=True):
            assert query_provider(p, "hello") is None

    def test_unknown_kind_raises(self):
        p = Provider(name="t", model="m", kind="openai", env_var="", api_key_value="k")
        # Monkey-patch kind to invalid value to test the guard
        object.__setattr__(p, "kind", "unknown")
        try:
            query_provider(p, "hello")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Unknown provider kind" in str(e)

    @patch("arena.providers._get_openai_client")
    def test_openai_returns_none_for_empty_content(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_client.chat.completions.create.return_value = mock_response

        p = Provider(name="t", model="m", kind="openai", env_var="", api_key_value="k")
        result = query_provider(p, "hello")
        assert result is None

    @patch("arena.providers._get_anthropic_client")
    def test_anthropic_returns_none_for_empty_content(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = []
        mock_client.messages.create.return_value = mock_response

        p = Provider(name="t", model="m", kind="anthropic", env_var="", api_key_value="k")
        result = query_provider(p, "hello")
        assert result is None
