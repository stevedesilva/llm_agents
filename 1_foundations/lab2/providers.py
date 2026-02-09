import os
from dataclasses import dataclass

from anthropic import Anthropic
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


@dataclass
class Provider:
    name: str
    model: str
    kind: str  # "openai" or "anthropic"
    env_var: str
    prefix_len: int = 8
    optional: bool = True
    base_url: str | None = None
    api_key_value: str | None = None
    max_tokens: int = 1000


PROVIDERS: list[Provider] = [
    Provider(
        name="GPT-5-mini",
        model="gpt-5-mini",
        kind="openai",
        env_var="OPENAI_API_KEY",
        prefix_len=8,
        optional=False,
    ),
    Provider(
        name="GPT-5-nano",
        model="gpt-5-nano",
        kind="openai",
        env_var="OPENAI_API_KEY",
        prefix_len=8,
        optional=False,
    ),
    Provider(
        name="Claude Sonnet 4.5",
        model="claude-sonnet-4-5",
        kind="anthropic",
        env_var="ANTHROPIC_API_KEY",
        prefix_len=7,
    ),
    Provider(
        name="Gemini 2.5 Flash",
        model="gemini-2.5-flash",
        kind="openai",
        env_var="GOOGLE_API_KEY",
        prefix_len=2,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    ),
    Provider(
        name="DeepSeek Chat",
        model="deepseek-chat",
        kind="openai",
        env_var="DEEPSEEK_API_KEY",
        prefix_len=3,
        base_url="https://api.deepseek.com/v1",
    ),
    Provider(
        name="Groq GPT-OSS-120B",
        model="openai/gpt-oss-120b",
        kind="openai",
        env_var="GROQ_API_KEY",
        prefix_len=4,
        base_url="https://api.groq.com/openai/v1",
    ),
    Provider(
        name="Ollama Llama 3.2",
        model="llama3.2",
        kind="openai",
        env_var="",
        base_url="http://localhost:11434/v1",
        api_key_value="ollama",
    ),
]


def validate_api_keys() -> None:
    """Print API key status for each unique env_var across all providers."""
    seen: set[str] = set()
    for provider in PROVIDERS:
        env_var = provider.env_var
        if not env_var or env_var in seen:
            continue
        seen.add(env_var)

        key = os.getenv(env_var)
        if key:
            print(f"{env_var} exists and begins {key[:provider.prefix_len]}")
        elif provider.optional:
            print(f"{env_var} not set (and this is optional)")
        else:
            print(f"{env_var} not set")


def query_provider(provider: Provider, question: str) -> str | None:
    """Query a provider and return the answer, or None if the key is missing."""
    api_key = provider.api_key_value or os.getenv(provider.env_var)

    if not api_key and provider.env_var:
        return None

    messages = [{"role": "user", "content": question}]

    if provider.kind == "anthropic":
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model=provider.model,
            messages=messages,
            max_tokens=provider.max_tokens,
        )
        return response.content[0].text

    # OpenAI-compatible
    kwargs: dict = {}
    if provider.base_url:
        kwargs["base_url"] = provider.base_url
    if api_key:
        kwargs["api_key"] = api_key

    client = OpenAI(**kwargs)
    response = client.chat.completions.create(
        model=provider.model,
        messages=messages,
    )
    return response.choices[0].message.content or ""
