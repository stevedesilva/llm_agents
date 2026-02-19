"""Gradio UI for the LLM Arena — chat-style question clarification + arena results."""

import asyncio

import gradio as gr
from dotenv import load_dotenv
from openai import OpenAI

from arena import QUERY_TIMEOUT, Provider, judge_all, query_provider, validate_api_keys
from arena.providers import MAX_INPUT_LENGTH

MAX_CLARIFICATION_ROUNDS = 5

PROVIDERS: list[Provider] = [
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

_openai_client: OpenAI | None = None


def _get_openai() -> OpenAI:
    """Return a module-level OpenAI client singleton."""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI()
    return _openai_client


# ---------------------------------------------------------------------------
# Clarification helpers
# ---------------------------------------------------------------------------


def check_clarity(question: str) -> str:
    """Ask GPT-5.2 whether the question is clear. Returns 'CLEAR' or clarifying questions."""
    client = _get_openai()
    response = client.chat.completions.create(
        model="gpt-5.2",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a question analyst. Evaluate if the following question "
                    "is clear and specific enough to get a meaningful answer from an LLM. "
                    "If the question is clear, respond with exactly 'CLEAR'. "
                    "If not, ask 1-2 short clarifying questions to help refine it."
                ),
            },
            {"role": "user", "content": question[:MAX_INPUT_LENGTH]},
        ],
        max_tokens=500,
    )
    return (response.choices[0].message.content or "").strip()


def refine_question(current_question: str, user_answer: str) -> str:
    """Ask GPT-5.2 to rewrite the question incorporating clarifying answers."""
    client = _get_openai()
    response = client.chat.completions.create(
        model="gpt-5.2",
        messages=[
            {
                "role": "system",
                "content": (
                    "Rewrite the user's original question incorporating their "
                    "clarifying answers into a single, clear, refined question. "
                    "Respond only with the refined question."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Original question: {current_question[:MAX_INPUT_LENGTH]}\n"
                    f"Clarifying answers: {user_answer[:500]}"
                ),
            },
        ],
        max_tokens=500,
    )
    return (response.choices[0].message.content or "").strip()


# ---------------------------------------------------------------------------
# Arena runner
# ---------------------------------------------------------------------------


async def run_arena(question: str) -> tuple[str, str, str, str]:
    """Run the full arena and return (final_question_md, answers_md, rankings_md, winner_md)."""
    question = question[:MAX_INPUT_LENGTH].strip()
    available = [p for p in PROVIDERS if p.has_api_key()]
    skipped = [p for p in PROVIDERS if not p.has_api_key()]

    async def _query_one(provider: Provider) -> tuple[Provider, str | None]:
        try:
            answer = await asyncio.wait_for(
                asyncio.to_thread(query_provider, provider, question),
                timeout=QUERY_TIMEOUT,
            )
            return provider, answer
        except asyncio.TimeoutError:
            return provider, None
        except Exception:
            return provider, None

    results = await asyncio.gather(*[_query_one(p) for p in available])

    competitors: list[str] = []
    answers: list[str] = []
    judges: list[Provider] = []

    answers_parts: list[str] = []
    for provider, answer in results:
        if answer is None:
            answers_parts.append(f"**{provider.name}:** *Error — no response*\n")
            continue
        competitors.append(provider.name)
        answers.append(answer)
        judges.append(provider)
        answers_parts.append(f"### {provider.name}\n\n{answer}\n")

    for p in skipped:
        answers_parts.append(f"*Skipped {p.name} — API key not set*\n")

    answers_md = "\n".join(answers_parts)

    if len(competitors) < 2:
        return (
            f"## Final Question\n\n{question}",
            answers_md,
            "**Not enough competitors to judge (need at least 2).**",
            "",
        )

    per_judge, averaged = await judge_all(question, competitors, answers, judges)

    rankings_parts: list[str] = []
    for judge_name, ranking in per_judge.items():
        if ranking:
            lines = ", ".join(f"{rank}. {name}" for rank, name in ranking)
            rankings_parts.append(f"**{judge_name}'s ranking:** {lines}")
        else:
            rankings_parts.append(f"**{judge_name}:** *failed to judge*")

    rankings_parts.append("\n## Final Averaged Rankings\n")
    for position, (avg_rank, name) in enumerate(averaged, start=1):
        rankings_parts.append(f"**{position}.** {name} (avg rank: {avg_rank:.2f})")

    rankings_md = "\n\n".join(rankings_parts)

    winner_md = ""
    if averaged:
        _, winner_name = averaged[0]
        winner_idx = competitors.index(winner_name)
        winner_md = f"## Winning Response — {winner_name}\n\n{answers[winner_idx]}"

    return (f"## Final Question\n\n{question}", answers_md, rankings_md, winner_md)


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------


def build_ui() -> gr.Blocks:
    with gr.Blocks(title="LLM Arena") as demo:
        gr.Markdown("# LLM Arena")
        gr.Markdown("Ask a question and have multiple LLMs compete to give the best answer.")

        # State
        current_question = gr.State("")
        is_clear = gr.State(False)
        clarify_round = gr.State(0)

        # Phase 1 — Clarification chat
        with gr.Group():
            gr.Markdown("## Step 1: Ask your question")
            chatbot = gr.Chatbot(label="Clarification")
            msg = gr.Textbox(
                placeholder="Type your question here...",
                label="Your message",
                show_label=False,
            )
            with gr.Row():
                submit_btn = gr.Button("Send", variant="primary")
                arena_btn = gr.Button("Run Arena", variant="secondary", interactive=False)

        # Phase 2 — Results
        with gr.Group(visible=False) as results_group:
            gr.Markdown("## Results")
            final_q_md = gr.Markdown()
            answers_md = gr.Markdown()
            rankings_md = gr.Markdown()
            winner_md = gr.Markdown()

        # ------------------------------------------------------------------
        # Handlers
        # ------------------------------------------------------------------

        async def on_submit(user_message, chat_history, question, clear, rounds):
            if not user_message.strip():
                return chat_history, "", question, clear, rounds, gr.update(interactive=False)

            chat_history = chat_history + [{"role": "user", "content": user_message}]

            if not question:
                question = user_message.strip()[:MAX_INPUT_LENGTH]
                reply = await asyncio.to_thread(check_clarity, question)
                rounds += 1

                if reply.upper() == "CLEAR":
                    chat_history.append(
                        {"role": "assistant", "content": "Your question is clear! Click **Run Arena** to proceed."}
                    )
                    return chat_history, "", question, True, rounds, gr.update(interactive=True)
                else:
                    chat_history.append({"role": "assistant", "content": reply})
                    return chat_history, "", question, False, rounds, gr.update(interactive=False)
            else:
                if rounds >= MAX_CLARIFICATION_ROUNDS:
                    chat_history.append(
                        {"role": "assistant", "content": f"Maximum clarification rounds reached. Proceeding with:\n\n**{question}**\n\nClick **Run Arena** to proceed."}
                    )
                    return chat_history, "", question, True, rounds, gr.update(interactive=True)

                refined = await asyncio.to_thread(refine_question, question, user_message.strip()[:500])
                question = refined[:MAX_INPUT_LENGTH]
                chat_history.append(
                    {"role": "assistant", "content": f"Refined question: **{refined}**"}
                )

                reply = await asyncio.to_thread(check_clarity, refined)
                rounds += 1

                if reply.upper() == "CLEAR":
                    chat_history.append(
                        {"role": "assistant", "content": "Your question is now clear! Click **Run Arena** to proceed."}
                    )
                    return chat_history, "", question, True, rounds, gr.update(interactive=True)
                else:
                    chat_history.append({"role": "assistant", "content": reply})
                    return chat_history, "", question, False, rounds, gr.update(interactive=False)

        submit_outputs = [chatbot, msg, current_question, is_clear, clarify_round, arena_btn]
        submit_inputs = [msg, chatbot, current_question, is_clear, clarify_round]

        submit_btn.click(on_submit, submit_inputs, submit_outputs)
        msg.submit(on_submit, submit_inputs, submit_outputs)

        async def on_run_arena(question, clear):
            if not clear or not question:
                return gr.update(visible=False), "", "", "", ""

            fq, ans, rank, win = await run_arena(question)
            return gr.update(visible=True), fq, ans, rank, win

        arena_btn.click(
            on_run_arena,
            [current_question, is_clear],
            [results_group, final_q_md, answers_md, rankings_md, winner_md],
        )

    return demo


if __name__ == "__main__":
    load_dotenv()
    validate_api_keys(PROVIDERS)
    app = build_ui()
    app.launch(server_name="127.0.0.1", share=False)
