import os
from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown

console = Console()

load_dotenv()

openai_api_key = os.getenv('OPENAI_API_KEY')
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
google_api_key = os.getenv('GOOGLE_API_KEY')
deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
groq_api_key = os.getenv('GROQ_API_KEY')


def init_client():
    if openai_api_key:
        print(f"OpenAI API Key exists and begins {openai_api_key[:8]}")
    else:
        print("OpenAI API Key not set")

    if anthropic_api_key:
        print(f"Anthropic API Key exists and begins {anthropic_api_key[:7]}")
    else:
        print("Anthropic API Key not set (and this is optional)")

    if google_api_key:
        print(f"Google API Key exists and begins {google_api_key[:2]}")
    else:
        print("Google API Key not set (and this is optional)")

    if deepseek_api_key:
        print(f"DeepSeek API Key exists and begins {deepseek_api_key[:3]}")
    else:
        print("DeepSeek API Key not set (and this is optional)")

    if groq_api_key:
        print(f"Groq API Key exists and begins {groq_api_key[:4]}")
    else:
        print("Groq API Key not set (and this is optional)")


def generate_question() -> str:
    """Generate a challenging question using OpenAI to evaluate LLM intelligence."""
    request = (
        "Please come up with a challenging, nuanced question that I can ask "
        "a number of LLMs to evaluate their intelligence. "
        "Answer only with the question, no explanation."
    )
    messages = [{"role": "user", "content": request}]

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
    )
    return response.choices[0].message.content or ""


def get_answer(question: str, model: str = "gpt-4o-mini") -> str:
    """Get an answer to a question from OpenAI."""
    messages = [{"role": "user", "content": question}]

    client = OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    return response.choices[0].message.content or ""


def display(content: str):
    """Display markdown content in the console using rich."""
    console.print(Markdown(content))


def main():
    init_client()

    question = generate_question()
    display(f"## Question\n\n{question}")

    answer = get_answer(question)
    display(f"## Answer\n\n{answer}")



if __name__ == "__main__":
    main()
