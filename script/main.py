import requests
import os
import subprocess
from dotenv import load_dotenv
import time
from multiprocessing import Pool
import threading
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
#this seems to make it faster
os.environ['LLAMA_CPP_VULKAN'] = '1'
os.environ['GGML_VULKAN_DEVICE'] = '0'
from llama_cpp import Llama


TOKENS = 100

#setup
load_dotenv()
db_host = os.getenv("DB_HOST")
MODEL1 = os.getenv("MODEL1")
MODEL2 = os.getenv("MODEL2") 
MODEL3 = os.getenv("MODEL3")
LLAMA_ADDR = os.getenv("LLAMA_ADDR")

SYS_PROMPT1 = os.getenv("SYS_PROMPT1")
SYS_PROMPT2 = os.getenv("SYS_PROMPT2")
SYS_PROMPT3 = os.getenv("SYS_PROMPT3")

DSYS_PROMPT1 = os.getenv("DSYS_PROMPT1")
DSYS_PROMPT2 = os.getenv("DSYS_PROMPT2")
DSYS_PROMPT3 = os.getenv("DSYS_PROMPT3")

models = [MODEL1, MODEL2, MODEL3]
start_time = time.perf_counter()

llm1 = Llama(
    model_path=MODEL1,
    n_gpu_layers = 28,  
    verbose=False,
    n_ctx=4098,
)

llm2 = Llama(
    model_path=MODEL2,
    n_gpu_layers=28,  
    verbose=False,
    n_ctx=4098,
)

llm3 = Llama(
    model_path=MODEL3,
    n_gpu_layers=0,  
    verbose=False,
    n_ctx=4098,
)

prompts = {llm1: SYS_PROMPT1, llm2: SYS_PROMPT2, llm3: SYS_PROMPT3}
dprompts = {llm1: DSYS_PROMPT1, llm2: DSYS_PROMPT2, llm3: DSYS_PROMPT3}

responses = {}
responses[llm1] = []
responses[llm2] = []
responses[llm3] = []


end_time = time.perf_counter()
elapsed_time = end_time - start_time
#startup time to load all three models 
print(elapsed_time)
llms = [llm1, llm2, llm3]
question = input("")
ans = []

#basic function for asking question
def ask_model(model, q, tokens):
    formatted_prompt = f"<|system|>\n{prompts[model]}<|end|>\n<|user|>\n{q}<|end|>\n<|assistant|>\n"
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
   responses_text = f"YOU WERE ASKED: {q}\n\n YOUR RESPONSE, RESPONSE A WAS: {response1}\nResponse B WAS: {response2}\nResponse C WAS: {response3}\n"
   formatted_prompt = f"<|system|>\n{dprompts[model]}<|end|>\n<|user|>\n{responses_text}<|end|>\n<|assistant|>\n"
   responses[model].append(model(formatted_prompt, max_tokens=tokens)['choices'][0]['text'])
    
start_time = time.perf_counter()
ask_models(llms, question, TOKENS)
# ask_model_deliberation(llm1, responses[llms[0]][0], responses[llms[1]][0], responses[llms[2]][0], 150, question)
# ask_model_deliberation(llm2, responses[llms[1]][0], responses[llms[2]][0], responses[llms[0]][0], 150, question)
# ask_model_deliberation(llm3, responses[llms[2]][0], responses[llms[1]][0], responses[llms[0]][0], 150, question)



print("\n" + "="*25 + " RESULTS " + "="*25)

decisions = []
for i in range(3):
    response = responses[llms[i]][0]
    first_line = response.strip().split('\n')[0]
    decisions.append(first_line)
    print(models[i] + ": " + response)


sent = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

embeddings = sent.encode(decisions)
print(embeddings.shape)
similarities = sent.similarity(embeddings, embeddings)
print(similarities)



end_time = time.perf_counter()
elapsed_time = end_time - start_time
print(elapsed_time)
