import os
import sys

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from rich.console import Console
from rich.markdown import Markdown

console = Console()


def load_api_key() -> str | None:
    """Load and validate the OpenAI API key from environment."""
    load_dotenv(override=True)
    api_key = os.getenv("OPENAI_API_KEY")

    if api_key:
        print(f"OpenAI API Key exists and begins {api_key[:8]}")
    else:
        print("OpenAI API Key not set - please head to the troubleshooting guide in the setup folder")

    return api_key


def create_client(api_key: str) -> OpenAI:
    """Create an OpenAI client with the provided API key."""
    return OpenAI(api_key=api_key)


def chat(client: OpenAI, prompt: str, model: str = "gpt-4.1-nano") -> str | None:
    """Send a chat completion request and return the response content."""
    messages = [{"role": "user", "content": prompt}]

    try:
        response = client.chat.completions.create(model=model, messages=messages)
        return response.choices[0].message.content
    except OpenAIError as e:
        print(f"OpenAI API error: {e}")
        return None


def main():
    """Main entry point for the script."""
    api_key = load_api_key()
    if not api_key:
        sys.exit(1)

    client = create_client(api_key)

    # Ask the model its name
    response = chat(client, "What is your name?")
    if response:
        console.print(Markdown(response))

    # Generate a challenging IQ question
    iq_prompt = "Please propose a hard, challenging question to assess someone's IQ. Respond only with the question."
    question = chat(client, iq_prompt, model="gpt-4.1-mini")
    if question:
        console.print(Markdown(question))


 # Other question -- split from above
    messages = "Pick a business area that might be worth exploring for an Agentic AI opportunity. Keep it short and clear."
    business_area = chat(client, messages, model="gpt-4.1-mini")
    if response:
        console.print(Markdown(response))
        
    messages = f"Present a pain point in the {business_idea} industry - something challenging that might be ripe for an Agentic solution."
    pain_point = chat(client, messages, model="gpt-4.1-mini")
    if response:
        console.print(Markdown(response))

    messages = f"Present a pain point in the {pain_point} industry - something challenging that might be ripe for an Agentic solution."
    soluton = chat(client, messages, model="gpt-4.1-mini")
    if response:
        console.print(Markdown(    soluton = chat(client, messages, model="gpt-4.1-mini")
))

if __name__ == "__main__":
    main()