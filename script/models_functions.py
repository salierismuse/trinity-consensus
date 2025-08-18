from init import *
import threading

def ask_model(model, q, tokens):
    formatted_prompt = f"<|system|>{prompts[model]}<|end|>\n<|user|>\n{q}<|end|>\n<|assistant|>\n"
    responses[model].append(model(formatted_prompt, max_tokens=tokens)['choices'][0]['text'])


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
   responses_text = f"Question: {q}\n\nResponse A: {response1}\n\nResponse B: {response2}\n\nResponse C: {response3}\n\nProvide your final recommendation."
   formatted_prompt = f"<|system|>\n{dprompts[model]}<|end|>\n<|user|>\n{responses_text}<|end|>\n<|assistant|>\n"
   responses[model].append(model(formatted_prompt, max_tokens=tokens)['choices'][0]['text'])

def conditional_check(model, response1, response2, response3, tokens, q, x):
   responses_text = f"Question: {q}\n\nResponse 1: {response1}\n\nResponse 2: {response2}\n\nResponse 3: {response3}\n\nYou were Response {x+1}."
   formatted_prompt = f"<|system|>\n{conditional_prompts[x]}<|end|>\n<|user|>\n{responses_text}<|end|>\n<|assistant|>\n"
   return (model(formatted_prompt, max_tokens=tokens)['choices'][0]['text'])

def final_decision(model1, model2, model3, response1, response2, response3, tokens, q):
    responses_text = f"Question: {q}\n\nResponse 1: {response1}\n\nResponse 2: {response2}\n\nResponse 3: {response3}\n"
    formatted_prompt = f"<|system|>\n{FINAL_DECISION_PROMPT}<|end|>\n<|user|>\n{responses_text}<|end|>\n<|assistant|>\n"
    return (DECISION_MODEL(formatted_prompt, max_tokens=tokens)['choices'][0]['text'])

def final_decision_two(model1, model2, response1, response2, tokens, q):
    responses_text = f"Question: {q}\n\nResponse 1: {response1}\n\nResponse 2: {response2}\n\n"
    formatted_prompt = f"<|system|>\n{FINAL_DECISION_PROMPT}<|end|>\n<|user|>\n{responses_text}<|end|>\n<|assistant|>\n"
    return (DECISION_MODEL(formatted_prompt, max_tokens=tokens)['choices'][0]['text'])


    
    
