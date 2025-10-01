from init import *
import threading
import json
import re

# -------------------- utils --------------------

def _clip_four_lines(text: str) -> str:
    """return the first 4 non-empty lines from text (answer + 3 reasons)."""
    if not text:
        return ""
    # normalize newlines, strip right-side spaces, drop empties
    lines = [ln.rstrip() for ln in text.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    lines = [ln for ln in lines if ln.strip() != ""]
    return "\n".join(lines[:4])

def top_line(text: str) -> str:
    """first non-empty line, normalized (lowercase, squashed spaces, quotes trimmed)."""
    if not text:
        return ""
    for ln in text.splitlines():
        s = ln.strip().lower()
        if s:
            s = s.strip('`"\' ')
            s = re.sub(r"\s+", " ", s)
            return s
    return ""

def _canonical_choice(s: str) -> str:
    """
    lightweight canonicalizer so logically equivalent answers normalize.
    extend with your domain-specific classes as needed.
    """
    s = s.lower().strip()
    s = re.sub(r"[.!?]$", "", s)

    # generic yes/no families
    if re.search(r"\b(yes|approve|allow|go ahead|do it)\b", s):
        return "yes"
    if re.search(r"\b(no|deny|disallow|avoid|refuse|do not|don't)\b", s):
        return "no"

    # sanitation example keywords (kept from your earlier work)
    if "toilet" in s or "loo" in s or "wc" in s:
        return "toilet"
    if "sink" in s:
        return "sink"

    # cautious / abstain
    if "defer" in s or "unsure" in s or "cannot decide" in s:
        return "defer"

    return s  # fallback: leave as-is

def classify_response(text: str) -> str:
    """
    map an entire response to one of: 'approve' | 'reject' | 'defer'.
    scans full text so long paragraphs don't dodge the top decision.
    """
    if not text:
        return "defer"
    t = text.lower()

    # strong explicit “recommend …”
    if re.search(r"\b(i )?(recommend|advise)\s+(yes|approval|approve|greenlight|proceed)\b", t):
        return "approve"
    if re.search(r"\b(i )?(recommend|advise)\s+(no|rejection|reject|do not approve|deny)\b", t):
        return "reject"

    # other explicit verbs
    if re.search(r"\b(approve|greenlight|go ahead|proceed)\b", t):
        return "approve"
    if re.search(r"\b(reject|do not approve|deny|turn down)\b", t):
        return "reject"

    # defer/hedge signals (only if no explicit approve/reject found)
    if re.search(r"\b(defer|postpone|cannot decide|needs further study|conduct (an|a) (eia|study)|more data needed)\b", t):
        return "defer"

    # bare “yes/no” as top line
    first = top_line(text)
    if re.fullmatch(r"(i recommend yes\.?|yes\.?|approve\.?|approval\.?|greenlight\.?)", first):
        return "approve"
    if re.fullmatch(r"(i recommend no\.?|no\.?|reject\.?|rejection\.?|deny\.?|do not approve\.?)", first):
        return "reject"

    return "defer"

# -------------------- llm calls --------------------

def ask_model(model, q, tokens):
    formatted_prompt = f"<|system|>{prompts[model]}<|end|>\n<|user|>\n{q}<|end|>\n<|assistant|>\n"
    out = model(formatted_prompt, max_tokens=tokens)['choices'][0]['text']
    responses[model].append(_clip_four_lines(out))

def ask_models(llms, q, tokens):
    threads = []
    for llm in llms:
        t = threading.Thread(target=ask_model, args=(llm, q, tokens))
        threads.append(t)
    for t in threads:
        t.start()
    for t in threads:
        t.join()

def ask_model_deliberation(model, response1, response2, response3, tokens, q, decision1, decision2, decision3):
    responses_text = (
        f"question: {q}\n\n"
        f"response a: {response1}\n\n"
        f"response b: {response2}\n\n"
        f"response c: {response3}\n\n"
        f"provide your final recommendation."
    )
    formatted_prompt = f"<|system|>\n{dprompts[model]}<|end|>\n<|user|>\n{responses_text}<|end|>\n<|assistant|>\n"
    out = model(formatted_prompt, max_tokens=tokens)['choices'][0]['text']
    responses[model].append(_clip_four_lines(out))

def conditional_check(model, response1, response2, response3, tokens, q, x):
    responses_text = (
        f"question: {q}\n\n"
        f"response 1: {response1}\n\n"
        f"response 2: {response2}\n\n"
        f"response 3: {response3}\n\n"
        f"you were response {x+1}."
    )
    formatted_prompt = f"<|system|>\n{conditional_prompts[x]}<|end|>\n<|user|>\n{responses_text}<|end|>\n<|assistant|>\n"
    out = model(formatted_prompt, max_tokens=tokens)['choices'][0]['text']
    return _clip_four_lines(out)

def final_decision(model1, model2, model3, response1, response2, response3, tokens, q):
    responses_text = (
        f"question: {q}\n\n"
        f"response 1: {response1}\n\n"
        f"response 2: {response2}\n\n"
        f"response 3: {response3}\n"
    )
    formatted_prompt = f"<|system|>\n{FINAL_DECISION_PROMPT}<|end|>\n<|user|>\n{responses_text}<|end|>\n<|assistant|>\n"
    out = DECISION_MODEL(formatted_prompt, max_tokens=tokens)['choices'][0]['text']
    return _clip_four_lines(out)

def final_decision_two(model1, model2, response1, response2, tokens, q):
    responses_text = (
        f"question: {q}\n\n"
        f"response 1: {response1}\n\n"
        f"response 2: {response2}\n\n"
    )
    formatted_prompt = f"<|system|>\n{FINAL_DECISION_PROMPT}<|end|>\n<|user|>\n{responses_text}<|end|>\n<|assistant|>\n"
    out = DECISION_MODEL(formatted_prompt, max_tokens=tokens)['choices'][0]['text']
    return _clip_four_lines(out)

# -------------------- deterministic judge on tokens --------------------

def judge_logical_equivalence_by_model3(llm3, question: str, top_a: str, top_b: str, top_c: str, tokens: int = 128):
    """
    with tokenized tops ('approve'|'reject'|'defer'), we can judge deterministically.
    returns (status, outlier_idx) with status ∈ {'total_same','partial_same','different'}
    and outlier_idx ∈ {None, 1, 2, 3}
    """
    # all same
    if top_a and top_a == top_b == top_c:
        return "total_same", None
    # two vs one
    if top_a and top_b and top_a == top_b != top_c:
        return "partial_same", 3
    if top_a and top_c and top_a == top_c != top_b:
        return "partial_same", 2
    if top_b and top_c and top_b == top_c != top_a:
        return "partial_same", 1
    # otherwise
    return "different", None