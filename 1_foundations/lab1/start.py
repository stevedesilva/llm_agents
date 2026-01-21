import os
import sys

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError


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
        print(response)

    # Generate a challenging IQ question
    iq_prompt = "Please propose a hard, challenging question to assess someone's IQ. Respond only with the question."
    question = chat(client, iq_prompt, model="gpt-4.1-mini")
    if question:
        print(question)


if __name__ == "__main__":
    main()