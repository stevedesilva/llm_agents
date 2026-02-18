"""Gradio UI for the LLM Arena — chat-style question clarification + arena results."""

import asyncio
import os
import sys

import gradio as gr
from openai import OpenAI

# Ensure local imports resolve when running from the project root.
sys.path.insert(0, os.path.dirname(__file__))

from judge import judge_all  # noqa: E402
from providers import PROVIDERS, Provider, query_provider, validate_api_keys  # noqa: E402

MAX_CLARIFICATION_ROUNDS = 5


def has_api_key(provider: Provider) -> bool:
    """Check whether a provider's API key is available without making an API call."""
    if provider.api_key_value:
        return True
    if not provider.env_var:
        return True
    return bool(os.getenv(provider.env_var))


# ---------------------------------------------------------------------------
# Clarification helpers
# ---------------------------------------------------------------------------

def check_clarity(question: str) -> str:
    """Ask GPT-5.2 whether the question is clear. Returns 'CLEAR' or clarifying questions."""
    client = OpenAI()
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
            {"role": "user", "content": question},
        ],
    )
    return (response.choices[0].message.content or "").strip()


def refine_question(current_question: str, user_answer: str) -> str:
    """Ask GPT-5.2 to rewrite the question incorporating clarifying answers."""
    client = OpenAI()
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
                    f"Original question: {current_question}\n"
                    f"Clarifying answers: {user_answer}"
                ),
            },
        ],
    )
    return (response.choices[0].message.content or "").strip()


# ---------------------------------------------------------------------------
# Arena runner
# ---------------------------------------------------------------------------

async def run_arena(question: str) -> tuple[str, str, str, str]:
    """Run the full arena and return (final_question_md, answers_md, rankings_md, winner_md)."""
    available = [p for p in PROVIDERS if has_api_key(p)]
    skipped = [p for p in PROVIDERS if not has_api_key(p)]

    async def _query_one(provider: Provider) -> tuple[Provider, str | None]:
        try:
            answer = await asyncio.to_thread(query_provider, provider, question)
            return provider, answer
        except Exception as e:
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

        def on_submit(user_message, chat_history, question, clear, rounds):
            if not user_message.strip():
                return chat_history, "", question, clear, rounds, gr.update(interactive=False)

            chat_history = chat_history + [{"role": "user", "content": user_message}]

            if not question:
                # First message — this is the question
                question = user_message.strip()
                reply = check_clarity(question)
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
                # Follow-up — user answering clarifying questions
                if rounds >= MAX_CLARIFICATION_ROUNDS:
                    chat_history.append(
                        {"role": "assistant", "content": f"Maximum clarification rounds reached. Proceeding with:\n\n**{question}**\n\nClick **Run Arena** to proceed."}
                    )
                    return chat_history, "", question, True, rounds, gr.update(interactive=True)

                refined = refine_question(question, user_message.strip())
                question = refined
                chat_history.append(
                    {"role": "assistant", "content": f"Refined question: **{refined}**"}
                )

                reply = check_clarity(refined)
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
    validate_api_keys()
    app = build_ui()
    app.launch()
