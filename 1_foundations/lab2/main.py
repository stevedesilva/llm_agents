import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from anthropic import Anthropic
from IPython.display import Markdown, display

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

def main():
    init_client()



if __name__ == "__main__":
    main()
