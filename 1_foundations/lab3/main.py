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
