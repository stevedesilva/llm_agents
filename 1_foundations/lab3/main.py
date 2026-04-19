import logging
import os
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from pypdf import PdfReader

load_dotenv(override=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

NAME = "Steve de Silva"
AGENT_MODEL = "gpt-4o-mini"
EVALUATOR_MODEL = "gemini-2.5-flash"
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


class Evaluation(BaseModel):
    is_acceptable: bool
    feedback: str


def require_env(var_name: str) -> str:
    value = os.getenv(var_name)
    if not value:
        raise EnvironmentError(f"Missing required environment variable: {var_name}")
    return value


def read_pdf_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"PDF not found at {path}")
    reader = PdfReader(path)
    chunks = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            chunks.append(text)
    return "\n".join(chunks)


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Summary file not found at {path}")
    return path.read_text(encoding="utf-8")


def build_system_prompt(name: str, summary: str, linkedin: str) -> str:
    prompt = (
        f"You are acting as {name}. You are answering questions on {name}'s website, "
        f"particularly questions related to {name}'s career, background, skills and experience. "
        f"Your responsibility is to represent {name} for interactions on the website as faithfully as possible. "
        f"You are given a summary of {name}'s background and LinkedIn profile which you can use to answer questions. "
        "Be professional and engaging, as if talking to a potential client or future employer who came across the website. "
        "If you don't know the answer, say so."
    )
    prompt += f"\n\n## Summary:\n{summary}\n\n## LinkedIn Profile:\n{linkedin}\n\n"
    prompt += f"With this context, please chat with the user, always staying in character as {name}."
    return prompt


def build_evaluator_system_prompt(name: str, summary: str, linkedin: str) -> str:
    prompt = (
        "You are an evaluator that decides whether a response to a question is acceptable. "
        "You are provided with a conversation between a User and an Agent. "
        "Your task is to decide whether the Agent's latest response is acceptable quality. "
        f"The Agent is playing the role of {name} and is representing {name} on their website. "
        "The Agent has been instructed to be professional and engaging, as if talking to a potential client or future employer who came across the website. "
        f"The Agent has been provided with context on {name} in the form of their summary and LinkedIn details. Here's the information:"
    )
    prompt += f"\n\n## Summary:\n{summary}\n\n## LinkedIn Profile:\n{linkedin}\n\n"
    prompt += "With this context, please evaluate the latest response, replying with whether the response is acceptable and your feedback."
    return prompt


def normalize_history(history):
    normalized = []
    for item in history or []:
        if isinstance(item, dict):
            role = item.get("role")
            content = item.get("content")
            if role in {"user", "assistant", "system"} and content is not None:
                normalized.append({"role": role, "content": str(content)})
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            user_msg, assistant_msg = item
            if user_msg:
                normalized.append({"role": "user", "content": str(user_msg)})
            if assistant_msg:
                normalized.append({"role": "assistant", "content": str(assistant_msg)})
    return normalized


def format_history_for_eval(history) -> str:
    lines = []
    for msg in history:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        lines.append(f"{role}: {content}")
    return "\n".join(lines) if lines else "(no prior conversation)"


def content_to_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks = []
        for part in content:
            if isinstance(part, dict) and part.get("type") == "text":
                text = part.get("text")
                if text:
                    chunks.append(str(text))
            elif isinstance(part, str):
                chunks.append(part)
        if chunks:
            return "\n".join(chunks)
    return ""


def evaluator_user_prompt(reply, message, history):
    user_prompt = "Here's the conversation between the User and the Agent:\n\n"
    user_prompt += f"{format_history_for_eval(history)}\n\n"
    user_prompt += f"Here's the latest message from the User:\n\n{message}\n\n"
    user_prompt += f"Here's the latest response from the Agent:\n\n{reply}\n\n"
    user_prompt += "Please evaluate the response, replying with whether it is acceptable and your feedback."
    return user_prompt


BASE_DIR = Path(__file__).parent
SUMMARY = read_text(BASE_DIR / "me" / "summary.txt")
LINKEDIN = read_pdf_text(BASE_DIR / "me" / "Steve_deSilva_CV.pdf")
SYSTEM_PROMPT = build_system_prompt(NAME, SUMMARY, LINKEDIN)
EVALUATOR_SYSTEM_PROMPT = build_evaluator_system_prompt(NAME, SUMMARY, LINKEDIN)

openai_client = OpenAI(api_key=require_env("OPENAI_API_KEY"))
gemini_client = OpenAI(api_key=require_env("GOOGLE_API_KEY"), base_url=GEMINI_BASE_URL)


def generate_reply(messages):
    try:
        response = openai_client.chat.completions.create(model=AGENT_MODEL, messages=messages)
        reply_text = content_to_text(response.choices[0].message.content)
        return reply_text or "I am sorry, I do not have a response right now."
    except Exception:
        logger.exception("Agent model call failed")
        return "I am sorry, I am having trouble responding right now. Please try again in a moment."


def evaluate(reply, message, history):
    try:
        messages = [
            {"role": "system", "content": EVALUATOR_SYSTEM_PROMPT},
            {"role": "user", "content": evaluator_user_prompt(reply, message, history)},
        ]
        response = gemini_client.chat.completions.parse(
            model=EVALUATOR_MODEL,
            messages=messages,
            response_format=Evaluation,
        )
        return response.choices[0].message.parsed
    except Exception:
        logger.exception("Evaluator model call failed")
        return None


def rerun(reply, message, history, feedback):
    updated_system_prompt = (
        SYSTEM_PROMPT
        + "\n\n## Previous answer rejected\n"
        + "You just tried to reply, but the quality control rejected your reply\n"
    )
    updated_system_prompt += f"## Your attempted answer:\n{reply}\n\n"
    updated_system_prompt += f"## Reason for rejection:\n{feedback}\n\n"
    messages = [{"role": "system", "content": updated_system_prompt}] + history + [{"role": "user", "content": message}]
    return generate_reply(messages)


def chat(message, history):
    if "patent" in message.lower():
        system = (
            SYSTEM_PROMPT
            + "\n\nEverything in your reply needs to be in pig latin - "
            + "it is mandatory that you respond only and entirely in pig latin"
        )
    else:
        system = SYSTEM_PROMPT

    normalized_history = normalize_history(history)
    messages = [{"role": "system", "content": system}] + normalized_history + [{"role": "user", "content": message}]
    reply = generate_reply(messages)

    evaluation = evaluate(reply, message, normalized_history)

    if evaluation and evaluation.is_acceptable:
        logger.info("Passed evaluation - returning reply")
        logger.info("Assistant reply: %s", reply)
        return reply

    if evaluation:
        logger.info("Failed evaluation - retrying")
        logger.info("Evaluator feedback: %s", evaluation.feedback)
        reply = rerun(reply, message, normalized_history, evaluation.feedback)
        logger.info("Assistant reply: %s", reply)
        return reply

    logger.info("Skipping rerun because evaluator is unavailable")
    logger.info("Assistant reply: %s", reply)
    return reply


def main():
    gr.ChatInterface(chat).launch()


if __name__ == "__main__":
    main()
