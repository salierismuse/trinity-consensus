import requests
import os
import subprocess
from dotenv import load_dotenv
import time
from multiprocessing import Pool
import threading
from sentence_transformers import SentenceTransformer

#this seems to make it faster
os.environ['LLAMA_CPP_VULKAN'] = '1'
os.environ['GGML_VULKAN_DEVICE'] = '0'
from llama_cpp import Llama


TOKENS = 150

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
CONDITIONAL_AGREEMENT_PROMPT1 = os.getenv("CONDITIONAL_AGREEMENT_PROMPT1")
CONDITIONAL_AGREEMENT_PROMPT2 = os.getenv("CONDITIONAL_AGREEMENT_PROMPT2")
CONDITIONAL_AGREEMENT_PROMPT3 = os.getenv("CONDITIONAL_AGREEMENT_PROMPT3")

models = [MODEL1, MODEL2, MODEL3]
start_time = time.perf_counter()

llm1 = Llama(
    model_path=MODEL1,
    n_gpu_layers = 28,  
    verbose=False,
    n_ctx=2048,
)

llm2 = Llama(
    model_path=MODEL2,
    n_gpu_layers=28,  
    verbose=False,
    n_ctx=2048,
)

llm3 = Llama(
    model_path=MODEL3,
    n_gpu_layers=0,  
    verbose=False,
    n_ctx=2048,
)

prompts = {llm1: SYS_PROMPT1, llm2: SYS_PROMPT2, llm3: SYS_PROMPT3}
dprompts = {llm1: DSYS_PROMPT1, llm2: DSYS_PROMPT2, llm3: DSYS_PROMPT3}
conditional_prompts = [CONDITIONAL_AGREEMENT_PROMPT1, CONDITIONAL_AGREEMENT_PROMPT2, CONDITIONAL_AGREEMENT_PROMPT3]
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
   responses_text = f"YOU WERE ASKED: {q}\n\n YOUR RESPONSE, RESPONSE A WAS: {response1}\nResponse B WAS: {response2}\nResponse C WAS: {response3}\n READING ALL OF THESE RESPONSES, WHAT DO YOU NOW RECOMMEND? YOUR FIRST LINE MUST LOOK LIKE RESPONSE A'S FIRST LINE IN TERMS OF FORMAT"
   formatted_prompt = f"<|system|>\n{prompts[model]}<|end|>\n<|user|>\n{responses_text}<|end|>\n<|assistant|>\n"
   responses[model].append(model(formatted_prompt, max_tokens=tokens)['choices'][0]['text'])
    
start_time = time.perf_counter()
ask_models(llms, question, TOKENS)


# if 2/3 models agree, this is called on the outlier
# it seeks to find a compromise


def conditional_check(model, response1, response2, response3, tokens, q, x):
   responses_text = f"YOU WERE ASKED: {q}\n\n YOUR RESPONSE WAS RESPONSE {x}.RESPONSE 1 WAS: {response1}\nResponse 2 WAS: {response2}\nResponse 3 WAS: {response3}\nIS THERE ANY CONDITION THAT WOULD ALLOW YOU TO AGREE WITH RESPONSE 2 AND 3"
   formatted_prompt = f"<|system|>\n{conditional_prompts[x]}<|end|>\n<|user|>\n{responses_text}<|end|>\n<|assistant|>\n"
   return (model(formatted_prompt, max_tokens=tokens)['choices'][0]['text'])

decisions = []

for i in range(3):
    response = responses[llms[i]][0]
    first_line = response.split('\n')[0].strip().lower()
    decisions.append(first_line)
    print(response)
    print("------")
print("---------")


sent = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

embeddings = sent.encode(decisions)

for i in decisions:
    print(i)
print(embeddings.shape)



similarities = sent.similarity(embeddings, embeddings)
print(similarities)

count = 0
count2 = 0
total = 0
for i in similarities:
    total += 1
    count2 = 0
    for ii in i:
        if ii < .9:
            count2+=1
        if count2 == 2:
            count += 1
            cond_model = total-1
            break


decisions = []
# zero outliers
if count == 0:
    print("TOTAL AGREEMENT")

# # one outlier
if count == 1:
    print("PARTIAL DISAGREEMENT")
    conditional_result = conditional_check(llms[cond_model], responses[llms[0]][-1], responses[llms[1]][-1], responses[llms[2]][-1], 150, question, cond_model)
    #proceed to deliberation
    if "IMPOSSIBLE" in conditional_result:
        ask_model_deliberation(llm1, responses[llms[0]][0], responses[llms[1]][0], responses[llms[2]][0], 150, question)
        ask_model_deliberation(llm2, responses[llms[1]][0], responses[llms[2]][0], responses[llms[0]][0], 150, question)
        ask_model_deliberation(llm3, responses[llms[2]][0], responses[llms[1]][0], responses[llms[0]][0], 150, question)
        for i in range(3):
            response = responses[llms[i]][-1]
            first_line = response.split('\n')[0].strip().lower()
            decisions.append(first_line)
    else:
        print(conditional_result)
# no agreement anywhere
if count > 1:
    print("DISAGREEMENT")
    print("-------------------")
    ask_model_deliberation(llm1, responses[llms[0]][0], responses[llms[1]][0], responses[llms[2]][0], 150, question)
    ask_model_deliberation(llm2, responses[llms[1]][0], responses[llms[2]][0], responses[llms[0]][0], 150, question)
    ask_model_deliberation(llm3, responses[llms[2]][0], responses[llms[1]][0], responses[llms[0]][0], 150, question)
    print("-------------")
    for i in range(3):
        response = responses[llms[i]][-1]
        first_line = response.split('\n')[0].strip().lower()
        decisions.append(first_line)
        print(response)
        print("------")
print("\n")

count = 0
embeddings = sent.encode(decisions)

for i in decisions:
    print(i)
print(embeddings.shape)



similarities = sent.similarity(embeddings, embeddings)
print(similarities)

count = 0
count2 = 0
total = 0
for i in similarities:
    total += 1
    count2 = 0
    for ii in i:
        if ii < .86:
            count2+=1
        if count2 == 2:
            count += 1
            cond_model = total-1
            break
if count == 0:
    print("TOTAL AGREEMENT")
if count == 1:
    print("PARTIAL DISAGREEMENT")
    conditional_result = conditional_check(llms[cond_model], responses[llms[0]][-1], responses[llms[1]][-1], responses[llms[2]][-1], 150, question, cond_model)
    print(conditional_result)
if count > 1:
    print("DISAGREEMENT")