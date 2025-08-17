from init import *
import threading

def ask_model(model, q, tokens):
    formatted_prompt = f"<|system|>{prompts[model]}\nRECOMMEND IN FIRST LINE ONLY IMMEDIATE ACTION, DO NOT BE VERBOSE\n<|end|>\n<|user|>\n{q}<|end|>\n<|assistant|>\n"
    responses[model].append(model(formatted_prompt, max_tokens=tokens)['choices'][0]['text'])

# initial distribution of question
def ask_models(llms, q, tokens):
    threads = []
    for llm in llms:
        t = threading.Thread(target=ask_model, args=(llm, q, tokens))
        threads.append(t)

    for t in threads:
        t.start()

    for t in threads:
        t.join()

def ask_model_deliberation(model, response1, response2, response3, tokens, q):
   responses_text = f"YOU WERE ASKED: {q}\n\n YOUR RESPONSE, RESPONSE A WAS: {response1}\nResponse B WAS: {response2}\nResponse C WAS: {response3}\n READING ALL OF THESE RESPONSES, WHAT DO YOU NOW RECOMMEND? YOUR FIRST LINE MUST BE FORMATTED LIKE RESPONSE A'S WITH A WORD COUNT OF PLUS OR MINUS ONE RESPONSE A'S."
   formatted_prompt = f"<|system|>\n{prompts[model]}<|end|>\n<|user|>\n{responses_text}<|end|>\n<|assistant|>\n"
   responses[model].append(model(formatted_prompt, max_tokens=tokens)['choices'][0]['text'])

def conditional_check(model, response1, response2, response3, tokens, q, x):
   responses_text = f"YOU WERE ASKED: {q}\n\n YOUR RESPONSE WAS RESPONSE {x}.RESPONSE 1 WAS: {response1}\nResponse 2 WAS: {response2}\nResponse 3 WAS: {response3}\n"
   formatted_prompt = f"<|system|>\n{conditional_prompts[x]}<|end|>\n<|user|>\n{responses_text}<|end|>\n<|assistant|>\n"
   return (model(formatted_prompt, max_tokens=tokens)['choices'][0]['text'])