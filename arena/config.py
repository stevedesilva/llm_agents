"""Shared configuration — default providers and constants used by CLI and Gradio entry points."""

from arena.providers import Provider

MAX_CLARIFICATION_ROUNDS = 5
MAX_CLARIFY_ANSWER_LENGTH = 500
CLARIFICATION_MODEL = "gpt-5.2"

DEFAULT_PROVIDERS: list[Provider] = [
    Provider(
        name="GPT-5.2",
        model="gpt-5.2",
        kind="openai",
        env_var="OPENAI_API_KEY",
        optional=False,
    ),
    Provider(
        name="GPT-5-mini",
        model="gpt-5-mini",
        kind="openai",
        env_var="OPENAI_API_KEY",
        optional=False,
    ),
    Provider(
        name="Claude Opus 4.6",
        model="claude-opus-4-6",
        kind="anthropic",
        env_var="ANTHROPIC_API_KEY",
    ),
    Provider(
        name="Gemini 3.0 Flash",
        model="gemini-3.0-flash",
        kind="openai",
        env_var="GOOGLE_API_KEY",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    ),
    Provider(
        name="DeepSeek Chat",
        model="deepseek-chat",
        kind="openai",
        env_var="DEEPSEEK_API_KEY",
        base_url="https://api.deepseek.com/v1",
    ),
    Provider(
        name="Groq GPT-OSS-120B",
        model="openai/gpt-oss-120b",
        kind="openai",
        env_var="GROQ_API_KEY",
        base_url="https://api.groq.com/openai/v1",
    ),
]
