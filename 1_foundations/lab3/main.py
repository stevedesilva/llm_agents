from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
from pathlib import Path
import gradio as gr

load_dotenv(override=True)

openai = OpenAI()

pdf_path = Path(__file__).parent / "me" / "Steve_deSilva_CV.pdf"
if not pdf_path.exists():
    raise FileNotFoundError(f"PDF not found at {pdf_path}")

reader = PdfReader(pdf_path)
linkedin = ""
for page in reader.pages:
    text = page.extract_text()
    if text:
        linkedin += text

print(linkedin)

summary_path = Path(__file__).parent / "me" / "summary.txt"
if not summary_path.exists():
    raise FileNotFoundError(f"Summary file not found at {summary_path}")

with summary_path.open("r", encoding="utf-8") as f:
    summary = f.read()

name = "Steve de Silva"

system_prompt = (
    f"You are acting as {name}. You are answering questions on {name}'s website, \
particularly questions related to {name}'s career, background, skills and experience. \
Your responsibility is to represent {name} for interactions on the website as faithfully as possible. \
You are given a summary of {name}'s background and LinkedIn profile which you can use to answer questions. \
Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
If you don't know the answer, say so."
)

system_prompt += f"\n\n## Summary:\n{summary}\n\n## LinkedIn Profile:\n{linkedin}\n\n"
system_prompt += f"With this context, please chat with the user, always staying in character as {name}."


print(system_prompt)


def chat(message, history):
    messages = (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": message}]
    )
    response = openai.chat.completions.create(model="gpt-4o-mini", messages=messages)
    return response.choices[0].message.content


gr.ChatInterface(chat).launch()
