"""Tests for arena.providers — Provider.has_api_key, query_provider, validate_api_keys."""

import os
from dataclasses import replace
from unittest.mock import MagicMock, patch

import pytest

from arena.providers import Provider, query_provider, validate_api_keys


class TestHasApiKey:
    def test_has_api_key_value(self):
        p = Provider(name="t", model="m", kind="openai", env_var="", api_key_value="key")
        assert p.has_api_key() is True

    def test_no_env_var_no_key_returns_false(self):
        p = Provider(name="t", model="m", kind="openai", env_var="")
        assert p.has_api_key() is False

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
        p_bad = replace(p, kind="unknown")  # type: ignore[arg-type]
        with pytest.raises(ValueError, match="Unknown provider kind"):
            query_provider(p_bad, "hello")

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

    @patch("arena.providers._get_openai_client")
    def test_openai_returns_content_string(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "hello world"
        mock_client.chat.completions.create.return_value = mock_response

        p = Provider(name="t", model="m", kind="openai", env_var="", api_key_value="k")
        assert query_provider(p, "hi") == "hello world"

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

    @patch("arena.providers._get_anthropic_client")
    def test_anthropic_returns_text(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_response = MagicMock()
        block = MagicMock()
        block.text = "anthropic response"
        mock_response.content = [block]
        mock_client.messages.create.return_value = mock_response

        p = Provider(name="t", model="m", kind="anthropic", env_var="", api_key_value="k")
        assert query_provider(p, "hi") == "anthropic response"

    @patch("arena.providers._get_openai_client")
    def test_openai_passes_base_url(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "ok"
        mock_client.chat.completions.create.return_value = mock_response

        p = Provider(
            name="t", model="m", kind="openai", env_var="",
            api_key_value="k", base_url="http://localhost:11434/v1",
        )
        query_provider(p, "hi")
        mock_get_client.assert_called_once_with(
            base_url="http://localhost:11434/v1", api_key="k"
        )


class TestValidateApiKeys:
    def test_key_set_prints_set(self, capsys):
        p = Provider(name="t", model="m", kind="openai", env_var="MY_KEY")
        with patch.dict(os.environ, {"MY_KEY": "sk-123"}):
            validate_api_keys([p])
        assert "MY_KEY is set" in capsys.readouterr().out

    def test_optional_missing_prints_optional(self, capsys):
        p = Provider(name="t", model="m", kind="openai", env_var="MISS", optional=True)
        with patch.dict(os.environ, {}, clear=True):
            validate_api_keys([p])
        assert "optional" in capsys.readouterr().out

    def test_non_optional_missing(self, capsys):
        p = Provider(name="t", model="m", kind="openai", env_var="MISS", optional=False)
        with patch.dict(os.environ, {}, clear=True):
            validate_api_keys([p])
        out = capsys.readouterr().out
        assert "MISS not set" in out
        assert "optional" not in out

    def test_deduplicates_same_env_var(self, capsys):
        p1 = Provider(name="a", model="m", kind="openai", env_var="SAME")
        p2 = Provider(name="b", model="m", kind="openai", env_var="SAME")
        with patch.dict(os.environ, {"SAME": "val"}):
            validate_api_keys([p1, p2])
        assert capsys.readouterr().out.count("SAME is set") == 1

    def test_empty_env_var_is_skipped(self, capsys):
        p = Provider(name="t", model="m", kind="openai", env_var="", api_key_value="ollama")
        validate_api_keys([p])
        assert capsys.readouterr().out == ""
