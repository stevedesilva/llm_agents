"""Gradio UI for the LLM Arena — chat-style question clarification + arena results."""

import asyncio
import time

import gradio as gr
from dotenv import load_dotenv

from arena import (
    CLARIFICATION_MODEL,
    DEFAULT_PROVIDERS,
    MAX_CLARIFICATION_ROUNDS,
    MAX_CLARIFY_ANSWER_LENGTH,
    QUERY_TIMEOUT,
    Provider,
    judge_all,
    query_provider,
    validate_api_keys,
)
from arena.providers import MAX_INPUT_LENGTH, _get_openai_client


# ---------------------------------------------------------------------------
# Clarification helpers
# ---------------------------------------------------------------------------


def check_clarity(question: str) -> str:
    """Ask the clarification model whether the question is clear."""
    client = _get_openai_client(base_url=None, api_key=None)
    response = client.chat.completions.create(
        model=CLARIFICATION_MODEL,
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
    """Ask the clarification model to rewrite the question incorporating clarifying answers."""
    client = _get_openai_client(base_url=None, api_key=None)
    response = client.chat.completions.create(
        model=CLARIFICATION_MODEL,
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
                    f"Clarifying answers: {user_answer[:MAX_CLARIFY_ANSWER_LENGTH]}"
                ),
            },
        ],
        max_tokens=500,
    )
    return (response.choices[0].message.content or "").strip()


# ---------------------------------------------------------------------------
# Provider status helper
# ---------------------------------------------------------------------------


def _provider_status_md(providers: list[Provider]) -> str:
    """Build a markdown string showing which providers are available."""
    parts: list[str] = []
    for p in providers:
        if p.has_api_key():
            parts.append(f"🟢 {p.name}")
        else:
            parts.append(f"⚪ {p.name} *(no key)*")
    return " &nbsp;|&nbsp; ".join(parts)


# ---------------------------------------------------------------------------
# Arena runner
# ---------------------------------------------------------------------------


async def run_arena(
    question: str, providers: list[Provider]
) -> tuple[str, str, str, str]:
    """Run the full arena and return (final_question_md, answers_md, rankings_md, winner_md)."""
    question = question[:MAX_INPUT_LENGTH].strip()
    available = [p for p in providers if p.has_api_key()]
    skipped = [p for p in providers if not p.has_api_key()]

    async def _query_one(provider: Provider) -> tuple[Provider, str | None, float, str]:
        """Returns (provider, answer, elapsed_seconds, error_reason)."""
        start = time.monotonic()
        try:
            answer = await asyncio.wait_for(
                asyncio.to_thread(query_provider, provider, question),
                timeout=QUERY_TIMEOUT,
            )
            elapsed = time.monotonic() - start
            return provider, answer, elapsed, ""
        except asyncio.TimeoutError:
            elapsed = time.monotonic() - start
            return provider, None, elapsed, f"timed out after {QUERY_TIMEOUT:.0f}s"
        except Exception as exc:
            elapsed = time.monotonic() - start
            reason = str(exc) if str(exc) else type(exc).__name__
            return provider, None, elapsed, reason

    results = await asyncio.gather(*[_query_one(p) for p in available])

    competitors: list[str] = []
    answers: list[str] = []
    judges: list[Provider] = []

    answers_parts: list[str] = []
    for provider, answer, elapsed, reason in results:
        time_str = f"*({elapsed:.1f}s)*"
        if answer is None:
            answers_parts.append(
                f"<details><summary><b>{provider.name}</b> {time_str} — "
                f"<i>Error: {reason}</i></summary>\n\nNo response received.\n</details>\n"
            )
            continue
        competitors.append(provider.name)
        answers.append(answer)
        judges.append(provider)
        answers_parts.append(
            f"<details open><summary><b>{provider.name}</b> {time_str}</summary>\n\n"
            f"{answer}\n</details>\n"
        )

    for p in skipped:
        answers_parts.append(
            f"<details><summary><b>{p.name}</b> — <i>skipped (no API key)</i></summary>"
            f"\n\nAPI key not configured.\n</details>\n"
        )

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
    providers = DEFAULT_PROVIDERS

    with gr.Blocks(title="LLM Arena") as demo:
        gr.Markdown("# LLM Arena")
        gr.Markdown("Ask a question and have multiple LLMs compete to give the best answer.")

        # Provider status
        provider_status = gr.Markdown(
            value=_provider_status_md(providers), label="Providers"
        )

        # State
        current_question = gr.State("")
        is_clear = gr.State(False)
        clarify_round = gr.State(0)
        question_history = gr.State([])

        # Phase 1 — Clarification chat
        with gr.Group():
            gr.Markdown("## Step 1: Ask your question")

            history_dropdown = gr.Dropdown(
                choices=[],
                label="Question history",
                interactive=True,
                visible=False,
            )

            chatbot = gr.Chatbot(label="Clarification")
            msg = gr.Textbox(
                placeholder="Type your question here...",
                label="Your message",
                show_label=False,
            )
            with gr.Row():
                submit_btn = gr.Button("Send", variant="primary")
                arena_btn = gr.Button("Run Arena", variant="secondary", interactive=False)
                reset_btn = gr.Button("New Question", variant="stop")

        # Phase 2 — Results
        with gr.Group(visible=False) as results_group:
            gr.Markdown("## Results")
            status_md = gr.Markdown()
            final_q_md = gr.Markdown()
            answers_md = gr.Markdown()
            rankings_md = gr.Markdown()
            winner_md = gr.Markdown()

        # ------------------------------------------------------------------
        # Handlers
        # ------------------------------------------------------------------

        async def on_submit(user_message, chat_history, question, clear, rounds):
            """Handle clarification chat messages. Returns with submit_btn disabled during processing."""
            if not user_message.strip():
                return (
                    chat_history, "", question, clear, rounds,
                    gr.update(interactive=False),  # arena_btn
                    gr.update(interactive=True),    # submit_btn
                )

            chat_history = chat_history + [{"role": "user", "content": user_message}]

            if not question:
                question = user_message.strip()[:MAX_INPUT_LENGTH]
                reply = await asyncio.to_thread(check_clarity, question)
                rounds += 1

                if reply.upper() == "CLEAR":
                    chat_history.append(
                        {"role": "assistant", "content": "Your question is clear! Click **Run Arena** to proceed."}
                    )
                    return (
                        chat_history, "", question, True, rounds,
                        gr.update(interactive=True),
                        gr.update(interactive=True),
                    )
                else:
                    chat_history.append({"role": "assistant", "content": reply})
                    return (
                        chat_history, "", question, False, rounds,
                        gr.update(interactive=False),
                        gr.update(interactive=True),
                    )
            else:
                if rounds >= MAX_CLARIFICATION_ROUNDS:
                    chat_history.append(
                        {"role": "assistant", "content": (
                            f"Maximum clarification rounds reached. Proceeding with:\n\n"
                            f"**{question}**\n\nClick **Run Arena** to proceed."
                        )}
                    )
                    return (
                        chat_history, "", question, True, rounds,
                        gr.update(interactive=True),
                        gr.update(interactive=True),
                    )

                refined = await asyncio.to_thread(
                    refine_question, question,
                    user_message.strip()[:MAX_CLARIFY_ANSWER_LENGTH],
                )
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
                    return (
                        chat_history, "", question, True, rounds,
                        gr.update(interactive=True),
                        gr.update(interactive=True),
                    )
                else:
                    chat_history.append({"role": "assistant", "content": reply})
                    return (
                        chat_history, "", question, False, rounds,
                        gr.update(interactive=False),
                        gr.update(interactive=True),
                    )

        submit_outputs = [chatbot, msg, current_question, is_clear, clarify_round, arena_btn, submit_btn]
        submit_inputs = [msg, chatbot, current_question, is_clear, clarify_round]

        submit_btn.click(on_submit, submit_inputs, submit_outputs)
        msg.submit(on_submit, submit_inputs, submit_outputs)

        async def on_run_arena(question, clear, history):
            if not clear or not question:
                return (
                    gr.update(visible=False), "", "", "", "", "",
                    gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True),
                    history, gr.update(),
                )

            # Add to history
            if question not in history:
                history = history + [question]

            fq, ans, rank, win = await run_arena(question, providers)
            dropdown_update = gr.update(
                choices=history, visible=len(history) > 0
            )
            return (
                gr.update(visible=True),  # results_group
                "Arena complete.",        # status_md
                fq, ans, rank, win,
                gr.update(interactive=True),   # submit_btn
                gr.update(interactive=True),   # arena_btn
                gr.update(interactive=True),   # msg
                history,
                dropdown_update,
            )

        # Disable controls while arena runs
        def _disable_controls():
            return (
                gr.update(interactive=False),  # submit_btn
                gr.update(interactive=False),  # arena_btn
                gr.update(interactive=False),  # msg
                gr.update(visible=True),       # results_group
                "Running arena — querying all providers...",  # status_md
            )

        arena_btn.click(
            _disable_controls,
            [],
            [submit_btn, arena_btn, msg, results_group, status_md],
        ).then(
            on_run_arena,
            [current_question, is_clear, question_history],
            [results_group, status_md, final_q_md, answers_md, rankings_md, winner_md,
             submit_btn, arena_btn, msg, question_history, history_dropdown],
        )

        # Reset handler
        def on_reset():
            return (
                [],          # chatbot
                "",          # msg
                "",          # current_question
                False,       # is_clear
                0,           # clarify_round
                gr.update(interactive=False),  # arena_btn
                gr.update(interactive=True),   # submit_btn
                gr.update(interactive=True),   # msg (textbox)
                gr.update(visible=False),      # results_group
                "", "", "", "", "",            # status_md, final_q_md, answers_md, rankings_md, winner_md
            )

        reset_btn.click(
            on_reset,
            [],
            [chatbot, msg, current_question, is_clear, clarify_round,
             arena_btn, submit_btn, msg, results_group,
             status_md, final_q_md, answers_md, rankings_md, winner_md],
        )

        # History selection — load a past question
        def on_history_select(selected, history):
            if not selected:
                return [], "", "", False, 0
            return (
                [{"role": "user", "content": selected},
                 {"role": "assistant", "content": "Loaded from history. Click **Run Arena** to proceed."}],
                "",
                selected,
                True,
                0,
            )

        history_dropdown.change(
            on_history_select,
            [history_dropdown, question_history],
            [chatbot, msg, current_question, is_clear, clarify_round],
        ).then(
            lambda: gr.update(interactive=True),
            [],
            [arena_btn],
        )

    return demo


if __name__ == "__main__":
    load_dotenv()
    validate_api_keys(DEFAULT_PROVIDERS)
    app = build_ui()
    app.launch(server_name="127.0.0.1", share=False)
