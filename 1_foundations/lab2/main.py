import os
from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown

load_dotenv()

console = Console()

API_KEYS = [
    ("OPENAI_API_KEY", "OpenAI", 8, False),
    ("ANTHROPIC_API_KEY", "Anthropic", 7, True),
    ("GOOGLE_API_KEY", "Google", 2, True),
    ("DEEPSEEK_API_KEY", "DeepSeek", 3, True),
    ("GROQ_API_KEY", "Groq", 4, True),
]


def print_api_key_status():
    """Print the status of all configured API keys."""
    for env_var, name, prefix_len, optional in API_KEYS:
        key = os.getenv(env_var)
        if key:
            print(f"{name} API Key exists and begins {key[:prefix_len]}")
        else:
            suffix = " (and this is optional)" if optional else ""
            print(f"{name} API Key not set{suffix}")


def create_client() -> OpenAI:
    """Create and return an OpenAI client."""
    return OpenAI()


def generate_question(client: OpenAI) -> str:
    """Generate a challenging question using OpenAI to evaluate LLM intelligence."""
    request = (
        "Please come up with a challenging, nuanced question that I can ask "
        "a number of LLMs to evaluate their intelligence. "
        "Answer only with the question, no explanation."
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": request}],
    )
    return response.choices[0].message.content or ""


def get_answer(client: OpenAI, question: str, model: str = "gpt-4o-mini") -> str:
    """Get an answer to a question from OpenAI."""
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": question}],
    )
    return response.choices[0].message.content or ""


def display(content: str):
    """Display markdown content in the console using rich."""
    console.print(Markdown(content))


def main():
    print_api_key_status()

    client = create_client()

    question = generate_question(client)
    display(f"## Question\n\n{question}")

    answer = get_answer(client, question)
    display(f"## Answer\n\n{answer}")


if __name__ == "__main__":
    main()
