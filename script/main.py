import requests
import os
import subprocess
from dotenv import load_dotenv
import time
from multiprocessing import Pool
import threading
#this seems to make it faster
os.environ['LLAMA_CPP_VULKAN'] = '1'
os.environ['GGML_VULKAN_DEVICE'] = '0'
from llama_cpp import Llama



#setup
load_dotenv()
db_host = os.getenv("DB_HOST")
MODEL1 = os.getenv("MODEL1")
MODEL2 = os.getenv("MODEL2") 
MODEL3 = os.getenv("MODEL3")
LLAMA_ADDR = os.getenv("LLAMA_ADDR")

models = [MODEL3, MODEL2, MODEL1]
start_time = time.perf_counter()
llm = Llama(
    model_path=MODEL1,
    n_gpu_layers=25,  
    verbose=False
)

llm2 = Llama(
    model_path=MODEL2,
    n_gpu_layers=25,  
    verbose=False
)

llm3 = Llama(
    model_path=MODEL3,
    n_gpu_layers=25,  
    verbose=False
)
end_time = time.perf_counter()
elapsed_time = end_time - start_time
print(elapsed_time)
llms = [llm, llm2, llm3]

question = "should i have eggs or oatmeal? CHOOSE ONE DEFINITIVELY IN FIRST SENTENCE"
ans = []
def ask_model(model, q, tokens):
    ans.append(model(q, max_tokens=tokens)['choices'][0]['text'])
    
for i in llms:
    ask_model(i, question, 100)
for i in range(3):
    print(models[i] + ": " + ans[i])
start_time = time.perf_counter()
for i in llms:
    ask_model(i, question, 100)
for i in range(3):
    print(models[i] + ": " + ans[i])

end_time = time.perf_counter()
elapsed_time = end_time - start_time
print(elapsed_time)
