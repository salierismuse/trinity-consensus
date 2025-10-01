# app.py
# trinity ui for tri-llm judge pipeline

import traceback
import gradio as gr

from init import *  # expects llms, TOKENS, responses, etc.
from models_functions import (
    ask_models,
    ask_model_deliberation,
    final_decision,
    final_decision_two,
    classify_response,
    _clip_four_lines,
    conditional_check,
)
from scripts import reset_to_base


def run_pipeline(question: str):
    try:
        if not question or not question.strip():
            return "", "", "", "**error:** empty question", ""

        # fresh state
        reset_to_base()

        # ---- round 1 ----
        ask_models(llms, question, TOKENS)

        outs1 = [responses[llms[i]][0] if responses[llms[i]] else "" for i in range(3)]
        toks1 = [classify_response(o) for o in outs1]

        status_lines = [f"first pass tokens: {toks1}"]

        # total agreement on first pass?
        if toks1[0] and toks1[0] == toks1[1] == toks1[2]:
            decision = final_decision(llms[0], llms[1], llms[2], outs1[0], outs1[1], outs1[2], 150, question)
            return outs1[0], outs1[1], outs1[2], "", "status: total_same (first pass)", decision

        # ---- deliberation (intermediary) ----
        ask_model_deliberation(llms[0], outs1[0], outs1[1], outs1[2], 100, question, toks1[0], toks1[1], toks1[2])
        ask_model_deliberation(llms[1], outs1[0], outs1[1], outs1[2], 100, question, toks1[0], toks1[1], toks1[2])
        ask_model_deliberation(llms[2], outs1[0], outs1[1], outs1[2], 100, question, toks1[0], toks1[1], toks1[2])

        outs2 = [responses[llms[i]][-1] for i in range(3)]
        toks2 = [classify_response(o) for o in outs2]
        status_lines.append(f"second pass tokens: {toks2}")

        # total agreement after deliberation?
        if toks2[0] and toks2[0] == toks2[1] == toks2[2]:
            decision = final_decision(llms[0], llms[1], llms[2], outs2[0], outs2[1], outs2[2], 150, question)
            status_text = "\n".join(status_lines + ["status: total_same"])
            return outs2[0], outs2[1], outs2[2], "", status_text, decision

        # ----- partial vs disagreement (deterministic on tokens) -----
        outlier_idx = None
        if toks2[0] == toks2[1] != toks2[2]:
            outlier_idx = 3
        elif toks2[0] == toks2[2] != toks2[1]:
            outlier_idx = 2
        elif toks2[1] == toks2[2] != toks2[0]:
            outlier_idx = 1

        condition_text = ""
        if outlier_idx is not None:
            # partial_same: ask the outlier for a condition
            cond_model = outlier_idx - 1  # 0/1/2
            condition_text = conditional_check(
                llms[cond_model],
                outs2[0], outs2[1], outs2[2],
                100, question, cond_model
            )

            # conservative rule: if a condition is explicitly requested, defer
            if "CONDITION:" in condition_text.upper():
                status_text = "\n".join(status_lines + [f"status: partial_same (outlier: model {outlier_idx}) — condition returned"])
                decision = '{"choice":"defer","reasons":["needs condition satisfied"],"risk_level":2,"citations":[]}'
                # show second-pass outputs; if any is empty, fall back to first-pass
                a = outs2[0] or outs1[0]
                b = outs2[1] or outs1[1]
                c = outs2[2] or outs1[2]
                return a, b, c, condition_text, status_text, decision

            # otherwise proceed with agreeing two (non-outliers)
            keep = [outs2[i] for i in range(3) if i != cond_model]
            decision = final_decision_two(llms[0], llms[1], keep[0], keep[1], 150, question)
            status_text = "\n".join(status_lines + [f"status: partial_same (outlier: model {outlier_idx})"])
            a = outs2[0] or outs1[0]
            b = outs2[1] or outs1[1]
            c = outs2[2] or outs1[2]
            return a, b, c, condition_text, status_text, decision

        # if we got here: disagreement
        status_text = "\n".join(status_lines + ["status: disagreement"])
        decision = '{"choice":"defer","reasons":["models disagree"],"risk_level":2,"citations":[]}'
        a = outs2[0] or outs1[0]
        b = outs2[1] or outs1[1]
        c = outs2[2] or outs1[2]
        return a, b, c, "", status_text, decision

    except Exception as e:
        tb = traceback.format_exc()
        return "", "", "", f"**error:** {e}\n```\n{tb}\n```", ""


with gr.Blocks(title="TRINITY") as demo:
    gr.Markdown("# trinity")
    q = gr.Textbox(label="question", placeholder="ask anything…")
    btn = gr.Button("run")
    with gr.Row():
        a = gr.Textbox(label="model 1 (clipped)", lines=8)
        b = gr.Textbox(label="model 2 (clipped)", lines=8)
        c = gr.Textbox(label="model 3 (clipped)", lines=8)
    condition_box = gr.Textbox(label="condition (from outlier / judge)", lines=4)
    status = gr.Markdown()
    decision = gr.Textbox(label="final decision", lines=8)

    btn.click(run_pipeline, inputs=[q], outputs=[a, b, c, condition_box, status, decision])

if __name__ == "__main__":
    demo.launch(
        share=False,
        inbrowser=True,
        server_name="127.0.0.1",
        server_port=7860,
        show_error=True,
        debug=True,
        show_api=False,  # hides the "use via api" box
    )